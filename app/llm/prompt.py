from langchain_core.prompts import PromptTemplate

issue_analysis_prompt_v1 = PromptTemplate.from_template(
    """You are an expert newsletter analyst.
    Your task is the extract a structured analysis from the newsletter issue content.
    Follow these strict rules:
    1. DO NOT include any explanations outside of the JSON.
    2. Match EXACTLY the schema provided to you.

    Following is the newsletter issue content:
    {newsletter_issue}
    """
)

issue_analysis_prompt_v2 = PromptTemplate.from_template(
    """You are an expert newsletter analyst.
    Given the content of a newsletter issue, provide a detailed analysis. Below is the content of the newsletter issue:

    Title: {title}
    Subtitle: {subtitle}

    {content}
    """
)

