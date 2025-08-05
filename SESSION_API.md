# Session-Based CSV Analyzer API

This API now supports session-based conversations, allowing multiple users to have separate conversations with the CSV analyzer.

## Setup

1. **MongoDB Setup**: You can use either a local MongoDB instance or a hosted MongoDB service (like MongoDB Atlas).

2. **Environment Variables**: Update your `.env` file with MongoDB configuration:

   **Option 1: Full Connection String (Recommended for hosted MongoDB)**
   ```
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/database_name?retryWrites=true&w=majority
   MONGODB_DATABASE=csv_analyzer
   ```

   **Option 2: Individual Components (For local or custom setup)**
   ```
   MONGODB_HOST=localhost
   MONGODB_PORT=27017
   MONGODB_USERNAME=your_username
   MONGODB_PASSWORD=your_password
   MONGODB_DATABASE=csv_analyzer
   ```

   **For local MongoDB without authentication:**
   ```
   MONGODB_HOST=localhost
   MONGODB_PORT=27017
   MONGODB_DATABASE=csv_analyzer
   ```

3. **Install Dependencies**: Run `pipenv install` to install the new MongoDB dependencies.

4. **Test Connection**: Run the test script to verify your MongoDB setup:
   ```bash
   pipenv run python test_mongodb.py
   ```

## API Endpoints

### 1. Create Session
**POST** `/session/create`

Create a new session for CSV analysis.

**Request Body:**
```json
{
  "csv_path": "sample.csv",  // optional, can be local file or HTTPS URL, defaults to "sample.csv"
  "session_id": "my-custom-id"  // optional, auto-generated if not provided
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "message": "Session created successfully"
}
```

### 2. Query with Session
**POST** `/query`

Send a query to analyze CSV data within a session context.

**Request Body:**
```json
{
  "query": "What are the top 5 sales by region?",
  "session_id": "uuid-string",  // optional, creates new session if not provided
  "csv_path": "sample.csv"  // optional, can be local file or HTTPS URL, used when creating new session
}
```

**Response:**
```json
{
  "response": "Based on the data analysis...",
  "type": "TEXT",  // or "CHART", "TABLE", etc.
  "session_id": "uuid-string"
}
```

### 3. Get Session History
**GET** `/session/{session_id}/history`

Retrieve the conversation history for a specific session.

**Response:**
```json
{
  "session_id": "uuid-string",
  "messages": [
    {
      "role": "user",
      "content": "What are the top 5 sales by region?"
    },
    {
      "role": "assistant",
      "content": "Based on the data analysis...",
      "additional_kwargs": {
        "type": "TEXT"
      }
    }
  ]
}
```

### 4. List Sessions
**GET** `/sessions`

List all existing sessions (for admin purposes).

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "uuid-string",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:30:00Z"
    }
  ]
}
```

### 5. Delete Session
**DELETE** `/session/{session_id}`

Delete a specific session and all its data.

**Response:**
```json
{
  "message": "Session deleted successfully"
}
```

## Usage Examples

### Example 1: Auto-create session with local file
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me the data summary",
    "csv_path": "sample.csv"
  }'
```

### Example 1b: Auto-create session with remote CSV
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me the data summary",
    "csv_path": "https://your-bucket.s3.amazonaws.com/data/sales.csv"
  }'
```

### Example 2: Use existing session with remote CSV
```bash
# First, create a session with remote CSV
curl -X POST "http://localhost:8000/session/create" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "https://storage.googleapis.com/your-bucket/data.csv"
  }'

# Then use the session_id in queries
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the trends in the data?",
    "session_id": "your-session-id-here"
  }'
```

### Example 3: Continue conversation
```bash
# Follow-up question in the same session
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Can you create a chart for that?",
    "session_id": "your-session-id-here"
  }'
```

## Features

- **Session Isolation**: Each session maintains its own conversation history and state
- **Auto-creation**: Sessions are automatically created if not provided
- **Persistent Storage**: All session data is stored in MongoDB
- **Multiple CSV Support**: Different sessions can analyze different CSV files
- **Conversation History**: Full conversation context is maintained per session
- **Session Management**: Create, list, and delete sessions as needed

## Migration from Previous Version

The API is backward compatible. If you don't provide a `session_id` in your `/query` requests, a new session will be automatically created for each request. To maintain conversation context, make sure to use the `session_id` returned in the response for subsequent queries.