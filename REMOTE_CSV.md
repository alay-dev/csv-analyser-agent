# Remote CSV Support

The CSV Analyzer now supports loading CSV files from remote HTTPS URLs, including cloud storage services like AWS S3, Google Cloud Storage, Azure Blob Storage, and other web-accessible CSV files.

## Supported URL Types

### ✅ Supported
- **HTTPS URLs**: `https://example.com/data.csv`
- **AWS S3**: `https://bucket-name.s3.amazonaws.com/path/to/file.csv`
- **Google Cloud Storage**: `https://storage.googleapis.com/bucket-name/path/to/file.csv`
- **Azure Blob Storage**: `https://account.blob.core.windows.net/container/file.csv`
- **GitHub Raw Files**: `https://raw.githubusercontent.com/user/repo/branch/file.csv`
- **Any public HTTPS endpoint** serving CSV content

### ❌ Not Supported
- **HTTP URLs** (only HTTPS for security)
- **FTP/SFTP URLs**
- **Private URLs requiring authentication** (OAuth, API keys, etc.)
- **URLs behind authentication walls**

## Usage Examples

### 1. Create Session with Remote CSV
```bash
curl -X POST "http://localhost:8000/session/create" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "https://your-bucket.s3.amazonaws.com/sales-data.csv"
  }'
```

### 2. Query with Remote CSV (Auto-create Session)
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the top 10 sales records?",
    "csv_path": "https://storage.googleapis.com/my-bucket/data.csv"
  }'
```

### 3. Different Cloud Storage Examples

#### AWS S3
```json
{
  "csv_path": "https://my-data-bucket.s3.us-west-2.amazonaws.com/datasets/sales.csv"
}
```

#### Google Cloud Storage
```json
{
  "csv_path": "https://storage.googleapis.com/my-project-bucket/analytics/user-data.csv"
}
```

#### Azure Blob Storage
```json
{
  "csv_path": "https://mystorageaccount.blob.core.windows.net/data/financial-records.csv"
}
```

#### GitHub Raw Files
```json
{
  "csv_path": "https://raw.githubusercontent.com/username/repository/main/data/sample.csv"
}
```

## Cloud Storage Setup

### AWS S3 Public Access
To make your S3 CSV file publicly accessible:

1. **Upload your CSV file to S3**
2. **Set public read permissions**:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "PublicReadGetObject",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::your-bucket-name/*"
       }
     ]
   }
   ```
3. **Use the public URL**: `https://your-bucket.s3.region.amazonaws.com/file.csv`

### Google Cloud Storage Public Access
1. **Upload your CSV file**
2. **Make it publicly readable**:
   ```bash
   gsutil acl ch -u AllUsers:R gs://your-bucket/your-file.csv
   ```
3. **Use the public URL**: `https://storage.googleapis.com/your-bucket/your-file.csv`

### Azure Blob Storage Public Access
1. **Upload your CSV file**
2. **Set container to public blob access**
3. **Use the public URL**: `https://account.blob.core.windows.net/container/file.csv`

## Error Handling

The system provides detailed error messages for common issues:

### Connection Errors
```
❌ Connection error while fetching CSV from URL: https://example.com/data.csv
```
**Solution**: Check if the URL is accessible and the server is responding.

### HTTP Errors
```
❌ HTTP error 404 while fetching CSV: https://example.com/data.csv
```
**Solution**: Verify the URL is correct and the file exists.

### Timeout Errors
```
❌ Timeout while fetching CSV from URL: https://example.com/data.csv
```
**Solution**: The server is taking too long to respond (>30 seconds). Try again or check server performance.

### Parsing Errors
```
❌ CSV parsing error from URL: Invalid CSV format
```
**Solution**: Ensure the file is a valid CSV format with proper headers and data structure.

### Empty File Errors
```
❌ Empty CSV file from URL: https://example.com/data.csv
```
**Solution**: Check that the CSV file contains data.

## Performance Considerations

### File Size Limits
- **Recommended**: < 100MB for optimal performance
- **Maximum**: Limited by available memory and timeout settings
- **Large files**: May take longer to download and process

### Timeout Settings
- **Connection timeout**: 30 seconds
- **Read timeout**: 30 seconds
- **Total processing time**: Depends on file size and complexity

### Caching
- Remote CSV files are **not cached** by default
- Each session creation downloads the file fresh
- Consider using local caching for frequently accessed files

## Security Considerations

### HTTPS Only
- Only HTTPS URLs are supported for security
- HTTP URLs will be rejected

### No Authentication
- The system doesn't support authenticated URLs
- Files must be publicly accessible
- Don't use URLs that require API keys, tokens, or login

### Content Validation
- Files are validated as proper CSV format
- Malicious content is not specifically filtered
- Only use trusted data sources

## Logging and Monitoring

The system provides detailed logs for remote CSV operations:

```
📂 Loading CSV...
🌐 Loading CSV from remote URL: https://example.com/data.csv
🔗 Fetching CSV from: example.com
📄 Content-Type: text/csv
✅ Successfully loaded CSV from URL
✅ CSV loaded successfully. Shape: (1000, 15)
📊 Columns: ['id', 'name', 'sales', 'region', ...]
```

### Debug Mode
Enable debug logging to see detailed HTTP request information:
```bash
LOG_LEVEL=DEBUG pipenv run uvicorn main:app --reload
```

## Best Practices

### 1. URL Validation
Always test your URLs in a browser first to ensure they're accessible.

### 2. File Format
Ensure your CSV files have:
- Proper headers in the first row
- Consistent column structure
- UTF-8 encoding
- Standard CSV format (comma-separated)

### 3. Performance
- Keep files under 100MB when possible
- Use compressed CSV files if supported by your storage service
- Consider data pagination for very large datasets

### 4. Reliability
- Use reliable cloud storage services
- Implement retry logic in your client applications
- Monitor for URL changes or expiration

### 5. Security
- Only use HTTPS URLs
- Don't include sensitive data in public URLs
- Regularly audit public file access

## Troubleshooting

### Common Issues

1. **"Invalid URL format"**
   - Check URL syntax
   - Ensure it starts with `https://`
   - Verify no special characters are unencoded

2. **"Connection timeout"**
   - Check internet connectivity
   - Verify the server is responding
   - Try the URL in a browser

3. **"HTTP 403 Forbidden"**
   - File may not be publicly accessible
   - Check bucket/container permissions
   - Verify CORS settings if applicable

4. **"CSV parsing error"**
   - Ensure file is valid CSV format
   - Check for proper encoding (UTF-8)
   - Verify column headers exist

### Testing Remote URLs

Use the test script to verify remote CSV loading:

```bash
# Test with a remote URL
pipenv run python -c "
from nodes.load_csv import load_csv_from_url
df = load_csv_from_url('https://your-url.com/data.csv')
print(f'Loaded CSV: {df.shape}')
print(f'Columns: {list(df.columns)}')
"
```

## Migration from Local Files

If you're migrating from local CSV files to remote URLs:

1. **Upload your CSV files** to your preferred cloud storage
2. **Set appropriate public permissions**
3. **Update your API calls** to use the new HTTPS URLs
4. **Test thoroughly** with your specific use cases
5. **Monitor performance** and adjust as needed

The API remains fully backward compatible - you can still use local file paths alongside remote URLs.