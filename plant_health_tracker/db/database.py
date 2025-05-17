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
        # Construct database URL
        db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
        
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
