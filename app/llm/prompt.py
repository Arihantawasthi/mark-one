from langchain_core.prompts import PromptTemplate

issue_analysis_prompt_v1 = PromptTemplate.from_template(
    """You are an expert newsletter analyst.
    Your task is the extract a structured analysis from the newsletter issue content.
    An “ad” is defined as any block that is promoting a brand, product, sponsor, partnership, or contains promotional language, EVEN IF it is subtle.
    If the text contains:
    - a brand
    - a product line
    - a promotional hyperlink
    - action language like “get”, “try”, “learn”, “buy”, “subscribe”, “install”, “sign up”
    - mentions a sponsor
    - is tonally promotional
    Classify it as an ad.

    When unsure, classify as AD.
    Never leave borderline promotional content unlabeled if there is a link and a text
    Be conservative: it is better to over-detect ads than under-detect.


    Follow these strict rules:
    1. DO NOT include any explanations outside of the JSON.
    2. Match EXACTLY the schema provided to you.
    3. Ctas are any links that are mentioned in the newsletter except ads.
        (e.g: "type": "social", "text": "Grant Wahl Twitter Dms", "url": "https://twitter.com/grantwahl/direct_messages")
    4. Anything with "subscribe", "install", "get the app" are ads.
        (e.g: "type": "subscription", "text": "Subscribe to our premium plan", "url": "https://newsletter.com/subscribe")

    Following is the newsletter issue:
    Issue URL: {url}
    Title: {title}
    Subtitle: {subtitle}

    Content:
    {content}
    """
)

issue_analysis_prompt_v2 = PromptTemplate.from_template(
    """You are an expert newsletter analyst.
    Given the content of a newsletter issue, provide a detailed analysis. Below is the content of the newsletter issue:

    Title: {title}
    Subtitle: {subtitle}

    Content:
    {content}
    """
)

