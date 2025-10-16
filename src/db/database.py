import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Generator
from ..core.config import settings


def get_db_connection():
    """Create a database connection."""
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        dbname=settings.DB_NAME,
        user=settings.DB_USERNAME,
        password=settings.DB_PASSWORD,
        port=settings.DB_PORT,
        cursor_factory=RealDictCursor
    )
    return conn


@contextmanager
def get_db() -> Generator:
    """Context manager for database connection."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def execute_query(query: str, params: tuple = None):
    """Execute a query and return results."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            try:
                return cur.fetchall()
            except psycopg2.ProgrammingError:
                return None


def execute_one(query: str, params: tuple = None):
    """Execute a query and return one result."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()
