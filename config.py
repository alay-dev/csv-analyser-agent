import os
from typing import Optional

class Config:
    """Configuration class for the CSV Analyzer Agent"""
    
    # MongoDB Configuration
    MONGODB_URL: Optional[str] = os.getenv("MONGODB_URL")
    MONGODB_HOST: str = os.getenv("MONGODB_HOST", "localhost")
    MONGODB_PORT: str = os.getenv("MONGODB_PORT", "27017")
    MONGODB_USERNAME: Optional[str] = os.getenv("MONGODB_USERNAME")
    MONGODB_PASSWORD: Optional[str] = os.getenv("MONGODB_PASSWORD")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "csv_analyzer")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def get_mongodb_url(cls) -> str:
        """Build MongoDB connection URL from components"""
        if cls.MONGODB_URL:
            return cls.MONGODB_URL
        
        if cls.MONGODB_USERNAME and cls.MONGODB_PASSWORD:
            return f"mongodb://{cls.MONGODB_USERNAME}:{cls.MONGODB_PASSWORD}@{cls.MONGODB_HOST}:{cls.MONGODB_PORT}"
        
        return f"mongodb://{cls.MONGODB_HOST}:{cls.MONGODB_PORT}"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present"""
        try:
            # Test MongoDB connection
            from motor.motor_asyncio import AsyncIOMotorClient
            client = AsyncIOMotorClient(cls.get_mongodb_url())
            return True
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False
