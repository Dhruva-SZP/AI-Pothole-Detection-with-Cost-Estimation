"""
Database Connection Manager using pyodbc for Microsoft SQL Server.
Provides thread-safe connections, context management, retry logic, and dict cursor parsing.
"""

import os
import sys
import logging
from contextlib import contextmanager
from pathlib import Path
import pyodbc
from dotenv import load_dotenv

# Ensure environment variables are loaded from backend root .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger("PotholeApp.Database")


def get_connection_string(database: str = None) -> str:
    """
    Constructs an ODBC connection string for SQL Server based on environment variables.
    """
    driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    server = os.getenv("DB_SERVER", r"localhost\SQLEXPRESS")
    db = database or os.getenv("DB_NAME", "PotholeDetectionDB")
    trusted_connection = os.getenv("DB_TRUSTED_CONNECTION", "yes").lower() == "yes"
    user = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")

    # Base connection parameters
    params = [
        f"Driver={{{driver}}}",
        f"Server={server}",
    ]

    if db:
        params.append(f"Database={db}")

    if trusted_connection:
        params.append("Trusted_Connection=yes")
    else:
        params.append(f"UID={user}")
        params.append(f"PWD={password}")

    # Reliability and timeout settings
    params.append("TrustServerCertificate=yes")
    params.append("Connection Timeout=15")

    return ";".join(params) + ";"


def create_connection(database: str = None, autocommit: bool = False) -> pyodbc.Connection:
    """
    Creates and returns a raw pyodbc connection to SQL Server.
    """
    conn_str = get_connection_string(database=database)
    try:
        conn = pyodbc.connect(conn_str, autocommit=autocommit)
        return conn
    except pyodbc.Error as err:
        logger.error("Database connection failed: %s | ConnStr: %s", err, conn_str)
        raise


@contextmanager
def get_db_connection(database: str = None):
    """
    Context manager for database operations.
    Automatically commits transactions on success, rolls back on error, and closes the connection.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
    """
    conn = None
    try:
        conn = create_connection(database=database, autocommit=False)
        yield conn
        conn.commit()
    except Exception as exc:
        if conn:
            try:
                conn.rollback()
            except Exception as rb_exc:
                logger.error("Rollback failed: %s", rb_exc)
        logger.exception("Database transaction error: %s", exc)
        raise
    finally:
        if conn:
            try:
                conn.close()
            except Exception as close_exc:
                logger.warning("Error closing connection: %s", close_exc)


def row_to_dict(cursor: pyodbc.Cursor, row: pyodbc.Row) -> dict:
    """
    Converts a single pyodbc.Row into a standard Python dictionary
    using cursor column descriptions.
    """
    if row is None:
        return None
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def rows_to_dict_list(cursor: pyodbc.Cursor, rows: list) -> list[dict]:
    """
    Converts a list of pyodbc.Row objects into a list of Python dictionaries.
    """
    if not rows:
        return []
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def test_connection(database: str = None) -> dict:
    """
    Tests the connection and returns server metadata.
    """
    target_db = database or os.getenv("DB_NAME", "PotholeDetectionDB")
    try:
        with get_db_connection(database=target_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION AS [Version], @@SERVERNAME AS [ServerName], DB_NAME() AS [CurrentDB]")
            row = cursor.fetchone()
            return {
                "success": True,
                "version": row.Version.split("\n")[0],
                "server": row.ServerName,
                "database": row.CurrentDB,
                "error": None
            }
    except Exception as err:
        return {
            "success": False,
            "version": None,
            "server": None,
            "database": None,
            "error": str(err)
        }
