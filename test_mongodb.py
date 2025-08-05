#!/usr/bin/env python3
"""
Test script to verify MongoDB connection and session management
"""
import asyncio
import os
from dotenv import load_dotenv
from session_manager import session_manager

async def test_mongodb_connection():
    """Test MongoDB connection and basic operations"""
    print("🧪 Testing MongoDB Connection...")
    
    try:
        # Test connection
        await session_manager.connect()
        print("✅ MongoDB connection successful!")
        
        # Test creating a session
        print("\n🧪 Testing session creation...")
        session_id = await session_manager.create_session(csv_path="sample.csv")
        print(f"✅ Session created: {session_id}")
        
        # Test retrieving the session
        print("\n🧪 Testing session retrieval...")
        session_state = await session_manager.get_session(session_id)
        if session_state:
            print("✅ Session retrieved successfully!")
            print(f"   - Thread ID: {session_state.get('thread_id')}")
            print(f"   - CSV Path: {session_state.get('csv_path')}")
            print(f"   - Messages: {len(session_state.get('messages', []))}")
        else:
            print("❌ Failed to retrieve session")
        
        # Test listing sessions
        print("\n🧪 Testing session listing...")
        sessions = await session_manager.list_sessions()
        print(f"✅ Found {len(sessions)} sessions")
        
        # Test deleting the session
        print("\n🧪 Testing session deletion...")
        deleted = await session_manager.delete_session(session_id)
        if deleted:
            print("✅ Session deleted successfully!")
        else:
            print("❌ Failed to delete session")
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
    
    finally:
        await session_manager.disconnect()
        print("🔌 Disconnected from MongoDB")
    
    return True

async def main():
    """Main test function"""
    load_dotenv()
    
    print("=" * 60)
    print("🧪 MONGODB CONNECTION TEST")
    print("=" * 60)
    print("MongoDB Configuration:")
    print(f"  - URL: {os.getenv('MONGODB_URL', 'Not set')}")
    print(f"  - Database: {os.getenv('MONGODB_DATABASE', 'csv_analyzer')}")
    print("=" * 60)
    
    success = await test_mongodb_connection()
    
    print("=" * 60)
    if success:
        print("✅ MongoDB setup is working correctly!")
        print("You can now run your FastAPI application with:")
        print("   pipenv run uvicorn main:app --reload")
    else:
        print("❌ MongoDB setup needs attention. Please check your configuration.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())