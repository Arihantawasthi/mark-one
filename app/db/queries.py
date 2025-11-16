from app.db.connector import DatabaseConnector
from psycopg import DatabaseError as PsycopgError

class DatabaseError(Exception):
    pass

def insert_analysis_run(notion_doc_url, niche, search_terms, total_newsletters, total_issues, status):
    sql = """
        INSERT INTO analysis_run (notion_doc_url, niche, search_terms, total_newsletters, total_issues, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
    """

    db_conn = DatabaseConnector().connect()
    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(sql, (notion_doc_url, niche, search_terms, total_newsletters, total_issues, status))
                analysis_run_id = cursor.fetchone()["id"]
                return analysis_run_id

    except PsycopgError as e:
        db_conn.rollback()
        raise DatabaseError(f"Error inserting search run: {e}")


def insert_issues(analysis_run_id, newsletter_title, issues):
    if not issues:
        return

    sql = """
        INSERT INTO issue (
            newsletter, analysis_run_id, title, subtitle, author,
            canonical_url, published_date, content, image_count
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    db_conn = DatabaseConnector().connect()
    try:
        with db_conn:
            with db_conn.cursor() as cursor:
                rows = [
                    (
                        newsletter_title,
                        analysis_run_id,
                        issue["title"],
                        issue["subtitle"],
                        issue["author"],
                        issue["link"],
                        issue["date"],
                        issue["content"],
                        issue["num_of_images"]
                    )
                    for issue in issues
                ]
                cursor.executemany(sql, rows)

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
