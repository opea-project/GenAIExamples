from jinja2 import Environment, BaseLoader, select_autoescape

def get_formatted_prompt(scene, prompt, history):
    env = Environment(
        loader=BaseLoader(),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.from_string(PROMPT)
    