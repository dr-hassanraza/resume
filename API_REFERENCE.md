# Resume Optimizer Chatbot - API Reference

## Authentication

All API endpoints require authentication using JWT tokens (except registration and login).

**Header Format:**
```
Authorization: Bearer <your_jwt_token>
```

## Base URL
```
http://localhost:8080/api/v1
```

---

## Authentication Endpoints

### POST `/auth/register`
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "secure_password",
  "full_name": "Full Name (optional)"
}
```

**Response:**
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "user_id": 1,
  "subscription_tier": "free"
}
```

### POST `/auth/login`
Authenticate user and get access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

### GET `/auth/me`
Get current user information.

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "subscription_tier": "free",
  "is_active": true
}
```

---

## Resume Management

### POST `/resumes/upload`
Upload and process a resume file.

**Request:** `multipart/form-data`
- `file`: PDF file
- `title`: Resume title

**Response:**
```json
{
  "id": 1,
  "title": "My Resume",
  "ats_score": 75.5,
  "industry": "technology",
  "experience_level": "mid",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### GET `/resumes/`
List all user resumes.

### GET `/resumes/{resume_id}`
Get specific resume details.

### POST `/resumes/optimize`
Generate optimization suggestions.

**Request Body:**
```json
{
  "resume_id": 1,
  "optimization_type": "ATS Keyword Optimizer",
  "job_title": "Software Engineer",
  "job_description": "Job description text..."
}
```

### POST `/resumes/{resume_id}/score`
Calculate ATS compatibility score.

**Request Body:**
```json
{
  "job_description": "Job description text..."
}
```

**Response:**
```json
{
  "overall_score": 85,
  "keyword_match": 80,
  "formatting_score": 90,
  "section_completeness": 85,
  "readability": 88,
  "issues": ["Missing specific keywords"],
  "recommendations": ["Add Python and React keywords"]
}
```

---

## Chat System

### POST `/chat/sessions`
Create a new chat session.

**Request Body:**
```json
{
  "resume_id": 1
}
```

### GET `/chat/sessions`
List user chat sessions.

### GET `/chat/sessions/{session_id}/messages`
Get messages for a chat session.

### WebSocket `/chat/ws/{session_id}`
Real-time chat communication.

**Message Types:**
- `chat`: Regular conversation
- `resume_upload`: Resume upload notification
- `optimization_request`: Request optimization

**Example WebSocket Message:**
```json
{
  "type": "chat",
  "message": "How can I improve my resume?",
  "timestamp": 1640995200000
}
```

---

## Analytics

### GET `/analytics/user`
Get user analytics overview.

**Response:**
```json
{
  "total_resumes": 5,
  "total_optimizations": 12,
  "total_chat_sessions": 8,
  "subscription_tier": "pro",
  "optimizations_this_month": 3,
  "optimizations_limit": 1000,
  "most_used_optimization": "ATS Keyword Optimizer",
  "average_ats_score": 78.5,
  "score_improvement": 12.3
}
```

### GET `/analytics/usage?timeframe=30d`
Get usage statistics.

**Query Parameters:**
- `timeframe`: `7d`, `30d`, `90d`, `1y`

### GET `/analytics/resumes`
Get resume statistics.

### GET `/analytics/optimizations`
Get optimization statistics.

---

## Enterprise Features

### GET `/enterprise/config`
Get enterprise configuration (enterprise tier only).

### PUT `/enterprise/config`
Update enterprise configuration.

### GET `/enterprise/api-key`
Get enterprise API key.

### POST `/enterprise/api-key/regenerate`
Regenerate enterprise API key.

### GET `/enterprise/metrics?timeframe=30d`
Get enterprise-wide metrics.

### GET `/enterprise/export?format=json`
Export enterprise data.

**Query Parameters:**
- `format`: `json` or `csv`

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message description"
}
```

**Common HTTP Status Codes:**
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `429`: Rate Limit Exceeded
- `500`: Internal Server Error

---

## Rate Limiting

**Free Tier:**
- 100 requests per hour
- 3 optimizations per month

**Pro Tier:**
- 1000 requests per hour
- 1000 optimizations per month

**Enterprise Tier:**
- Unlimited requests
- Unlimited optimizations

---

## WebSocket Events

### Client to Server

**Chat Message:**
```json
{
  "type": "chat",
  "message": "Your message here"
}
```

**Resume Upload:**
```json
{
  "type": "resume_upload",
  "resume_data": {
    "content": "resume text",
    "title": "resume title"
  }
}
```

**Optimization Request:**
```json
{
  "type": "optimization_request",
  "optimization_type": "ATS Keyword Optimizer",
  "job_title": "Software Engineer",
  "job_description": "Job description..."
}
```

### Server to Client

**Assistant Response:**
```json
{
  "type": "assistant",
  "message": "AI response here",
  "timestamp": 1640995200000
}
```

**Processing Status:**
```json
{
  "type": "processing",
  "message": "Analyzing your resume...",
  "timestamp": 1640995200000
}
```

**Optimization Result:**
```json
{
  "type": "optimization_result",
  "message": "## Optimization Results\n\n...",
  "optimization_type": "ATS Keyword Optimizer",
  "timestamp": 1640995200000
}
```

---

## SDKs and Integration

### Python SDK Example

```python
import requests

class ResumeOptimizerClient:
    def __init__(self, api_key, base_url="http://localhost:8080/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def upload_resume(self, file_path, title):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'title': title}
            response = requests.post(
                f"{self.base_url}/resumes/upload",
                files=files,
                data=data,
                headers=self.headers
            )
        return response.json()
    
    def optimize_resume(self, resume_id, optimization_type, job_description=""):
        data = {
            "resume_id": resume_id,
            "optimization_type": optimization_type,
            "job_description": job_description
        }
        response = requests.post(
            f"{self.base_url}/resumes/optimize",
            json=data,
            headers=self.headers
        )
        return response.json()

# Usage
client = ResumeOptimizerClient("your_api_key")
resume = client.upload_resume("resume.pdf", "My Resume")
optimization = client.optimize_resume(resume["id"], "ATS Keyword Optimizer")
```

### JavaScript SDK Example

```javascript
class ResumeOptimizerClient {
  constructor(apiKey, baseUrl = 'http://localhost:8080/api/v1') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    };
  }

  async uploadResume(file, title) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);

    const response = await fetch(`${this.baseUrl}/resumes/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.apiKey}` },
      body: formData
    });

    return response.json();
  }

  async optimizeResume(resumeId, optimizationType, jobDescription = '') {
    const response = await fetch(`${this.baseUrl}/resumes/optimize`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        resume_id: resumeId,
        optimization_type: optimizationType,
        job_description: jobDescription
      })
    });

    return response.json();
  }
}

// Usage
const client = new ResumeOptimizerClient('your_api_key');
const resume = await client.uploadResume(fileInput.files[0], 'My Resume');
const optimization = await client.optimizeResume(resume.id, 'ATS Keyword Optimizer');
```