import psycopg2
import app.core.settings as settings

class DatabaseConnector:
    def __init__(self):
        self.connection = None

    def connect(self):
        if self.connection is None:
            self.connection = psycopg2.connect(
                dbname=settings.DATABASE_NAME,
                user=settings.DATABASE_USER,
                password=settings.DATABASE_PASSWORD,
                host=settings.DATABASE_HOST,
                port=settings.DATABASE_PORT
            )
        return self.connection

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
