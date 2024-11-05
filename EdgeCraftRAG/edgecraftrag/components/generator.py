from edgecraftrag.base import (
    BaseComponent,
    CompType,
    GeneratorType
)
import os
from langchain_core.prompts import PromptTemplate
import dataclasses

from pydantic import model_serializer


class QnAGenerator(BaseComponent):

    def __init__(self, llm_model, prompt_template, **kwargs):
        BaseComponent.__init__(
            self,
            comp_type=CompType.GENERATOR,
            comp_subtype=GeneratorType.LOCAL,
        )
        self._REPLACE_PAIRS = (
            ("\n\n", "\n"),
            ("\t\n", "\n"),
        )
        template = prompt_template
        self.prompt = (
            DocumentedContextRagPromptTemplate.from_file(template)
            if os.path.isfile(template)
            else DocumentedContextRagPromptTemplate.from_template(template)
        )
        self.llm = llm_model

    def clean_string(self, string):
        ret = string
        for p in self._REPLACE_PAIRS:
            ret = ret.replace(*p)
        return ret

    def run(self, chat_request, retrieved_nodes, **kwargs):
        if self.llm() is None:
            # This could happen when User delete all LLMs through RESTful API
            return "No LLM availiable, please load LLM"
        # query transformation
        text_gen_context = ""
        for n in retrieved_nodes:
            origin_text = n.node.get_text()
            text_gen_context += self.clean_string(origin_text.strip())

        query = chat_request.messages
        prompt_str = self.prompt.format(
            input=query, 
            context=text_gen_context
        )
        generate_kwargs = dict(
            temperature=chat_request.temperature,
            do_sample=chat_request.temperature > 0.0,
            top_p=chat_request.top_p,
            top_k=chat_request.top_k,
            typical_p=chat_request.typical_p,
            repetition_penalty=chat_request.repetition_penalty
        )
        self.llm().generate_kwargs = generate_kwargs

        return self.llm().complete(prompt_str)

    @model_serializer
    def ser_model(self):
        ser = {
            'idx': self.idx,
            'generator_type': self.comp_subtype,
            'model': self.llm()
        }
        return ser


@dataclasses.dataclass
class INSTRUCTIONS:
    IM_START = "You are an AI assistant that helps users answer questions given a specific context."
    SUCCINCT = "Ensure your response is succinct"
    ACCURATE = "Ensure your response is accurate."
    SUCCINCT_AND_ACCURATE = "Ensure your response is succinct. Try to be accurate if possible."
    ACCURATE_AND_SUCCINCT = "Ensure your response is accurate. Try to be succinct if possible."
    NO_RAMBLING = "Avoid posing new questions or self-questioning and answering, and refrain from repeating words in your response."
    SAY_SOMETHING = "Avoid meaningless answer such a random symbol or blanks."
    ENCOURAGE = "If you cannot well understand the question, try to translate it into English, and translate the answer back to the language of the question."
    NO_IDEA = 'If the answer is not discernible, please respond with "Sorry. I have no idea" in the language of the question.'
    CLOZE_TEST = """The task is a fill-in-the-blank/cloze test."""
    NO_MEANINGLESS_SYMBOLS = "Meaningless symbols and ``` should not be included in your response."
    ADAPT_NATIVE_LANGUAGE = "Please try to think like a person that speak the same language that the question used."


def _is_cloze(question):
    return ("()" in question or "（）" in question) and ("填" in question or "fill" in question or "cloze" in question)


# depreciated
def get_instructions(question):
    # naive pre-retrieval rewrite
    # cloze
    if _is_cloze(question):
        instructions = [INSTRUCTIONS.CLOZE_TEST, ]
    else:
        instructions = [INSTRUCTIONS.ACCURATE_AND_SUCCINCT, INSTRUCTIONS.NO_RAMBLING, INSTRUCTIONS.NO_MEANINGLESS_SYMBOLS]
    return ["System: {}".format(_) for _ in instructions]


def preprocess_question(question):
    if _is_cloze(question):
        question = question.replace(' ', '').replace('（', '(').replace('）', ')')
        # .replace("()", " <|blank|> ")
        ret = "User: Please finish the following fill-in-the-blank question marked by $$$ at the beginning and end. Make sure all the () are filled.\n$$$\n{}\n$$$\nAssistant: ".format(question)
    else:
        ret = "User: {}\nAssistant: 从上下文提供的信息中可以知道，".format(question)
    return ret


class DocumentedContextRagPromptTemplate(PromptTemplate):

    def format(self, **kwargs) -> str:
        # context = '\n'.join([clean_string(f"{_.page_content}".strip()) for i, _ in enumerate(kwargs["context"])])
        context = kwargs["context"]
        question = kwargs["input"]
        preprocessed_question = preprocess_question(question)
        if "instructions" in self.template:
            instructions = get_instructions(question)
            prompt_str = self.template.format(
                context=context,
                instructions='\n'.join(instructions),
                input=preprocessed_question
            )
        else:
            prompt_str = self.template.format(
                context=context,
                input=preprocessed_question
            )
        return prompt_str
