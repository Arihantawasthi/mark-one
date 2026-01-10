from psycopg.rows import dict_row
from app.db.connector import DatabaseConnector
from psycopg import DatabaseError as PsycopgError
import json

from app.llm.models import Analysis

class DatabaseError(Exception):
    pass


def get_client_by_username(username) -> dict | None:
    sql = """SELECT * FROM client WHERE username = %s;"""

    db_conn = DatabaseConnector().connect()
    try:
        with db_conn:
            with db_conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, (username,))
                client = cursor.fetchone()
                return client

    except PsycopgError as e:
        raise DatabaseError(f"Error fetching client: {e}")


def insert_client(username, password, max_usage, max_token_usage):
    sql = """
        INSERT INTO client (username, password, max_usage, max_token_usage)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """

    db_conn = DatabaseConnector().connect()
    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(sql, (username, password, max_usage, max_token_usage))
                return cursor.fetchone()["id"]

    except PsycopgError as e:
        raise DatabaseError(f"Error inserting client: {e}")


def insert_analysis_run(display_title, notion_doc_url, niche, search_terms, total_newsletters, total_issues, status, client_id):
    sql = """
        INSERT INTO analysis_run (client_id, display_title, notion_doc_url, niche, search_terms, total_newsletters, total_issues, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """

    db_conn = DatabaseConnector().connect()
    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(sql, (client_id, display_title, notion_doc_url, niche, search_terms, total_newsletters, total_issues, status))
                analysis_run_id = cursor.fetchone()["id"]
                return analysis_run_id

    except PsycopgError as e:
        db_conn.rollback()
        raise DatabaseError(f"Error inserting search run: {e}")


def insert_issues(analysis_run_id, issues) -> list:
    if not issues:
        return []

    sql = """
        INSERT INTO issue (
            analysis_run_id, newsletter, title, subtitle, author, canonical_url, published_date,
            content, like_count, comment_count, links, toon, image_count, platform
        ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
    """

    db_conn = DatabaseConnector().connect()
    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                rows = [
                    (
                        analysis_run_id,
                        issue["newsletter"],
                        issue["title"],
                        issue["subtitle"],
                        issue["author"],
                        issue["link"],
                        issue["date"],
                        issue["content"],
                        issue["like_count"],
                        issue["comment_count"],
                        json.dumps(issue["links"]),
                        issue["toon"],
                        issue["image_count"],
                        issue["platform"]
                    )
                    for issue in issues
                ]
                cursor.executemany(sql, rows, returning=True)
                return cursor.fetchall()

    except PsycopgError as e:
        db_conn.rollback()
        raise DatabaseError(f"Error inserting issues: {e}")

def update_analysis_run_issues_and_status(analysis_run_id: int, total_issues: int, status: str):
    """
    Update total_issues and status of a analysis run.
    Args:
        analysis_run_id (int): The ID of the analysis run to update.
        total_issues (int): The total number of issues found.
        status (str): The new status of the search run.

    Raises:
        DatabaseError: If there is an error during the database operation.
    """

    sql = """
        UPDATE analysis_run
        SET total_issues = %s, status = %s
        WHERE id = %s;
    """

    db_conn = DatabaseConnector().connect()
    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(sql, (total_issues, status, analysis_run_id))

    except PsycopgError as e:
        db_conn.rollback()
        raise DatabaseError(f"Error updating search run: {e}")


def get_issues_by_analysis_run_id(analysis_run_id: int):
    sql = """SELECT * FROM issue WHERE analysis_run_id = %s;"""
    db_conn = DatabaseConnector().connect()

    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(sql, (analysis_run_id,))
                issues = cursor.fetchall()
                return issues

    except PsycopgError as e:
        db_conn.rollback()
        raise DatabaseError(f"Error fetching issues: {e}")

def serialize_links(obj):
    return {
        "type": obj.type,
        "text": obj.text,
        "url": obj.url,
    }


