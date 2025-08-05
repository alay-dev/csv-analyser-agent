# Logging Documentation

The CSV Analyzer application includes comprehensive logging to help you monitor MongoDB connections, session operations, and API requests.

## Log Levels

You can control the verbosity of logs by setting the `LOG_LEVEL` environment variable:

- **DEBUG**: Very detailed information, typically only of interest when diagnosing problems
- **INFO**: General information about what the program is doing (default)
- **WARNING**: Something unexpected happened, but the software is still working
- **ERROR**: A serious problem occurred, the software couldn't perform some function
- **CRITICAL**: A very serious error occurred, the program may be unable to continue

## Configuration

### Environment Variable
Set the log level in your `.env` file:
```env
LOG_LEVEL=INFO
```

### Available Levels
```env
LOG_LEVEL=DEBUG    # Most verbose
LOG_LEVEL=INFO     # Default - recommended for production
LOG_LEVEL=WARNING  # Only warnings and errors
LOG_LEVEL=ERROR    # Only errors and critical issues
LOG_LEVEL=CRITICAL # Only critical issues
```

## Log Categories

### 🔌 MongoDB Connection Logs
- Connection attempts and results
- Database and collection initialization
- Connection errors and timeouts
- Disconnection events

**Example logs:**
```
2024-01-01 12:00:00 - session_manager - INFO - 🔌 Attempting to connect to MongoDB...
2024-01-01 12:00:01 - session_manager - INFO - ✅ MongoDB ping successful
2024-01-01 12:00:01 - session_manager - INFO - 🎉 Successfully connected to MongoDB: csv_analyzer
```

### 📝 Session Management Logs
- Session creation, retrieval, updates, and deletion
- Session state serialization/deserialization
- Session operation results

**Example logs:**
```
2024-01-01 12:01:00 - session_manager - INFO - 📝 Creating new session with CSV: sample.csv
2024-01-01 12:01:00 - session_manager - INFO - 🆔 Generated new session ID: abc123...
2024-01-01 12:01:01 - session_manager - INFO - ✅ Session created successfully: abc123...
```

### 🤖 API Request Logs
- Incoming API requests
- Query processing steps
- Response generation
- Error handling

**Example logs:**
```
2024-01-01 12:02:00 - main - INFO - 🤖 Processing query: 'What are the top 5 sales...' for session: abc123...
2024-01-01 12:02:01 - main - INFO - 🔄 Processing query through graph...
2024-01-01 12:02:02 - main - INFO - ✅ Query processed successfully. Response type: TEXT
```

### 🚀 Application Lifecycle Logs
- Server startup and shutdown
- Database connection lifecycle
- Configuration information

**Example logs:**
```
2024-01-01 12:00:00 - main - INFO - 🚀 FastAPI server starting up...
2024-01-01 12:00:00 - main - INFO - 💡 MongoDB will connect on first database operation
```

## Log Symbols Reference

| Symbol | Meaning |
|--------|---------|
| 🔌 | Database connection operations |
| 📝 | Session creation/management |
| 🔍 | Data retrieval operations |
| 💾 | Data storage operations |
| 🤖 | API request processing |
| 🔄 | Processing/transformation |
| ✅ | Successful operations |
| ❌ | Failed operations |
| ⚠️ | Warnings |
| 🚀 | Application startup |
| 🛑 | Application shutdown |
| 🆔 | ID generation/management |
| 📊 | Data/statistics information |
| 🧹 | Cleanup operations |

## Debugging Common Issues

### MongoDB Connection Issues

**Set DEBUG level for detailed connection info:**
```env
LOG_LEVEL=DEBUG
```

**Look for these log patterns:**
```
❌ MongoDB connection timeout: ...
💡 Check if MongoDB server is running and accessible

🔌 MongoDB connection failed: ...
💡 Check MongoDB URL and credentials
```

### Session Issues

**Look for these log patterns:**
```
⚠️ Session not found: session_id
❌ Failed to create session: error_details
⚠️ No documents modified for session: session_id
```

### API Processing Issues

**Look for these log patterns:**
```
❌ Failed to initialize session: session_id
❌ Failed to process query: error_details
⚠️ No messages in updated state, returning default response
```

## Production Recommendations

### Log Level
Use `INFO` level for production to balance visibility and performance:
```env
LOG_LEVEL=INFO
```

### Log Monitoring
Monitor these critical log patterns in production:
- `❌` - All error messages
- `⚠️` - Warning messages that might indicate issues
- Connection timeout messages
- Session creation failures

### Log Rotation
Consider implementing log rotation for production deployments to manage log file sizes.

## Testing Logs

### Test MongoDB Connection
```bash
pipenv run python test_mongodb.py
```

This will show detailed connection logs and test all database operations.

### Test API with Logs
```bash
# Start server with DEBUG logging
LOG_LEVEL=DEBUG pipenv run uvicorn main:app --reload

# Make test requests and observe logs
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'
```

## Custom Logging

You can customize logging in your code:

```python
from logging_config import get_logger

logger = get_logger(__name__)

# Use the logger
logger.info("Custom log message")
logger.error("Custom error message")
```

## Troubleshooting

### No Logs Appearing
1. Check `LOG_LEVEL` environment variable
2. Ensure `.env` file is loaded
3. Verify logging configuration is imported

### Too Many Logs
1. Increase `LOG_LEVEL` to `WARNING` or `ERROR`
2. Check for infinite loops in your code
3. Consider log filtering

### Missing Connection Logs
1. Set `LOG_LEVEL=DEBUG`
2. Check MongoDB URL configuration
3. Verify network connectivity