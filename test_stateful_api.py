#!/usr/bin/env python3
"""
Test script for the stateful CSV Analyzer Agent API
"""

import asyncio
import requests
import json
from typing import Dict, Any

class StatefulAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
    
    def test_connection(self) -> bool:
        """Test if the API is running"""
        try:
            response = requests.get(f"{self.base_url}/docs")
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def create_session(self, csv_path: str = "sample.csv") -> str:
        """Create a new session"""
        print(f"📝 Creating session with CSV: {csv_path}")
        
        response = requests.post(
            f"{self.base_url}/session/create",
            json={"csv_path": csv_path}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.session_id = data["session_id"]
            print(f"✅ Session created: {self.session_id}")
            return self.session_id
        else:
            print(f"❌ Failed to create session: {response.text}")
            return None
    
    def process_query(self, query: str, csv_path: str = None) -> Dict[str, Any]:
        """Process a query in the current session"""
        if not self.session_id:
            print("❌ No active session. Create one first.")
            return None
        
        print(f"🤖 Processing query: {query}")
        
        payload = {
            "query": query,
            "session_id": self.session_id
        }
        
        if csv_path:
            payload["csv_path"] = csv_path
        
        response = requests.post(
            f"{self.base_url}/query",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data['response'][:100]}...")
            print(f"📊 Response type: {data.get('type', 'TEXT')}")
            return data
        else:
            print(f"❌ Query failed: {response.text}")
            return None
    
    def get_session_history(self) -> Dict[str, Any]:
        """Get conversation history for the current session"""
        if not self.session_id:
            print("❌ No active session. Create one first.")
            return None
        
        print(f"📋 Getting session history for: {self.session_id}")
        
        response = requests.get(
            f"{self.base_url}/session/{self.session_id}/history"
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ History retrieved: {len(data['messages'])} messages")
            return data
        else:
            print(f"❌ Failed to get history: {response.text}")
            return None
    
    def list_sessions(self) -> Dict[str, Any]:
        """List all sessions"""
        print("📋 Listing all sessions")
        
        response = requests.get(f"{self.base_url}/sessions")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data['sessions'])} sessions")
            return data
        else:
            print(f"❌ Failed to list sessions: {response.text}")
            return None
    
    def delete_session(self) -> bool:
        """Delete the current session"""
        if not self.session_id:
            print("❌ No active session to delete.")
            return False
        
        print(f"🗑️ Deleting session: {self.session_id}")
        
        response = requests.delete(
            f"{self.base_url}/session/{self.session_id}"
        )
        
        if response.status_code == 200:
            print(f"✅ Session deleted: {self.session_id}")
            self.session_id = None
            return True
        else:
            print(f"❌ Failed to delete session: {response.text}")
            return False
    
    def run_demo(self):
        """Run a complete demo of the stateful API"""
        print("🚀 Starting Stateful API Demo")
        print("=" * 50)
        
        # Test connection
        if not self.test_connection():
            print("❌ API is not running. Please start the server first.")
            return
        
        print("✅ API connection successful")
        print()
        
        # Create session
        if not self.create_session():
            return
        
        print()
        
        # Process multiple queries to demonstrate statefulness
        queries = [
            "What columns are in this dataset?",
            "Show me the first 5 rows",
            "What is the data type of each column?",
            "Generate a summary of the numerical columns"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"--- Query {i} ---")
            self.process_query(query)
            print()
        
        # Get session history
        print("--- Session History ---")
        history = self.get_session_history()
        if history:
            print(f"Total messages: {len(history['messages'])}")
            for i, msg in enumerate(history['messages']):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:50]
                print(f"{i+1}. [{role}]: {content}...")
        
        print()
        
        # List all sessions
        print("--- All Sessions ---")
        self.list_sessions()
        
        print()
        
        # Clean up
        print("--- Cleanup ---")
        self.delete_session()
        
        print()
        print("🎉 Demo completed!")

def main():
    """Main function to run the demo"""
    tester = StatefulAPITester()
    tester.run_demo()

if __name__ == "__main__":
    main()