def insert_issue_analysis(issue_id: int, analysis: Analysis):
    data = {
        "issue_id": issue_id,
        "title": analysis.title,
        "subtitle": analysis.subtitle,
        "author": analysis.author,
        "word_count": analysis.word_count,
        "image_count": analysis.image_count,
        "like_count": analysis.like_count,
        "comment_count": analysis.comment_count,
        "section_count": analysis.section_count,
        "emoji_count": analysis.emoji_count,
        "title_emoji_count": analysis.title_emoji_count,
        "subtitle_emoji_count": analysis.subtitle_emoji_count,
        "title_word_count": analysis.title_word_count,
        "subtitle_word_count": analysis.subtitle_word_count,
        "addressed_user_by_name": analysis.addressed_user_by_name,
        "reading_time_minutes": analysis.reading_time_minutes,
        "product_mention_count": analysis.product_mention_count,
        "url": analysis.url,
        "ctas": [serialize_links(link) for link in analysis.ctas],
        "ads": [serialize_links(link) for link in analysis.ads],
        "overall_summary": analysis.overall_summary,
        "overall_intent": analysis.overall_intent,
        "overall_tone": analysis.overall_tone,
        "platform": analysis.platform,
    }

    columns = ", ".join(data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    data["ctas"] = json.dumps(data["ctas"])
    data["ads"] = json.dumps(data["ads"])

    values = tuple(data.values())

    sql = f"""
        INSERT INTO issue_analytics ({columns})
        VALUES ({placeholders})
    """

    db_conn = DatabaseConnector().connect()
    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(sql, values)
    except PsycopgError as e:
        db_conn.rollback()
        raise DatabaseError(f"Error inserting issue analysis: {e}")


def get_issue_analysis():
    sql = """SELECT * FROM issue_analytics;"""
    db_conn = DatabaseConnector().connect()

    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(sql)
                analyses = cursor.fetchall()
                return analyses

    except PsycopgError as e:
        db_conn.rollback()
        raise DatabaseError(f"Error fetching issue analyses: {e}")


def get_issue_analyses_by_issue_ids(issue_ids: list[int]):
    if not issue_ids:
        return []

    sql = f"""SELECT * FROM issue_analytics WHERE issue_id = ANY(%s);"""
    db_conn = DatabaseConnector().connect()

    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(sql, (issue_ids, ))
                return cursor.fetchall()

    except PsycopgError as e:
        db_conn.rollback()
        raise DatabaseError(f"Error fetching issue analyses: {e}")


def insert_aggregate_issue_analysis(analysis_run_id: int, aggregate_analysis):
    data = {
        "analysis_run_id": analysis_run_id,
        "overall_summary": aggregate_analysis.overall_summary,
        "overall_intent": aggregate_analysis.overall_intent,
        "overall_tone": aggregate_analysis.overall_tone,
        "avg_word_count": aggregate_analysis.avg_word_count,
        "avg_image_count": aggregate_analysis.avg_image_count,
        "avg_section_count": aggregate_analysis.avg_section_count,
        "avg_emoji_count": aggregate_analysis.avg_emoji_count,
        "avg_title_emoji_count": aggregate_analysis.avg_title_emoji_count,
        "avg_subtitle_emoji_count": aggregate_analysis.avg_subtitle_emoji_count,
        "avg_title_word_count": aggregate_analysis.avg_title_word_count,
        "avg_subtitle_word_count": aggregate_analysis.avg_subtitle_word_count,
        "reading_time_minutes": aggregate_analysis.reading_time_minutes,
        "engagement_graph": json.dumps(aggregate_analysis.engagement_graph),
    }

    columns = ", ".join(data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    values = tuple(data.values())

    sql = f"""
        INSERT INTO issue_aggregate_analytics ({columns})
        VALUES ({placeholders}) RETURNING *;
    """

    db_conn = DatabaseConnector().connect()
    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(sql, values)
                return cursor.fetchone()
    except PsycopgError as e:
        db_conn.rollback()
        raise DatabaseError(f"Error inserting aggregate issue analysis: {e}")


def get_analysis_status(analysis_run_id: int):
    sql = """SELECT status FROM analysis_run WHERE id = %s;"""
    db_conn = DatabaseConnector().connect()

    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(sql, (analysis_run_id,))
                result = cursor.fetchone()
                return result["status"] if result else None

    except PsycopgError as e:
        db_conn.rollback()
        raise DatabaseError(f"Error fetching analysis run status: {e}")


def get_agg_issue_analysis_by_run_id(analysis_run_id: int):
    sql = """SELECT * FROM issue_aggregate_analytics WHERE analysis_run_id = %s;"""
    db_conn = DatabaseConnector().connect()

    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(sql, (analysis_run_id,))
                result = cursor.fetchone()
                return result

    except PsycopgError as e:
        db_conn.rollback()
        raise DatabaseError(f"Error fetching aggregate issue analysis: {e}")

# Need to optimize this (Maybe add issue_analytics.analysis_run_id field)
def get_issue_analyses_by_analysis_run_id(analysis_run_id: int):
    sql = """ SELECT * FROM issue_analytics ia
             JOIN issue i ON ia.issue_id = i.id
             WHERE i.analysis_run_id = %s ORDER BY i.created_at DESC;"""
    db_conn = DatabaseConnector().connect()

    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(sql, (analysis_run_id,))
                analyses = cursor.fetchall()
                return analyses

    except PsycopgError as e:
        db_conn.rollback()
        raise DatabaseError(f"Error fetching issue analytics by analysis run ID: {e}")


def put_progress_statuses(analysis_run_id: int, status: dict):
    sql = """
        INSERT INTO analysis_statuses (analysis_run_id, statuses)
        VALUES (%s, %s::jsonb)
        ON CONFLICT (analysis_run_id)
        DO UPDATE SET
            statuses = analysis_statuses.statuses || %s::jsonb,
            updated_at = NOW();
    """

    db_conn = DatabaseConnector().connect()
    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                status_json_array = json.dumps([status])
                cursor.execute(sql, (analysis_run_id, status_json_array, status_json_array))

    except PsycopgError as e:
        db_conn.rollback()
        raise DatabaseError(f"Error updating progress status: {e}")


def get_analysis_progress_status(analysis_run_id: int):
    sql = """SELECT statuses FROM analysis_statuses WHERE analysis_run_id = %s;"""
    db_conn = DatabaseConnector().connect()

    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(sql, (analysis_run_id,))
                result = cursor.fetchone()
                return result["statuses"] if result else []

    except PsycopgError as e:
        db_conn.rollback()
        raise DatabaseError(f"Error fetching analysis progress status: {e}")

def get_all_analyses(client_id: int | None):
    sql = """SELECT * FROM analysis_run where client_id = %s;"""
    db_conn = DatabaseConnector().connect()

    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(sql, (client_id,))
                analyses = cursor.fetchall()
                return analyses

    except PsycopgError as e:
        db_conn.rollback()
        raise DatabaseError(f"Error fetching all issue analyses: {e}")
