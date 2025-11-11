# ScreenSteps API Integration Guide - VLP2SS

This guide provides detailed information about integrating with the ScreenSteps API for uploading converted VLP content.

**Version:** 1.0.1  
**Author:** Burke Azbill  
**License:** MIT

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

## Overview

The ScreenSteps API v2 allows programmatic access to create and manage knowledge base content. This guide focuses on the endpoints used by the VLP to ScreenSteps converter.

### Base URL

```text
https://{account}.screenstepslive.com/api/v2
```

Replace `{account}` with your ScreenSteps account name.

### API Version

This guide covers **API v2**. For the latest API documentation, visit:
<https://help.screensteps.com/m/integration/c/301068>

## Authentication

### Generating an API Token

1. Log in to your ScreenSteps account
2. Navigate to **Account Settings** → **API Tokens**
3. Click **Generate New Token**
4. Provide a description (e.g., "VLP Converter")
5. Select **Full Access** permission
6. Click **Create Token**
7. Copy the token immediately (it won't be shown again)

### Using the API Token

The API uses HTTP Basic Authentication:

```text
Username: Your ScreenSteps user ID
Password: Your API token
```

**Current Issue**: Need secure authentication for API access

**Recommendation**: Use API tokens instead of passwords

**Benefit**:

- More secure than passwords
- Can be revoked without changing password
- Granular permission control
- Audit trail of API usage

**Example Usage**:

```bash
# Using curl
curl -u "admin:YOUR_API_TOKEN" \
  https://myaccount.screenstepslive.com/api/v2/sites

# Using Python requests
import requests
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth('admin', 'YOUR_API_TOKEN')
response = requests.get(
    'https://myaccount.screenstepslive.com/api/v2/sites',
    auth=auth
)
```

## API Endpoints

### 1. List Sites

Get all sites accessible to the authenticated user.

**Endpoint**: `GET /sites`

**Request**:

```bash
curl -u "admin:TOKEN" \
  https://myaccount.screenstepslive.com/api/v2/sites
```

**Response**:

```json
{
  "sites": [
    {
      "id": 12345,
      "title": "My Knowledge Base",
      "url": "https://myaccount.screenstepslive.com",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 2. Get Site Details

Get details about a specific site, including manuals.

**Endpoint**: `GET /sites/{site_id}`

**Request**:

```bash
curl -u "admin:TOKEN" \
  https://myaccount.screenstepslive.com/api/v2/sites/12345
```

**Response**:

```json
{
  "site": {
    "id": 12345,
    "title": "My Knowledge Base",
    "manuals": [
      {
        "id": 67890,
        "title": "User Guide",
        "chapters_count": 5
      }
    ]
  }
}
```

### 3. Create Manual

Create a new manual in a site.

**Endpoint**: `POST /sites/{site_id}/manuals`

**Request**:

```bash
curl -u "admin:TOKEN" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "manual": {
      "title": "HOL-2601-03-VCF-L",
      "description": "VMware Cloud Foundation Lab"
    }
  }' \
  https://myaccount.screenstepslive.com/api/v2/sites/12345/manuals
```

**Response**:

```json
{
  "manual": {
    "id": 67890,
    "title": "HOL-2601-03-VCF-L",
    "description": "VMware Cloud Foundation Lab",
    "created_at": "2025-01-03T14:30:00Z"
  }
}
```

### 4. Create Chapter

Create a new chapter in a manual.

**Endpoint**: `POST /sites/{site_id}/manuals/{manual_id}/chapters`

**Request**:

```bash
curl -u "admin:TOKEN" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "chapter": {
      "title": "Module 1 - Introduction",
      "description": "Introduction to Views and Dashboards"
    }
  }' \
  https://myaccount.screenstepslive.com/api/v2/sites/12345/manuals/67890/chapters
```

**Response**:

```json
{
  "chapter": {
    "id": 11111,
    "title": "Module 1 - Introduction",
    "description": "Introduction to Views and Dashboards",
    "manual_id": 67890
  }
}
```

### 5. Create Article

Create a new article in a chapter.

**Endpoint**: `POST /sites/{site_id}/chapters/{chapter_id}/articles`

**Request**:

```bash
curl -u "admin:TOKEN" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "article": {
      "title": "Key Concepts",
      "html_body": "<p>Views provide several types...</p>",
      "meta_title": "Key Concepts",
      "meta_description": "Learn about key concepts"
    }
  }' \
  https://myaccount.screenstepslive.com/api/v2/sites/12345/chapters/11111/articles
