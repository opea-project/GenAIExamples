from jinja2 import Environment, BaseLoader

PROMPT = open("utils/prompt_template.jinja2").read().strip()

def get_formatted_prompt(scene, prompt, history):
    newline = "\n"
    # formated = f"{newline}User: {history[0]}{newline}Assistant: {history[1]}{newline}"
    try:
        formated = "\n[INST]\n".join(history)
    except:
        formated = "\n[INST]\n".join(["hello", "hi"])
    env = Environment(loader=BaseLoader())
    template = env.from_string(PROMPT)
    return template.render(scene=scene, prompt=prompt, history=formated)
