from shared import State
import os
import pandas as pd
import requests
from urllib.parse import urlparse
from logging_config import get_logger

logger = get_logger(__name__)

def load_csv(state: State) -> State:
    logger.info("📂 Loading CSV...")
    csv_path = state.get("csv_path")
    
    if not csv_path:
        raise ValueError("CSV path not provided")
    
    # Check if it's a URL (starts with http:// or https://)
    if csv_path.startswith(('http://', 'https://')):
        logger.info(f"🌐 Loading CSV from remote URL: {csv_path}")
        df = load_csv_from_url(csv_path)
    else:
        logger.info(f"📁 Loading CSV from local file: {csv_path}")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Local CSV file not found: {csv_path}")
        df = pd.read_csv(csv_path)
    
    logger.info(f"✅ CSV loaded successfully. Shape: {df.shape}")
    logger.info(f"📊 Columns: {list(df.columns)}")
    
    state["dataframe"] = df
    return state

def load_csv_from_url(url: str) -> pd.DataFrame:
    """Load CSV from a remote URL with proper error handling"""
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid URL format: {url}")
        
        logger.info(f"🔗 Fetching CSV from: {parsed_url.netloc}")
        
        # Make request with timeout and proper headers
        headers = {
            'User-Agent': 'CSV-Analyzer-Agent/1.0',
            'Accept': 'text/csv,application/csv,text/plain,*/*',
            'Accept-Encoding': 'gzip, deflate'  # Accept compressed responses
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        logger.info(f"📄 Content-Type: {content_type}")
        
        # Read CSV from response content (automatically handles decompression)
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        
        logger.info(f"✅ Successfully loaded CSV from URL")
        return df
        
    except requests.exceptions.Timeout:
        logger.error(f"⏰ Timeout while fetching CSV from URL: {url}")
        raise TimeoutError(f"Timeout while fetching CSV from URL: {url}")
    except requests.exceptions.ConnectionError:
        logger.error(f"🔌 Connection error while fetching CSV from URL: {url}")
        raise ConnectionError(f"Connection error while fetching CSV from URL: {url}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"🚫 HTTP error {e.response.status_code} while fetching CSV: {url}")
        raise ValueError(f"HTTP error {e.response.status_code} while fetching CSV from URL: {url}")
    except pd.errors.EmptyDataError:
        logger.error(f"📭 Empty CSV file from URL: {url}")
        raise ValueError(f"Empty CSV file from URL: {url}")
    except pd.errors.ParserError as e:
        logger.error(f"📊 CSV parsing error from URL {url}: {str(e)}")
        raise ValueError(f"CSV parsing error from URL {url}: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error loading CSV from URL {url}: {str(e)}")
        raise ValueError(f"Failed to load CSV from URL {url}: {str(e)}")

def analyze_schema(state: State) -> State:
    df = state["dataframe"]
    schema = {
        "columns": list(df.columns),
        "dtypes": df.dtypes.apply(lambda x: str(x)).to_dict(),
        "sample": df.head(5).to_dict(orient="records")
    }
    state["schema"] = schema
    return state


def load_and_analyze_csv(state: State) -> State:
    state = load_csv(state)
    state = analyze_schema(state)
    return state