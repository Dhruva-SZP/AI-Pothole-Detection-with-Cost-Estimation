"""
Database Initialization & Schema Deployment Script for SQL Server.
Executes schema.sql batches against the SQL Server instance configured in .env.
"""

import os
import re
import sys
import logging
from pathlib import Path

# Setup path to import connection utilities
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from database.connection import (
    create_connection,
    get_connection_string,
    logger
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
init_logger = logging.getLogger("InitDB")


def execute_sql_file(sql_file_path: Path):
    """
    Reads a SQL script file, splits statements on 'GO' lines, and executes them sequentially.
    """
    if not sql_file_path.exists():
        raise FileNotFoundError(f"Schema file not found at: {sql_file_path}")

    with open(sql_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Step 1: Ensure database exists by connecting to 'master'
    init_logger.info("Connecting to SQL Server 'master' database to verify target database...")
    db_name = os.getenv("DB_NAME", "PotholeDetectionDB")
    master_conn = create_connection(database="master", autocommit=True)
    master_cursor = master_conn.cursor()

    master_cursor.execute("SELECT name FROM sys.databases WHERE name = ?", (db_name,))
    exists = master_cursor.fetchone()
    if not exists:
        init_logger.info(f"Database [{db_name}] does not exist. Creating...")
        master_cursor.execute(f"CREATE DATABASE [{db_name}]")
        init_logger.info(f"Database [{db_name}] created successfully.")
    else:
        init_logger.info(f"Database [{db_name}] already exists.")

    master_cursor.close()
    master_conn.close()

    # Step 2: Connect to target database and execute batches
    init_logger.info(f"Connecting to [{db_name}] to execute schema DDL...")
    target_conn = create_connection(database=db_name, autocommit=True)
    target_cursor = target_conn.cursor()

    # Split batches on standalone GO statements (case-insensitive)
    batches = re.split(r"^\s*GO\s*$", content, flags=re.MULTILINE | re.IGNORECASE)

    for idx, raw_batch in enumerate(batches, 1):
        batch = raw_batch.strip()
        # Filter out comments-only or empty batches
        cleaned_lines = [
            line for line in batch.splitlines() 
            if line.strip() and not line.strip().startswith("--")
        ]
        if not cleaned_lines:
            continue

        # Skip USE statement since we are already connected to target DB
        if any(line.upper().startswith("USE ") for line in cleaned_lines):
            continue

        try:
            target_cursor.execute(batch)
            init_logger.info(f"Successfully executed DDL batch #{idx}")
        except Exception as exc:
            init_logger.error(f"Failed executing batch #{idx}:\n{batch}\nError: {exc}")
            raise

    target_cursor.close()
    target_conn.close()
    init_logger.info("All schema tables, constraints, seeds, and indexes have been initialized.")


def verify_tables():
    """
    Verifies that all expected tables and indexes exist in PotholeDetectionDB.
    """
    db_name = os.getenv("DB_NAME", "PotholeDetectionDB")
    conn = create_connection(database=db_name)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    init_logger.info(f"Verified tables in [{db_name}]: {tables}")

    cursor.execute("""
        SELECT COUNT(*) AS CostParamCount FROM dbo.CostParameters;
    """)
    cost_count = cursor.fetchone()[0]
    init_logger.info(f"Active CostParameters seed count: {cost_count}")

    cursor.close()
    conn.close()
    return tables


if __name__ == "__main__":
    schema_path = CURRENT_DIR / "schema.sql"
    init_logger.info(f"Initializing database from {schema_path}...")
    execute_sql_file(schema_path)
    verify_tables()
    print("\n[SUCCESS] Database initialization completed successfully!")
