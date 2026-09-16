"""
Universal Database Connection Manager for Microsoft SQL Server.
Supports both pymssql (FreeTDS embedded - zero-dependency Linux/Render compatible)
and pyodbc (Windows native ODBC).
Provides thread-safe connections, automatic placeholder translation (? -> %s),
context management, transaction commits/rollbacks, and dictionary cursor parsing.
"""

import os
import sys
import logging
from contextlib import contextmanager
from pathlib import Path
from dotenv import load_dotenv

# Ensure environment variables are loaded from backend root .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger("PotholeApp.Database")

# Driver availability checks
try:
    import pymssql
    PYMSSQL_AVAILABLE = True
except ImportError:
    pymssql = None
    PYMSSQL_AVAILABLE = False

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    pyodbc = None
    PYODBC_AVAILABLE = False


def get_db_credentials(database: str = None) -> dict:
    """
    Parses and sanitizes database connection parameters from environment variables.
    Handles host:port parsing in DB_SERVER automatically.
    """
    is_render = "RENDER" in os.environ or sys.platform != "win32"

    raw_server = os.getenv("DB_SERVER", "").strip()
    raw_port = os.getenv("DB_PORT", "").strip()
    db = (database or os.getenv("DB_NAME", "PotholeDetectionDB")).strip()
    user = os.getenv("DB_USER", "").strip()
    password = os.getenv("DB_PASSWORD", "").strip()
    driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server").strip()

    # On cloud / Render, 'localhost' is unreachable because the SQL Server runs on the user's local PC.
    # Default to the active public tunnel endpoint if not explicitly overridden by user:
    if is_render and (not raw_server or raw_server.lower().startswith("localhost") or raw_server == "127.0.0.1"):
        raw_server = "bore.pub"
        if not raw_port:
            raw_port = "41982"
        if not user:
            user = "pothole_app"
        if not password:
            password = "PotholeSecure2026!"

    if not raw_server:
        raw_server = r"localhost\SQLEXPRESS"

    # Determine default trusted connection
    trusted_env = os.getenv("DB_TRUSTED_CONNECTION", "")
    if trusted_env:
        trusted_connection = trusted_env.lower() in ("yes", "true", "1")
    else:
        # Default to trusted only on Windows if no user/password is specified and not on Render
        trusted_connection = sys.platform == "win32" and not user and not is_render

    # Parse host and port if passed together e.g. "0.tcp.ngrok.io:19456"
    server_host = raw_server
    port = None

    if ":" in raw_server and not raw_server.startswith(r"\\"):
        parts = raw_server.split(":", 1)
        server_host = parts[0].strip()
        if parts[1].strip().isdigit():
            port = int(parts[1].strip())

    if raw_port and raw_port.isdigit():
        port = int(raw_port)

    return {
        "server": server_host,
        "raw_server": raw_server,
        "port": port,
        "database": db,
        "user": user,
        "password": password,
        "trusted_connection": trusted_connection,
        "driver": driver
    }


def should_use_pymssql(creds: dict) -> bool:
    """
    Determines whether pymssql should be used instead of pyodbc.
    Prefers pymssql for:
    - Linux environments (including Render where MS ODBC driver is not installed)
    - TCP tunnel / remote connections with SQL Authentication
    - When pyodbc is not installed
    """
    if not PYODBC_AVAILABLE:
        return True
    if not PYMSSQL_AVAILABLE:
        return False

    # Render or Linux OS
    if sys.platform != "win32" or "RENDER" in os.environ:
        return True

    # TCP port specified or SQL user specified with trusted_connection=False
    if not creds["trusted_connection"] and (creds["user"] or creds["port"]):
        return True

    return False


