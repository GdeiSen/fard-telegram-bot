import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text, event
from models.base import Base
from models.user import User
from models.user_auth import UserAuth, Session

class DatabaseManager:
    def __init__(self, db_url: str = None):
        # Get database URL from environment or use default
        self.db_url = db_url or os.environ.get('DATABASE_URL', 'sqlite+aiosqlite:///data.db')
        
        # Create engine
        self.engine = create_async_engine(
            self.db_url,
            echo=bool(os.environ.get('SQL_ECHO', 'False').lower() == 'true'),
            future=True,
            poolclass=NullPool if self.db_url.startswith('sqlite') else None,
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    def Session(self):
        """Return a database session"""
        return self.SessionLocal()
    
    async def initialize_db(self):
        """Initialize the database, creating tables if they don't exist"""
        async with self.engine.begin() as conn:
            # For SQLite: Enable foreign keys and configure for proper autoincrement
            if 'sqlite' in self.db_url:
                await conn.execute(text("PRAGMA foreign_keys=ON"))
            
            # Create tables
            await conn.run_sync(Base.metadata.create_all)
            
            # Check if we need to add indices
            await self._add_indices(conn)
            
    async def _add_indices(self, conn):
        """Add any necessary indices to the database tables"""
        # Session token index for fast lookups
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_sessions_token ON sessions (token)"
        ))
        
        # UserAuth user_id index
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_user_auth_user_id ON user_auth (user_id)"
        ))
    
    async def close(self):
        """Close the database connection"""
        await self.engine.dispose()