from langchain.prompts import PromptTemplate

prompt_template = """
    ### System: Please translate the following {language_from} codes into {language_to} codes.

    ### Original codes:
    {source_code}

    ### Translated codes:
"""
codetrans_prompt_template = PromptTemplate.from_template(prompt_template)
