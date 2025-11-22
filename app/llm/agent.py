from pydantic import BaseModel, Field
from app.llm.prompt import issue_analysis_prompt_v1, issue_analysis_prompt_v2
from langchain_openai import ChatOpenAI
from app.core import settings

class CTAObject(BaseModel):
    type: str = Field(description="Type of CTA")
    text: str = Field(description="Text of the CTA")
    url: str = Field(description="URL of the CTA")

    class Config:
        extra = "forbid"

class AdObject(BaseModel):
    type: str = Field(description="Type of Advertisement")
    text: str = Field(description="Text of the Advertisement")
    url: str = Field(description="URL of the Advertisement")

    class Config:
        extra = "forbid"

class AnalysisResponse(BaseModel):
    title: str = Field(description="Title of the newsletter issue")
    subtitle: str = Field(description="Subtitle of the newsletter issue")
    author: str = Field(description="Author of the newsletter issue")
    word_count: int = Field(description="Number of words in the newsletter issue")
    image_count: int = Field(description="Number of images in the newsletter issue")
    section_count: int = Field(description="Number of sections in the newsletter issue")
    emoji_count: int = Field(description="Number of emojis in the newsletter issue")
    title_emoji_count: int = Field(description="Number of emojis in the title of the newsletter issue")
    subtitle_emoji_count: int = Field(description="Number of emojis in the subtitle of the newsletter issue")
    title_word_count: int = Field(description="Number of words in the title of the newsletter issue")
    subtitle_word_count: int = Field(description="Number of words in the subtitle of the newsletter issue")
    addressed_user_by_name: bool = Field(description="Whether the newsletter issue addresses the user by their name")
    reading_time_minutes: int = Field(description="Estimated reading time in minutes for the newsletter issue")
    product_mention_count: int = Field(description="Number of product mentions in the newsletter issue")
    ctas: list[CTAObject] = Field(description="List of call-to-actions (CTAs) present in the newsletter issue, consider only links")
    ads: list[AdObject] = Field(description="List of advertisements present in the newsletter issue, consider only links like text")
    overall_summary: str = Field(description="Overall summary of the newsletter issue")
    overall_intent: str = Field(description="Overall intent of the newsletter issue, e.g., to inform, to sell, to entertain, etc.")
    overall_tone: str = Field(description="Overall tone of the newsletter issue, e.g., formal, informal, friendly, professional, etc.")

def analyze_newsletter_issue(issue: dict):
    model = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0, use_responses_api=True)
    prompt = issue_analysis_prompt_v1.format(
        title=issue["title"],
        subtitle=issue["subtitle"],
        content=issue["content"]
    )
    model_response = model.invoke(prompt, response_format=AnalysisResponse)
    return model_response