```

**Response**:

```json
{
  "article": {
    "id": 22222,
    "title": "Key Concepts",
    "html_body": "<p>Views provide several types...</p>",
    "chapter_id": 11111,
    "created_at": "2025-01-03T14:35:00Z"
  }
}
```

### 6. Upload Image

Upload an image to an article.

**Endpoint**: `POST /sites/{site_id}/articles/{article_id}/images`

**Request**:

```bash
curl -u "admin:TOKEN" \
  -X POST \
  -F "file=@image.png" \
  https://myaccount.screenstepslive.com/api/v2/sites/12345/articles/22222/images
```

**Response**:

```json
{
  "image": {
    "id": 33333,
    "url": "https://cdn.screenstepslive.com/images/original/image.png",
    "filename": "image.png",
    "content_type": "image/png"
  }
}
```

### 7. Update Article

Update an existing article's content.

**Endpoint**: `PUT /sites/{site_id}/articles/{article_id}`

**Request**:

```bash
curl -u "admin:TOKEN" \
  -X PUT \
  -H "Content-Type: application/json" \
  -d '{
    "article": {
      "html_body": "<p>Updated content with new image...</p>"
    }
  }' \
  https://myaccount.screenstepslive.com/api/v2/sites/12345/articles/22222
```

**Response**:

```json
{
  "article": {
    "id": 22222,
    "title": "Key Concepts",
    "html_body": "<p>Updated content with new image...</p>",
    "updated_at": "2025-01-03T14:40:00Z"
  }
}
```

## Usage Examples

### Example 1: Complete Upload Workflow

**Current Issue**: Need to upload converted content to ScreenSteps

**Recommendation**: Follow the complete workflow: create manual → chapters → articles → images

**Benefit**:

- Organized content structure
- Proper hierarchy
- All content uploaded correctly

**Example Usage**:

```python
import requests
from requests.auth import HTTPBasicAuth

# Configuration
account = "myaccount"
user = "admin"
token = "YOUR_API_TOKEN"
site_id = "12345"
base_url = f"https://{account}.screenstepslive.com/api/v2"
auth = HTTPBasicAuth(user, token)

# Step 1: Create Manual
manual_data = {
    "manual": {
        "title": "HOL-2601-03-VCF-L",
        "description": "VMware Cloud Foundation Lab"
    }
}
response = requests.post(
    f"{base_url}/sites/{site_id}/manuals",
    json=manual_data,
    auth=auth
)
manual = response.json()["manual"]
manual_id = manual["id"]

# Step 2: Create Chapter
chapter_data = {
    "chapter": {
        "title": "Module 1 - Introduction",
        "description": "Introduction to Views and Dashboards"
    }
}
response = requests.post(
    f"{base_url}/sites/{site_id}/manuals/{manual_id}/chapters",
    json=chapter_data,
    auth=auth
)
chapter = response.json()["chapter"]
chapter_id = chapter["id"]

# Step 3: Create Article
article_data = {
    "article": {
        "title": "Key Concepts",
        "html_body": "<p>Views provide several types...</p>",
        "meta_title": "Key Concepts",
        "meta_description": "Learn about key concepts"
    }
}
response = requests.post(
    f"{base_url}/sites/{site_id}/chapters/{chapter_id}/articles",
    json=article_data,
    auth=auth
)
article = response.json()["article"]
article_id = article["id"]

# Step 4: Upload Image
with open("image.png", "rb") as f:
    files = {"file": ("image.png", f, "image/png")}
    response = requests.post(
        f"{base_url}/sites/{site_id}/articles/{article_id}/images",
        files=files,
        auth=auth
    )
image = response.json()["image"]
image_url = image["url"]

