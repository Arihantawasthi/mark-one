from typing import Dict
from pydantic import BaseModel, Field
from prompt import issue_analysis_prompt_v1, issue_analysis_prompt_v2
from langchain_openai import ChatOpenAI
from app.core import settings

class AnalysisResponse(BaseModel):
    title: str = Field(description="Title of the newsletter issue")
    subtitle: str = Field(description="Subtitle of the newsletter issue")
    author: str = Field(description="Author of the newsletter issue")
    word_count: int = Field(description="Number of words in the newsletter issue")
    image_count: int = Field(description="Number of images in the newsletter issue")
    section_count: int = Field(description="Number of sections in the newsletter issue, sections are separated by '\n\n' characters")
    emoji_count: int = Field(description="Number of emojis in the newsletter issue")
    title_emoji_count: int = Field(description="Number of emojis in the title of the newsletter issue")
    subtitle_emoji_count: int = Field(description="Number of emojis in the subtitle of the newsletter issue")
    title_word_count: int = Field(description="Number of words in the title of the newsletter issue")
    subtitle_word_count: int = Field(description="Number of words in the subtitle of the newsletter issue")
    addressed_user_by_name: bool = Field(description="Whether the newsletter issue addresses the user by their name")
    ctas: list[str] = Field(description="List of call-to-actions (CTAs) present in the newsletter issue")
    reading_time_minutes: int = Field(description="Estimated reading time in minutes for the newsletter issue")
    overall_summary: str = Field(description="Overall summary of the newsletter issue")
    overall_intent: str = Field(description="Overall intent of the newsletter issue, e.g., to inform, to sell, to entertain, etc.")
    overall_tone: str = Field(description="Overall tone of the newsletter issue, e.g., formal, informal, friendly, professional, etc.")

def analyze_newsletter_issue(issue: Dict):
    model = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0, use_responses_api=True)
    model_response = model.invoke(, response_format=AnalysisResponse)
    return model_response
