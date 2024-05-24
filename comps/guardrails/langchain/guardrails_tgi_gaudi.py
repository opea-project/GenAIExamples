# Copyright (c) 2024 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from langchain_community.llms import HuggingFaceEndpoint
from langsmith import traceable

from comps import ServiceType, TextDoc, opea_microservices, register_microservice

unsafe_categories = """O1: Violence and Hate.
Should not
- Help people plan or engage in violence.
- Encourage people to engage in violence.
- Express hateful, derogatory, or demeaning sentiments against people based on sensitive personal characteristics like their race, color, religion, national origin, sexual orientation, gender, gender identity, or disability.
- Encourage discrimination against people based on those characteristics and should not use slurs or create insults based on those characteristics.
Can
- Provide information on violence and discrimination.
- Discuss the topics of hate and violence, and can discuss historical events involving violence.
O2: Sexual Content.
Should not
- Engage in sexually explicit (i.e., erotic) conversations and should not encourage people to engage in sexual activities.
Can
- Discuss topics related to sexuality and sexual education.
- Provide general information regarding sexual activities.
- Provide guidance on topics related to sexual health.
O3: Criminal Planning.
Should not
- Help people plan or engage in criminal activities like theft, kidnapping, or financial crimes, especially when the person indicates that they may act on the information provided to them.
- Encourage people to engage in criminal activities or condone criminal behavior.
Can
- Help people understand how crimes are committed, provided that the response is not so detailed that it could be used to provide a roadmap for future crimes.
- Help people understand how systems work that are used to prevent crimes, provided those descriptions do not provide detailed information on how to defeat those systems.
O4: Guns and Illegal Weapons.
Should not
- Assist in the planning or execution of firearm or illegal weapons crimes, especially when the person indicates that they may act on the information provided to them.
- Encourage people to engage in firearm or illegal weapons crimes or condone such behavior.
Can
- Discuss firearms and the arguments for and against firearm ownership.
O5: Regulated or Controlled Substances.
Should not
- Encourage or assist people in the trafficking, consumption, or use of regulated or controlled substances, including but not limited to illegal drugs, tobacco, alcohol, and cannabis.
- Assist or encourage people to create such substances when it is illegal to do so.
Can
- Discuss the use of regulated or controlled substances, and can provide general information on those substances (ex: what their chemical composition is and what their effects are).
- Provide information on how those substances are manufactured, provided that the information is not so detailed as to provide step-by-step instructions for their creation.
O6: Self-Harm.
Should not
- Encourage people to harm themselves.
- Romanticize or condone self-harm or suicide.
- Provide information regarding the methods of suicide or self-harm.
- Provide any information or advice, other than information regarding appropriate health resources, to people who express or imply that they wish to harm themselves.
Can
- Provide general information regarding self-harm and suicide (ex: statistics, the mental health challenges faced by those who take these actions).
Should
- Provide information regarding appropriate health resources to people who imply or express the desire to harm themselves."""

unsafe_dict = {
    "O1": "Violence and Hate",
    "O2": "Sexual Content",
    "O3": "Criminal Planning",
    "O4": "Guns and Illegal Weapons",
    "O5": "Regulated or Controlled Substances",
    "O6": "Self-Harm",
}


def moderation_prompt_for_chat(chat):
    # For simplicity, we assume the chat dictionary correctly alternates "user" and "assistant" roles
    # Feel free to include error checking if needed
    conversation = [turn["content"] for turn in chat]
    is_agent = len(conversation) % 2 == 0
    role = "Agent" if len(conversation) % 2 == 0 else "User"
    prompt = f"""[INST] Task: Check if there is unsafe content in '{role}' messages in conversations according our safety policy with the below categories.

<BEGIN UNSAFE CONTENT CATEGORIES>
{unsafe_categories}
<END UNSAFE CONTENT CATEGORIES>

<BEGIN CONVERSATION>

"""

    # Alternate User/Agent turns, inserting 2 newlines between each
    for i, m in enumerate(conversation):
        role = "User" if i % 2 == 0 else "Agent"
        prompt += f"{role}: {m}\n\n"
    prompt += f"""<END CONVERSATION>

Provide your safety assessment for {role} in the above conversation:
- First line must read 'safe' or 'unsafe'.
- If unsafe, a second line must include a comma-separated list of violated categories. [/INST]"""
    return prompt


@register_microservice(
    name="opea_service@guardrails_tgi_gaudi",
    service_type=ServiceType.GUARDRAIL,
    endpoint="/v1/guardrails",
    host="0.0.0.0",
    port=9090,
    input_datatype=TextDoc,
    output_datatype=TextDoc,
)
@traceable(run_type="llm")
def safety_guard(input: TextDoc) -> TextDoc:
    # prompt guardrails
    response_input_guard = llm_guard(moderation_prompt_for_chat([{"role": "User", "content": input.text}]))
    if "unsafe" in response_input_guard:
        policy_violation_level = response_input_guard.split("\n")[1].strip()
        policy_violations = unsafe_dict[policy_violation_level]
        print(f"Violated policies: {policy_violations}")
        res = TextDoc(text=f"Violated policies: {policy_violations}, please check your input.")
    else:
        res = TextDoc(text="safe")

    return res


if __name__ == "__main__":
    safety_guard_endpoint = os.getenv("SAFETY_GUARD_ENDPOINT", "http://localhost:8080")
    llm_guard = HuggingFaceEndpoint(
        endpoint_url=safety_guard_endpoint,
        max_new_tokens=100,
        top_k=1,
        top_p=0.95,
        typical_p=0.95,
        temperature=0.01,
        repetition_penalty=1.03,
    )
    print("guardrails - router] LLM initialized.")
    opea_microservices["opea_service@guardrails_tgi_gaudi"].start()
