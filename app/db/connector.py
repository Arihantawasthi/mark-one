import psycopg
import app.core.settings as settings

class DatabaseConnector:
    def __init__(self):
        self.connection = None

    def connect(self):
        if self.connection is None:
            DSN = (
                f"dbname={settings.DATABASE_NAME} "
                f"user={settings.DATABASE_USER} "
                f"password={settings.DATABASE_PASSWORD} "
                f"host={settings.DATABASE_HOST} "
                f"port={settings.DATABASE_PORT}"
            )
            self.connection = psycopg.connect(
                DSN,
                row_factory=psycopg.rows.dict_row
            )
        return self.connection

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
