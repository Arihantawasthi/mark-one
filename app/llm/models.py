from pydantic import BaseModel, Field

class LinkObject(BaseModel):
    type: str = Field(description="Type of CTA or ad ")
    text: str = Field(description="Text of the CTA or ad")
    url: str = Field(description="URL of the CTA or ad")

    class Config:
        extra = "forbid"

class AnalysisResponse(BaseModel):
    title: str = Field(description="Title of the newsletter issue")
    subtitle: str = Field(description="Subtitle of the newsletter issue")
    author: str = Field(description="Author of the newsletter issue")
    word_count: int = Field(description="Number of words in the newsletter issue")
    section_count: int = Field(description="Number of sections in the newsletter issue")
    emoji_count: int = Field(description="Number of emojis in the newsletter issue")
    title_emoji_count: int = Field(description="Number of emojis in the title of the newsletter issue")
    subtitle_emoji_count: int = Field(description="Number of emojis in the subtitle of the newsletter issue")
    title_word_count: int = Field(description="Number of words in the title of the newsletter issue")
    subtitle_word_count: int = Field(description="Number of words in the subtitle of the newsletter issue")
    addressed_user_by_name: bool = Field(description="Whether the newsletter issue addresses the user by their name")
    reading_time_minutes: int = Field(description="Estimated reading time in minutes for the newsletter issue")
    product_mention_count: int = Field(description="Number of product mentions in the newsletter issue")
    url: str = Field(description="URL of the newsletter issue")
    ctas: list[LinkObject] = Field(description="List of call-to-actions (CTAs) present in the newsletter issue, consider only links")
    ads: list[LinkObject] = Field(description="List of advertisements present in the newsletter issue, analyze if there's any promotional content for brand, product, or anything with link")
    overall_summary: str = Field(description="Overall summary of the newsletter issue")
    overall_intent: str = Field(description="Overall intent of the newsletter issue, e.g., to inform, to sell, to entertain, etc.")
    overall_tone: str = Field(description="Overall tone of the newsletter issue, e.g., formal, informal, friendly, professional, etc.")


class AggregateAnalysisResponse(BaseModel):
    overall_summary: str = Field(description="Aggregated overall summary of the newsletter")
    overall_intent: str = Field(description="Aggregated overall intent of the newsletter")
    overall_tone: str = Field(description="Aggregated overall tone of the newsletter")


class AggregateAnalysis(AggregateAnalysisResponse):
    avg_word_count: float
    avg_image_count: float
    avg_section_count: float
    avg_emoji_count: float
    avg_title_emoji_count: float
    avg_subtitle_emoji_count: float
    avg_title_word_count: float
    avg_subtitle_word_count: float
    reading_time_minutes: float
    engagement_graph: list[dict]

class Analysis(AnalysisResponse):
    image_count: int
    like_count: int
    comment_count: int
    platform: str
