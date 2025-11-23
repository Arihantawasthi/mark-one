from toon_format import encode
from app.services import substack
from app.celery.config import celery_app
import logging

from app.db import queries
from app.llm.models import Analysis, AnalysisResponse, AggregateAnalysis, AggregateAnalysisResponse

logger = logging.getLogger(__name__)

@celery_app.task(name="process_and_save_newsletters_task", bind=True)
def process_and_save_newsletters_task(self, analysis_run_id, search_result):
    logger.info(f"Starting analysis for newsletter: {search_result['title']}")
    substack.process_and_save_newsletters(analysis_run_id, search_result)
    logger.info(f"Completed analysis for newsletter: {search_result['title']}")


def construct_issue_analysis_obj(model_response: AnalysisResponse, issue: dict) -> Analysis:
    return Analysis(
        **model_response.model_dump(),
        image_count=issue.get("image_count", 0),
        like_count=issue.get("like_count", 0),
        comment_count=issue.get("comment_count", 0)
    )


@celery_app.task(name="analyze_issue_task", bind=True)
def analyze_issue_task(self, issue):
    from app.llm import agent

    analysis = agent.analyze_newsletter_issue(issue)
    analysis_model = construct_issue_analysis_obj(analysis, issue)
    queries.insert_issue_analysis(issue["id"], analysis_model)


@celery_app.task(name="test_task", bind=True)
def test_task(self):
    for _ in range(5):
        logger.error("TEST TASK EXECUTED")


def construct_agg_analysis_obj(model_response: AggregateAnalysisResponse, engagement_graph: dict, issue_analyses: dict) -> AggregateAnalysis:
    return AggregateAnalysis(
        **model_response.model_dump(),
        engagement_graph=engagement_graph,
        avg_word_count=sum([analysis["word_count"] for analysis in issue_analyses]) / len(issue_analyses),
        avg_image_count=sum([analysis["image_count"] for analysis in issue_analyses]) / len(issue_analyses),
        avg_section_count=sum([analysis["section_count"] for analysis in issue_analyses]) / len(issue_analyses),
        avg_emoji_count=sum([analysis["emoji_count"] for analysis in issue_analyses]) / len(issue_analyses),
        avg_title_emoji_count=sum([analysis["title_emoji_count"] for analysis in issue_analyses]) / len(issue_analyses),
        avg_subtitle_emoji_count=sum([analysis["subtitle_emoji_count"] for analysis in issue_analyses]) / len(issue_analyses),
        avg_title_word_count=sum([analysis["title_word_count"] for analysis in issue_analyses]) / len(issue_analyses),
        avg_subtitle_word_count=sum([analysis["subtitle_word_count"] for analysis in issue_analyses]) / len(issue_analyses),
        reading_time_minutes=sum([analysis["reading_time_minutes"] for analysis in issue_analyses]) / len(issue_analyses),
    )


@celery_app.task(name="aggregate_issue_analysis", bind=True)
def aggregate_issue_analysis(self, issue_ids, analysis_run_id):
    from app.llm import agent

    issue_analyses = queries.get_issue_analyses_by_issue_ids(issue_ids)
    engagement_graph = generate_engagement_graph(issue_analyses)

    metrics_to_analyze = []
    for analysis in issue_analyses:
        metrics_to_analyze.append({
            "overall_summary": analysis["overall_summary"],
            "overall_intent": analysis["overall_intent"],
            "overall_tone": analysis["overall_tone"],
        })

    individual_analyses = encode(metrics_to_analyze)
    aggregate_analysis = agent.aggregate_issue_analysis(individual_analyses)
    # logger.error(f"AGGREGATE ANALYSIS COMPLETED: {individual_analyses}")
    aggregate_analysis_obj = construct_agg_analysis_obj(aggregate_analysis, engagement_graph, issue_analyses)

    result = queries.insert_aggregate_issue_analysis(analysis_run_id, aggregate_analysis_obj)
    return result


def generate_engagement_graph(issue_analyses):
    engagement_data = []
    for analysis in issue_analyses:
        engagement_data.append({
            "issue_id": analysis["issue_id"],
            "word_count": analysis["word_count"],
            "like_count": analysis["like_count"],
            "comment_count": analysis["comment_count"],
            "engagement_score": analysis["like_count"] + (3 * analysis["comment_count"])
        })

    engagement_data = sorted(engagement_data, key=lambda x: x["word_count"])
    return engagement_data
