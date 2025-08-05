#!/usr/bin/env python3
"""
Test script to verify remote CSV loading functionality
"""
import asyncio
import os
from dotenv import load_dotenv
from nodes.load_csv import load_csv_from_url
from shared import State
from graph_builder import initialize_state
from logging_config import setup_logging, get_logger

# Set up logging
setup_logging(level="INFO", format_style="detailed")
logger = get_logger(__name__)

# Test URLs - publicly accessible CSV files
TEST_URLS = [
    # GitHub raw CSV file (usually reliable)
    "https://raw.githubusercontent.com/plotly/datasets/master/iris.csv",
    
    # Another GitHub CSV
    "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/tips.csv",
    
    # Add your own test URLs here
    # "https://your-bucket.s3.amazonaws.com/test.csv",
    # "https://storage.googleapis.com/your-bucket/test.csv",
]

def test_url_loading():
    """Test loading CSV from various URLs"""
    print("=" * 60)
    print("🧪 REMOTE CSV LOADING TEST")
    print("=" * 60)
    
    for i, url in enumerate(TEST_URLS, 1):
        print(f"\n🔗 Test {i}: {url}")
        print("-" * 40)
        
        try:
            # Test direct URL loading
            df = load_csv_from_url(url)
            
            print(f"✅ Successfully loaded CSV")
            print(f"📊 Shape: {df.shape}")
            print(f"📋 Columns: {list(df.columns)}")
            print(f"🔍 Sample data:")
            print(df.head(2).to_string())
            
        except Exception as e:
            print(f"❌ Failed to load CSV: {str(e)}")
            continue

def test_state_initialization():
    """Test state initialization with remote CSV"""
    print("\n" + "=" * 60)
    print("🧪 STATE INITIALIZATION TEST")
    print("=" * 60)
    
    # Use the first URL for state initialization test
    if TEST_URLS:
        test_url = TEST_URLS[0]
        print(f"\n🔗 Testing state initialization with: {test_url}")
        print("-" * 40)
        
        try:
            # Test state initialization
            state = initialize_state(csv_path=test_url)
            
            print(f"✅ State initialized successfully")
            print(f"🆔 Thread ID: {state.get('thread_id')}")
            print(f"📁 CSV Path: {state.get('csv_path')}")
            print(f"📊 DataFrame shape: {state.get('dataframe').shape if state.get('dataframe') is not None else 'None'}")
            print(f"📋 Schema columns: {state.get('schema', {}).get('columns', [])}")
            print(f"💬 Messages: {len(state.get('messages', []))}")
            
        except Exception as e:
            print(f"❌ Failed to initialize state: {str(e)}")

def test_invalid_urls():
    """Test error handling with invalid URLs"""
    print("\n" + "=" * 60)
    print("🧪 ERROR HANDLING TEST")
    print("=" * 60)
    
    invalid_urls = [
        "http://example.com/test.csv",  # HTTP instead of HTTPS
        "https://nonexistent-domain-12345.com/test.csv",  # Non-existent domain
        "https://httpstat.us/404",  # 404 error
        "https://httpstat.us/500",  # 500 error
        "not-a-url",  # Invalid URL format
    ]
    
    for i, url in enumerate(invalid_urls, 1):
        print(f"\n❌ Test {i}: {url}")
        print("-" * 40)
        
        try:
            df = load_csv_from_url(url)
            print(f"⚠️ Unexpectedly succeeded: {df.shape}")
        except Exception as e:
            print(f"✅ Correctly failed: {type(e).__name__}: {str(e)}")

def main():
    """Main test function"""
    load_dotenv()
    
    print("🌐 Remote CSV Loading Test Suite")
    print("This will test loading CSV files from remote HTTPS URLs")
    
    # Test URL loading
    test_url_loading()
    
    # Test state initialization
    test_state_initialization()
    
    # Test error handling
    test_invalid_urls()
    
    print("\n" + "=" * 60)
    print("✅ Remote CSV testing completed!")
    print("💡 You can now use HTTPS URLs in your API requests:")
    print("   - Session creation: POST /session/create")
    print("   - Direct queries: POST /query")
    print("=" * 60)

if __name__ == "__main__":
    main()