def get_safe_db_summary(creds: dict = None) -> str:
    """
    Returns a masked summary of the database connection configuration.
    NEVER leaks DB_PASSWORD.
    """
    c = creds or get_db_credentials()
    port_str = f":{c['port']}" if c["port"] else ""
    auth_type = "Windows Authentication" if c["trusted_connection"] else f"SQL Login ({c['user'] or 'none'})"
    preferred_lib = "pymssql (FreeTDS)" if should_use_pymssql(c) else "pyodbc"
    return (
        f"Server=[{c['server']}{port_str}], Database=[{c['database']}], "
        f"Auth=[{auth_type}], Driver=[{preferred_lib}]"
    )


class PyMssqlCursorWrapper:
    """
    Cursor wrapper for pymssql that transparently adapts DB-API '?' (qmark)
    placeholders to '%s' (pyformat) placeholders used by pymssql/FreeTDS.
    """
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql: str, params=None):
        if params is not None:
            # Convert '?' placeholders to '%s' for pymssql compatibility
            formatted_sql = sql.replace("?", "%s")
            if isinstance(params, (list, tuple)):
                return self._cursor.execute(formatted_sql, tuple(params))
            return self._cursor.execute(formatted_sql, (params,))
        return self._cursor.execute(sql)

    def executemany(self, sql: str, seq_of_params):
        formatted_sql = sql.replace("?", "%s")
        return self._cursor.executemany(formatted_sql, seq_of_params)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchmany(self, size=None):
        return self._cursor.fetchmany(size) if size is not None else self._cursor.fetchmany()

    @property
    def description(self):
        return self._cursor.description

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        return self._cursor.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class PyMssqlConnectionWrapper:
    """
    Connection wrapper for pymssql ensuring wrapped cursors and standard context management.
    """
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, *args, **kwargs):
        return PyMssqlCursorWrapper(self._conn.cursor(*args, **kwargs))

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __getattr__(self, name):
        return getattr(self._conn, name)


def get_connection_string(database: str = None) -> str:
    """
    Constructs an ODBC connection string for SQL Server (used by pyodbc).
    """
    creds = get_db_credentials(database=database)
    driver = creds["driver"]
    server = creds["server"]
    if creds["port"]:
        server = f"{server},{creds['port']}"
    elif creds["raw_server"]:
        server = creds["raw_server"]

    params = [
        f"Driver={{{driver}}}",
        f"Server={server}",
    ]

    if creds["database"]:
        params.append(f"Database={creds['database']}")

    if creds["trusted_connection"]:
        params.append("Trusted_Connection=yes")
    else:
        params.append(f"UID={creds['user']}")
        params.append(f"PWD={creds['password']}")

    params.append("TrustServerCertificate=yes")
    params.append("Connection Timeout=15")

    return ";".join(params) + ";"


def create_connection(database: str = None, autocommit: bool = False):
    """
    Creates and returns a database connection using either pymssql or pyodbc.
    Automatically selects the best driver and translates parameters.
    """
    creds = get_db_credentials(database=database)
    use_pymssql = should_use_pymssql(creds)

    is_render = "RENDER" in os.environ or sys.platform != "win32"
    server_is_local = creds["server"].lower().startswith("localhost") or creds["server"] == "127.0.0.1"

    # On cloud / Render: if DB_SERVER has not been pointed to an external host/tunnel,
    # avoid hanging on UDP 1434 broadcast lookup to non-existent localhost SQLEXPRESS.
    if is_render and server_is_local and not os.getenv("DB_SERVER"):
        raise ConnectionError(
            "SQL Server is not running on Render container localhost. "
            "Configure DB_SERVER and DB_PORT with your ngrok tunnel in Render Environment."
        )

    if use_pymssql:
        if not PYMSSQL_AVAILABLE:
            raise RuntimeError("pymssql is required but not installed in the current environment.")
        try:
            # Clean server name for FreeTDS / pymssql (strip instance name if port/tunnel is used)
            connect_server = creds["server"]
            if "\\" in connect_server and (creds["port"] or is_render):
                connect_server = connect_server.split("\\", 1)[0]

            connect_kwargs = {
                "server": connect_server,
                "database": creds["database"],
                "user": creds["user"],
                "password": creds["password"],
                "autocommit": autocommit,
                "timeout": int(os.getenv("DB_TIMEOUT", "4")),
                "login_timeout": int(os.getenv("DB_LOGIN_TIMEOUT", "4"))
            }
            if creds["port"]:
                connect_kwargs["port"] = creds["port"]

            raw_conn = pymssql.connect(**connect_kwargs)
            return PyMssqlConnectionWrapper(raw_conn)
        except Exception as err:
            logger.error("pymssql connection failed to [%s:%s] DB [%s]: %s",
                         creds["server"], creds["port"], creds["database"], err)
            # If on Windows and pyodbc is available as a fallback, attempt pyodbc
            if sys.platform == "win32" and PYODBC_AVAILABLE and creds["trusted_connection"]:
                logger.info("Attempting fallback to pyodbc on Windows...")
                return _create_pyodbc_connection(database, autocommit)
            raise

    # Otherwise use pyodbc
    return _create_pyodbc_connection(database, autocommit)


