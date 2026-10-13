import os
from functools import lru_cache
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def resolve_database_url(secrets: Any = None) -> str | None:
    database_url = os.getenv("DATABASE_URL", "").strip()

    # Support discrete environment variables (commonly set on Render / container platforms)
    env_db_fields = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    alt_env_db_fields = ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD")

    if not database_url and all(os.getenv(k, "").strip() for k in env_db_fields):
        database_url = URL.create(
            "postgresql+psycopg",
            username=os.getenv("DB_USER", "").strip(),
            password=os.getenv("DB_PASSWORD", "").strip(),
            host=os.getenv("DB_HOST", "").strip(),
            port=int(os.getenv("DB_PORT", "5432").strip()),
            database=os.getenv("DB_NAME", "").strip(),
            query={"sslmode": os.getenv("DB_SSLMODE", "require").strip()},
        ).render_as_string(hide_password=False)
    elif not database_url and all(os.getenv(k, "").strip() for k in alt_env_db_fields):
        database_url = URL.create(
            "postgresql+psycopg",
            username=os.getenv("PGUSER", "").strip(),
            password=os.getenv("PGPASSWORD", "").strip(),
            host=os.getenv("PGHOST", "").strip(),
            port=int(os.getenv("PGPORT", "5432").strip()),
            database=os.getenv("PGDATABASE", "").strip(),
            query={"sslmode": os.getenv("PGSSLMODE", "require").strip()},
        ).render_as_string(hide_password=False)

    if not database_url and secrets is not None:
        try:
            database_config = secrets.get("database", {})
            database_url = str(database_config.get("url", "")).strip()
            required_fields = ("host", "port", "database", "user", "password")
            if not database_url and all(str(database_config.get(key, "")).strip() for key in required_fields):
                database_url = URL.create(
                    "postgresql+psycopg",
                    username=str(database_config["user"]),
                    password=str(database_config["password"]),
                    host=str(database_config["host"]),
                    port=int(database_config["port"]),
                    database=str(database_config["database"]),
                    query={"sslmode": str(database_config.get("sslmode", "require"))},
                ).render_as_string(hide_password=False)
        except (AttributeError, TypeError):
            database_url = ""

    if not database_url:
        return None
    if database_url.startswith("postgres://"):
        database_url = "postgresql+psycopg://" + database_url[len("postgres://"):]
    elif database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url[len("postgresql://"):]
    try:
        parsed_url = make_url(database_url)
        if parsed_url.drivername == "postgresql+psycopg" and not parsed_url.query.get("sslmode"):
            database_url = parsed_url.update_query_dict({"sslmode": "require"}).render_as_string(
                hide_password=False
            )
    except Exception:
        return None
    return database_url


@lru_cache(maxsize=4)
def get_engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)


def get_session_factory(database_url: str):
    return sessionmaker(bind=get_engine(database_url), expire_on_commit=False)
