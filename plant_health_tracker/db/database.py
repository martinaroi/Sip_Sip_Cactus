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
        # Prefer full connection string from env if provided
        db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_CONNECTION_STRING")

        if db_url:
            # Normalize scheme for SQLAlchemy + psycopg2
            if db_url.startswith("postgres://"):
                db_url = "postgresql+psycopg2://" + db_url[len("postgres://"):]
            elif db_url.startswith("postgresql://") and "+psycopg2" not in db_url:
                db_url = "postgresql+psycopg2://" + db_url[len("postgresql://"):]
        else:
            # Fallback to composing from discrete env vars, with safe defaults
            host = DB_HOST or "localhost"
            name = DB_NAME or "postgres"
            user = DB_USER or "postgres"
            password = DB_PASSWORD or ""
            port = DB_PORT or "5432"
            sslmode = os.getenv("DB_SSLMODE", "require")

            # Build URL, add sslmode if defined
            db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
            if sslmode:
                db_url += f"?sslmode={sslmode}"

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
