from app.llm.prompt import issue_analysis_prompt_v1, aggregate_issue_analysis_prompt
from langchain_openai import ChatOpenAI
from app.core import settings

from app.llm.models import AnalysisResponse, AggregateAnalysisResponse


def analyze_newsletter_issue(issue: dict) -> AnalysisResponse:
    model = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0, use_responses_api=True)
    prompt = issue_analysis_prompt_v1.format(
        url=issue.get("canonical_url", ""),
        title=issue["title"],
        subtitle=issue["subtitle"],
        content=issue["content"]
    )
    model_response = model.invoke(prompt, response_format=AnalysisResponse)
    response_object = model_response.additional_kwargs["parsed"]
    response_object.image_count = issue.get("image_count", 0)
    response_object.like_count = issue.get("like_count", 0)
    response_object.comment_count = issue.get("comment_count", 0)
    return response_object


def aggregate_issue_analysis(individual_analyses: str) -> AggregateAnalysisResponse:
    model = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0, use_responses_api=True)
    prompt = aggregate_issue_analysis_prompt.format(
        individual_analyses=individual_analyses
    )
    model_response = model.invoke(prompt, response_format=AggregateAnalysisResponse)
    response_object = model_response.additional_kwargs["parsed"]
    return response_object