print(f"Manual created: {manual_id}")
print(f"Chapter created: {chapter_id}")
print(f"Article created: {article_id}")
print(f"Image uploaded: {image_url}")
```

### Example 2: Using the Uploader Script

```bash
# Upload converted content
python3 screensteps_uploader.py \
    --content output/HOL-2601-03-VCF-L \
    --account myaccount \
    --user admin \
    --token YOUR_API_TOKEN \
    --site 12345 \
    --verbose
```

## Rate Limiting

ScreenSteps API implements rate limiting to prevent abuse.

### Rate Limit Headers

Response headers include:

- `X-RateLimit-Limit`: Maximum requests per time window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets (Unix timestamp)

### 429 Too Many Requests

When rate limit is exceeded, the API returns:

**Status**: `429 Too Many Requests`

**Response**:

```json
{
  "error": "Rate limit exceeded",
  "retry_in": 60
}
```

**Current Issue**: API rate limiting prevents rapid uploads

**Recommendation**: Implement automatic retry with exponential backoff

**Benefit**:

- Automatic handling of rate limits
- No manual intervention needed
- Reliable uploads

**Example Usage**:

```python
import time
import requests
from requests.auth import HTTPBasicAuth

def api_request_with_retry(method, url, auth, **kwargs):
    """Make API request with automatic retry on rate limit"""
    while True:
        response = requests.request(method, url, auth=auth, **kwargs)
        
        if response.status_code == 200:
            return response
        elif response.status_code == 429:
            # Rate limit exceeded
            try:
                retry_info = response.json()
                retry_in = retry_info.get('retry_in', 60)
            except:
                retry_in = 60
            
            print(f"Rate limit exceeded. Retrying in {retry_in} seconds...")
            time.sleep(retry_in)
        else:
            response.raise_for_status()

# Usage
auth = HTTPBasicAuth('admin', 'TOKEN')
response = api_request_with_retry(
    'POST',
    'https://myaccount.screenstepslive.com/api/v2/sites/12345/manuals',
    auth,
    json={'manual': {'title': 'Test'}}
)
```

## Error Handling

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "error": "Error message",
  "details": "Additional error details"
}
```

### Handling Errors

**Current Issue**: API errors can interrupt batch uploads

**Recommendation**: Implement comprehensive error handling

**Benefit**:

- Graceful failure handling
- Detailed error logging
- Partial success tracking

**Example Usage**:

```python
def safe_api_call(func, *args, **kwargs):
    """Wrapper for safe API calls with error handling"""
    try:
        return func(*args, **kwargs)
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return None
    except requests.exceptions.ConnectionError:
        print("Connection error. Check network connectivity.")
        return None
    except requests.exceptions.Timeout:
        print("Request timed out.")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Usage
result = safe_api_call(
    requests.post,
    url,
    json=data,
    auth=auth
)

if result:
    print("Success!")
else:
    print("Failed to create resource")
```

## Best Practices

### 1. Use API Tokens

- Never use passwords in scripts
- Generate dedicated tokens for automation
- Rotate tokens regularly
- Revoke unused tokens

### 2. Implement Rate Limiting

- Respect rate limits
- Implement automatic retry
- Add delays between requests
- Monitor rate limit headers

### 3. Error Handling

- Handle all HTTP status codes
- Log errors for debugging
- Implement retry logic
- Provide meaningful error messages

### 4. Data Validation

- Validate input before API calls
- Check required fields
- Sanitize HTML content
- Verify file formats

### 5. Security

- Store credentials securely
- Use environment variables
- Never commit tokens to version control
- Use HTTPS only

### 6. Testing

- Test with small datasets first
- Verify uploads in ScreenSteps UI
- Check image references
- Validate content formatting

### 7. Monitoring

- Log all API calls
- Track success/failure rates
- Monitor upload times
- Review error logs regularly

## Additional Resources

- [ScreenSteps API Documentation](https://help.screensteps.com/m/integration/c/301068)
- [ScreenSteps Python Library](https://help.screensteps.com/m/integration/l/1056481-python-command-line-exporter)
- [API Token Management](https://help.screensteps.com/m/integration/l/1056486-generating-a-screensteps-api-token)

## Support

For API-related issues:

1. Check the [ScreenSteps API documentation](https://help.screensteps.com/m/integration/c/301068)
2. Review error logs
3. Verify API token permissions
4. Contact ScreenSteps support: <support@screensteps.com>