def _create_pyodbc_connection(database: str = None, autocommit: bool = False):
    """
    Internal helper to create a pyodbc connection.
    """
    if not PYODBC_AVAILABLE:
        raise RuntimeError("pyodbc is required for ODBC connection but is not installed.")
    conn_str = get_connection_string(database=database)
    try:
        conn = pyodbc.connect(conn_str, autocommit=autocommit)
        return conn
    except Exception as err:
        creds = get_db_credentials(database=database)
        safe_info = (f"Server={creds['server']}, Database={creds['database']}, "
                     f"Trusted={creds['trusted_connection']}, User={creds['user']}")
        logger.error("pyodbc connection failed: %s | Info: %s", err, safe_info)
        raise


@contextmanager
def get_db_connection(database: str = None):
    """
    Context manager for database operations.
    Automatically commits transactions on success, rolls back on error, and closes the connection.
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


def row_to_dict(cursor, row) -> dict:
    """
    Converts a single row (pyodbc.Row or tuple) into a standard Python dictionary
    using cursor column descriptions.
    """
    if row is None:
        return None
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def rows_to_dict_list(cursor, rows: list) -> list[dict]:
    """
    Converts a list of row objects into a list of Python dictionaries.
    """
    if not rows:
        return []
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def test_connection(database: str = None) -> dict:
    """
    Tests the connection and returns server metadata, driver info, and latency.
    NEVER leaks DB_PASSWORD.
    """
    creds = get_db_credentials(database=database)
    target_db = creds["database"]
    driver_name = "pymssql (FreeTDS)" if should_use_pymssql(creds) else "pyodbc"

    is_render = "RENDER" in os.environ or sys.platform != "win32"
    server_is_local = creds["server"].lower().startswith("localhost") or creds["server"] == "127.0.0.1"

    if is_render and server_is_local and not os.getenv("DB_SERVER"):
        return {
            "success": False,
            "version": None,
            "server": creds["server"],
            "database": target_db,
            "driver": driver_name,
            "error": "SQL Server is offline (waiting for ngrok tunnel). Configure DB_SERVER and DB_PORT in Render."
        }

    try:
        with get_db_connection(database=target_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION AS [Version], @@SERVERNAME AS [ServerName], DB_NAME() AS [CurrentDB]")
            row = cursor.fetchone()
            row_dict = row_to_dict(cursor, row)
            version_str = row_dict.get("Version") or (row[0] if row else "")
            server_str = row_dict.get("ServerName") or (row[1] if len(row) > 1 else "")
            db_str = row_dict.get("CurrentDB") or (row[2] if len(row) > 2 else target_db)

            return {
                "success": True,
                "version": version_str.split("\n")[0] if version_str else "Unknown",
                "server": server_str or creds["server"],
                "database": db_str,
                "driver": driver_name,
                "error": None
            }
    except Exception as err:
        return {
            "success": False,
            "version": None,
            "server": creds["server"],
            "database": target_db,
            "driver": driver_name,
            "error": str(err)
        }

