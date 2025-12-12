import logging
from toon_format import encode
from app.db import queries
from app.llm import agent
from app.llm.models import AggregateAnalysis, AggregateAnalysisResponse, Analysis, AnalysisResponse

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, analysis_run_id: int, issue: dict):
        self.issue = issue
        self.analysis_run_id = analysis_run_id

    def analyze_issue(self):
        logger.info(
            f"[Issue Analysis] Calling LLM for issue ID: {self.issue['id']}",
            extra={ "analysis_run_id": self.analysis_run_id, "issue_id": self.issue["id"] }
        )

        analysis_response: AnalysisResponse = agent.analyze_newsletter_issue(self.issue)
        analysis_model = Analysis(
            **analysis_response.model_dump(),
            image_count=self.issue.get("image_count", 0),
            like_count=self.issue.get("like_count", 0),
            comment_count=self.issue.get("comment_count", 0),
            platform=self.issue.get("platform", "")
        )

        queries.insert_issue_analysis(self.issue["id"], analysis_model)

        logger.info(
            f"[Issue Analysis] Completed and saved Analysis for issue ID: {self.issue['id']}",
            extra={ "analysis_run_id": self.analysis_run_id, "issue_id": self.issue["id"] }
        )


    def aggregate_analysis(self, issue_ids: list[int]):
        logger.info(
            f"[Aggregate Analysis] Loading issue anayses",
            extra={ "analysis_run_id": self.analysis_run_id, "issue_count": len(issue_ids) }
        )

        issue_analyses = queries.get_issue_analyses_by_issue_ids(issue_ids)
        if not issue_analyses:
            logger.error(
                f"[Aggregate Analysis] No issue analyses found",
                extra={ "analysis_run_id": self.analysis_run_id }
            )
            return None

        engagement_graph = self._generate_engagement_graph(issue_analyses)
        metrics_to_analyze = [
            {
                "overall_summary": analysis["overall_summary"],
                "overall_intent": analysis["overall_intent"],
                "overall_tone": analysis["overall_tone"],
            }
            for analysis in issue_analyses
        ]

        encoded_metrics = encode(metrics_to_analyze)

        logger.info(
            f"[Aggregate Analysis] Calling LLM for aggregate analysis",
            extra={ "analysis_run_id": self.analysis_run_id  }
        )
        agg_response: AggregateAnalysisResponse = agent.aggregate_issue_analysis(encoded_metrics)
        aggregate_analysis_obj = self._construct_agg_obj(agg_response, engagement_graph, issue_analyses)

        results = queries.insert_aggregate_issue_analysis(self.analysis_run_id, aggregate_analysis_obj)
        queries.update_analysis_run_issues_and_status(self.analysis_run_id, len(issue_ids), "completed")
        logger.info(
            f"[Aggregate Analysis] Completed and saved aggregate analysis",
            extra={ "analysis_run_id": self.analysis_run_id  }
        )
        return results



    def _generate_engagement_graph(self, issue_analyses: dict) -> dict:
        data = []
        for analysis in issue_analyses:
            likes = analysis["like_count"]
            comments = analysis["comment_count"]
            data.append({
                "issue_id": analysis["issue_id"],
                "word_count": analysis["word_count"],
                "like_count": likes,
                "comment_count": comments,
                # Simple engagement score algorithm
                "engagement_score": likes + (3 * comments)
            })

        return sorted(data, key=lambda x: x["word_count"])


    def _construct_agg_obj(
        self,
        model_response: AggregateAnalysisResponse,
        engagement_graph: dict,
        issue_analyses: dict
    ) -> AggregateAnalysis | None:
        count = len(issue_analyses)
        if count == 0:
            return None # Handle div by zero if necessary

        def avg(key):
            return sum(a[key] for a in issue_analyses) / count

        return AggregateAnalysis(
            **model_response.model_dump(),
            engagement_graph=engagement_graph,
            avg_word_count=avg("word_count"),
            avg_image_count=avg("image_count"),
            avg_section_count=avg("section_count"),
            avg_emoji_count=avg("emoji_count"),
            avg_title_emoji_count=avg("title_emoji_count"),
            avg_subtitle_emoji_count=avg("subtitle_emoji_count"),
            avg_title_word_count=avg("title_word_count"),
            avg_subtitle_word_count=avg("subtitle_word_count"),
            reading_time_minutes=avg("reading_time_minutes"),
        )
