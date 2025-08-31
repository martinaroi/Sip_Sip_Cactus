"""Database connection singleton for SQLAlchemy."""
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import Engine
import os

from plant_health_tracker.config.base import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)

class DatabaseConnection:
    """Singleton class for managing database connections."""
    
    _instance: Optional['DatabaseConnection'] = None
    _engine: Optional[Engine] = None
    _SessionLocal: Optional[sessionmaker] = None

    def __new__(cls) -> 'DatabaseConnection':
        """Create a new instance of DatabaseConnection if it doesn't exist."""
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the database connection if it hasn't been initialized."""
        if self._engine is None:
            self._initialize_connection()

    def _initialize_connection(self):
        """Initialize the database connection and session factory."""
    # Prefer full connection string from env or Streamlit secrets if provided
        db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_CONNECTION_STRING")

        # Try Streamlit secrets if available (e.g., Streamlit Cloud)
        if not db_url:
            try:
                import streamlit as st  # type: ignore
                secrets = getattr(st, "secrets", {})
                if secrets:
                    # direct URL keys
                    for key in ("DATABASE_URL", "POSTGRES_CONNECTION_STRING"):
                        if key in secrets:
                            db_url = secrets[key]
                            break
                    # nested dicts like [database] or [db]
                    if not db_url:
                        for section in ("database", "db"):
                            if section in secrets:
                                sec = secrets[section]
                                for key in ("url", "connection_string", "dsn"):
                                    if key in sec:
                                        db_url = sec[key]
                                        break
                                if db_url:
                                    break
                    # fallback discrete keys from secrets if no URL
                    if not db_url:
                        host = secrets.get("DB_HOST") or secrets.get("database_host")
                        name = secrets.get("DB_NAME") or secrets.get("database_name")
                        user = secrets.get("DB_USER") or secrets.get("database_user")
                        password = secrets.get("DB_PASSWORD") or secrets.get("database_password")
                        port = secrets.get("DB_PORT") or secrets.get("database_port")
                        sslmode = secrets.get("DB_SSLMODE") or "require"
                        if host and name and user and port:
                            db_url = f"postgresql+psycopg2://{user}:{password or ''}@{host}:{port}/{name}?sslmode={sslmode}"
            except Exception:
                # streamlit not installed or secrets not accessible; ignore
                pass

        if db_url:
            # Normalize scheme for SQLAlchemy + psycopg2
            if db_url.startswith("postgres://"):
                db_url = "postgresql+psycopg2://" + db_url[len("postgres://"):]
            elif db_url.startswith("postgresql://") and "+psycopg2" not in db_url:
                db_url = "postgresql+psycopg2://" + db_url[len("postgresql://"):]
        if not db_url:
            # Try loading .env files explicitly if variables aren't set yet
            try:
                from dotenv import load_dotenv  # type: ignore
                here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                root = os.path.abspath(os.path.join(here, os.pardir, os.pardir))
                prod = os.path.join(root, "env", "production.env")
                dev = os.path.join(root, "env", "development.env")
                # Load prod first, then dev as fallback
                if os.path.exists(prod):
                    load_dotenv(prod, override=False)
                if os.path.exists(dev):
                    load_dotenv(dev, override=False)
                # Re-check URL after loading
                db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_CONNECTION_STRING")
            except Exception:
                pass

        if not db_url:
            # Fallback to composing from discrete env vars, with safe defaults
            host = os.getenv("DB_HOST") or DB_HOST or "localhost"
            name = os.getenv("DB_NAME") or DB_NAME or "postgres"
            user = os.getenv("DB_USER") or DB_USER or "postgres"
            password = os.getenv("DB_PASSWORD") or DB_PASSWORD or ""
            port = os.getenv("DB_PORT") or DB_PORT or "5432"
            sslmode = os.getenv("DB_SSLMODE", "require")

            # Build URL, add sslmode if defined
            db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
            if sslmode:
                db_url += f"?sslmode={sslmode}"

            # If we still have a localhost default and no explicit host provided, fail fast
            if (host in (None, "", "localhost", "127.0.0.1") and
                not os.getenv("DATABASE_URL") and not os.getenv("POSTGRES_CONNECTION_STRING")):
                raise RuntimeError(
                    "Database configuration not found. Set DATABASE_URL or POSTGRES_CONNECTION_STRING, "
                    "or provide DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD via environment variables or Streamlit secrets."
                )

    # Create engine
        self._engine = create_engine(
            db_url,
            pool_pre_ping=True,  # Enable connection health checks
            pool_size=5,  # Set initial pool size
            max_overflow=10,  # Allow up to 10 connections beyond pool_size
        )
        
        # Create session factory
        self._SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine
        )

    def get_engine(self) -> Engine:
        """Get the SQLAlchemy engine instance.
        
        Returns:
            Engine: SQLAlchemy engine instance
        """
        if self._engine is None:
            raise RuntimeError("Database engine not initialized")
        return self._engine

    def get_session(self) -> Session:
        """Get a new database session.
        
        Returns:
            Session: New SQLAlchemy session
        
        Note:
            The session should be closed after use, preferably using a context manager
        """
        if self._SessionLocal is None:
            raise RuntimeError("Database session factory not initialized")
        return self._SessionLocal()

    def dispose(self):
        """Dispose of the current engine and all its database connections."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._SessionLocal = None
