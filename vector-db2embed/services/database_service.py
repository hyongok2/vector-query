"""Database service with clean interface"""
import pandas as pd
from sqlalchemy import create_engine, Engine
from typing import Optional
from abc import ABC, abstractmethod


class DatabaseInterface(ABC):
    """Abstract interface for database operations"""

    @abstractmethod
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query and return DataFrame"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test database connection"""
        pass


class SQLDatabaseService(DatabaseInterface):
    """SQL database service implementation"""

    def __init__(self, connection_uri: str):
        self.connection_uri = connection_uri
        self._engine: Optional[Engine] = None

    def _get_engine(self) -> Engine:
        """Get or create database engine"""
        if self._engine is None:
            self._engine = create_engine(self.connection_uri)
        return self._engine

    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query and return DataFrame"""
        try:
            engine = self._get_engine()
            return pd.read_sql(query, engine)
        except Exception as e:
            raise DatabaseConnectionError(f"Query execution failed: {e}")

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            engine = self._get_engine()
            with engine.connect():
                return True
        except Exception:
            return False

    def close(self):
        """Close database connection"""
        if self._engine:
            self._engine.dispose()
            self._engine = None


class DatabaseConnectionError(Exception):
    """Database connection error"""
    pass


class QueryValidator:
    """SQL query validation utilities"""

    @staticmethod
    def is_safe_query(query: str) -> bool:
        """Basic SQL injection protection"""
        query_lower = query.lower().strip()

        # Allow only SELECT statements
        if not query_lower.startswith('select'):
            return False

        # Block dangerous keywords
        dangerous_keywords = [
            'drop', 'delete', 'insert', 'update', 'alter',
            'create', 'truncate', 'exec', 'execute'
        ]

        for keyword in dangerous_keywords:
            if f' {keyword} ' in query_lower or query_lower.endswith(f' {keyword}'):
                return False

        return True

    @staticmethod
    def validate_query(query: str) -> str:
        """Validate and clean query"""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not QueryValidator.is_safe_query(query):
            raise ValueError("Only SELECT queries are allowed")

        return query.strip()


class DatabaseServiceFactory:
    """Factory for creating database services"""

    @staticmethod
    def create_service(connection_uri: str) -> DatabaseInterface:
        """Create database service from connection URI"""
        if not connection_uri:
            raise ValueError("Connection URI is required")

        return SQLDatabaseService(connection_uri)