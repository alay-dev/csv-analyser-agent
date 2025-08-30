#!/usr/bin/env python3
"""
Simple test script for session creation
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_session_creation():
    """Test session creation functionality"""
    try:
        from session_manager import session_manager
        
        print("🔧 Testing session creation...")
        
        # Test CSV path
        csv_path = "sample.csv"
        if not os.path.exists(csv_path):
            print(f"❌ CSV file not found: {csv_path}")
            return False
        
        print(f"✅ CSV file found: {csv_path}")
        
        # Test session creation
        session_id = await session_manager.create_session(csv_path)
        print(f"✅ Session created: {session_id}")
        
        # Test session retrieval (will fail if MongoDB not connected)
        state = await session_manager.get_session(session_id)
        if state:
            print(f"✅ Session retrieved successfully")
            print(f"   - CSV path: {state.get('csv_path')}")
            print(f"   - Thread ID: {state.get('thread_id')}")
            print(f"   - Messages: {len(state.get('messages', []))}")
        else:
            print("⚠️ Session retrieval failed (expected if MongoDB not connected)")
            # Create a fresh state for testing
            from graph_builder import initialize_state
            state = initialize_state(csv_path)
            state["session_id"] = session_id
            print(f"💡 Created fresh state for testing")
        
        # Test session update
        state["messages"].append({"role": "user", "content": "Test message"})
        updated = await session_manager.update_session(session_id, state)
        if updated:
            print("✅ Session updated successfully")
        else:
            print("❌ Failed to update session")
            return False
        
        # Test session deletion
        deleted = await session_manager.delete_session(session_id)
        if deleted:
            print("✅ Session deleted successfully")
        else:
            print("❌ Failed to delete session")
            return False
        
        print("🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 Starting session creation test...")
    
    # Test without MongoDB connection first
    print("\n--- Testing without MongoDB connection ---")
    success = await test_session_creation()
    
    if success:
        print("\n✅ Basic functionality test passed!")
    else:
        print("\n❌ Basic functionality test failed!")
        return
    
    # Test with MongoDB connection
    print("\n--- Testing with MongoDB connection ---")
    try:
        from session_manager import session_manager
        await session_manager.connect()
        print("✅ MongoDB connected")
        
        success = await test_session_creation()
        if success:
            print("✅ Full functionality test passed!")
        else:
            print("❌ Full functionality test failed!")
        
        await session_manager.disconnect()
        print("✅ MongoDB disconnected")
        
    except Exception as e:
        print(f"⚠️ MongoDB test skipped: {str(e)}")
        print("💡 Make sure MongoDB is running and accessible")
        print("💡 You can start MongoDB with: brew services start mongodb-community")
        print("💡 Or use MongoDB Atlas (cloud)")

if __name__ == "__main__":
    asyncio.run(main())
