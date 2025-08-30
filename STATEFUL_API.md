# Stateful CSV Analyzer Agent API

This document describes the stateful version of the CSV Analyzer Agent API, which now persists sessions and conversation history in MongoDB.

## Changes Made

### 1. Database Persistence
- **Before**: Sessions were stateless, recreated from CSV on each request
- **After**: Sessions are persisted in MongoDB with full conversation history

### 2. Session Management
- Sessions are created once and maintained across requests
- Conversation history is preserved between API calls
- CSV data is loaded once per session and cached

### 3. Database Connection
- MongoDB connection is established on API startup
- Connection is properly managed with startup/shutdown events
- Configuration is centralized in `config.py`

## Configuration

### Environment Variables
Create a `.env` file with the following variables:

```bash
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
# OR use individual components:
# MONGODB_HOST=localhost
# MONGODB_PORT=27017
# MONGODB_USERNAME=your_username
# MONGODB_PASSWORD=your_password
MONGODB_DATABASE=csv_analyzer

# Logging
LOG_LEVEL=INFO
```

### MongoDB Setup
1. Install MongoDB locally or use MongoDB Atlas
2. Ensure the database is accessible
3. The API will automatically create the `csv_analyzer` database and `sessions` collection

## API Endpoints

### Session Management

#### Create Session
```http
POST /session/create
Content-Type: application/json

{
  "csv_path": "path/to/your/file.csv",
  "session_id": "optional-custom-id"
}
```

#### List Sessions
```http
GET /sessions
```

#### Delete Session
```http
DELETE /session/{session_id}
```

#### Get Session History
```http
GET /session/{session_id}/history
```

### Query Processing

#### Process Query
```http
POST /query
Content-Type: application/json

{
  "query": "What is the average value in column X?",
  "session_id": "existing-session-id",
  "csv_path": "path/to/your/file.csv"
}
```

**Note**: If no `session_id` is provided, a new session will be created automatically.

## Session Lifecycle

1. **Creation**: Session is created with initial CSV data loaded
2. **Query Processing**: User queries are processed and responses are generated
3. **Persistence**: All messages and state changes are saved to MongoDB
4. **Retrieval**: Session state is retrieved from database on subsequent requests
5. **Cleanup**: Sessions can be explicitly deleted or will persist indefinitely

## Benefits of Stateful Mode

1. **Conversation Continuity**: Users can reference previous messages and context
2. **Performance**: CSV data is loaded once per session, not on every request
3. **Analytics**: Full conversation history is available for analysis
4. **User Experience**: Sessions can be resumed across different API calls
5. **Scalability**: Multiple users can have independent sessions

## Migration from Stateless Mode

If you were using the stateless version:

1. **Update your client code** to reuse session IDs
2. **Remove csv_path from subsequent requests** after session creation
3. **Handle session persistence** - sessions will now maintain state
4. **Consider session cleanup** for long-running applications

## Error Handling

The API now includes proper error handling for:
- Database connection failures
- Session not found errors
- MongoDB operation failures
- Configuration validation errors

## Monitoring

The API provides detailed logging for:
- Database connection status
- Session creation/deletion operations
- Query processing steps
- Error conditions

## Example Usage

### Python Client Example
```python
import requests

# Create a session
response = requests.post("http://localhost:8000/session/create", json={
    "csv_path": "data.csv"
})
session_id = response.json()["session_id"]

# Process queries in the same session
response = requests.post("http://localhost:8000/query", json={
    "query": "What columns are in this dataset?",
    "session_id": session_id
})

# Get conversation history
history = requests.get(f"http://localhost:8000/session/{session_id}/history")
print(history.json()["messages"])
```

### cURL Example
```bash
# Create session
SESSION_ID=$(curl -s -X POST "http://localhost:8000/session/create" \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "data.csv"}' | jq -r '.session_id')

# Process query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Show me the first 5 rows\", \"session_id\": \"$SESSION_ID\"}"

# Get history
curl "http://localhost:8000/session/$SESSION_ID/history"
```

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Check if MongoDB is running
   - Verify connection string in environment variables
   - Ensure network access to MongoDB instance

2. **Session Not Found**
   - Verify session ID is correct
   - Check if session was deleted
   - Ensure session exists in database

3. **Performance Issues**
   - Monitor MongoDB query performance
   - Consider adding database indexes
   - Check session cleanup policies

### Debug Mode
Set `LOG_LEVEL=DEBUG` in your environment to get detailed logging information.
