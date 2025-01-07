import sqlite3
from contextlib import contextmanager
from config import Config

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DATABASE_PATH)
        self.conn.row_factory = sqlite3.Row
        self.setup_database()

    @contextmanager
    def get_cursor(self):
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def setup_database(self):
        with self.get_cursor() as cursor:
            cursor.executescript('''
                CREATE TABLE IF NOT EXISTS responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT UNIQUE NOT NULL,
                    response_type TEXT NOT NULL,
                    response_content TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS server_roles (
                    server_id INTEGER PRIMARY KEY,
                    role_name TEXT
                );
                CREATE TABLE IF NOT EXISTS stars (
                    user_id TEXT PRIMARY KEY,
                    user_mention TEXT,
                    stars INTEGER
                );
            ''')

    def create_server_tables(self, server_id):
        with self.get_cursor() as cursor:
            cursor.executescript(f'''
                CREATE TABLE IF NOT EXISTS responses_{server_id} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT UNIQUE NOT NULL,
                    response_type TEXT NOT NULL,
                    response_content TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS stars_{server_id} (
                    user_id TEXT PRIMARY KEY,
                    user_mention TEXT,
                    stars INTEGER
                );
            ''')

db_manager = DatabaseManager()