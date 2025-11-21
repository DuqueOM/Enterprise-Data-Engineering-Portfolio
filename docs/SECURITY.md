# Security & Compliance Guide

## Overview

This document outlines security best practices, compliance considerations, and data protection strategies implemented across all portfolio projects.

---

## 🔒 Security Principles

### Core Security Tenets

1. **Defense in Depth**: Multiple layers of security controls
2. **Least Privilege**: Minimal permissions necessary
3. **Secure by Default**: Security enabled out-of-the-box
4. **Zero Trust**: Verify everything, trust nothing
5. **Fail Secure**: System fails to secure state

---

## 🛡️ Security Implementation

### 1. Secrets Management

#### ✅ Best Practices Implemented

**Environment Variables**
```bash
# .env file (NEVER commit to Git)
WANDB_API_KEY=your_api_key_here
SLACK_WEBHOOK=your_webhook_url
DATABASE_URL=postgresql://user:pass@localhost/db
```

**Loading Secrets**
```python
import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file

api_key = os.getenv('WANDB_API_KEY')
if not api_key:
    raise ValueError("WANDB_API_KEY not found in environment")
```

#### ❌ Common Mistakes to Avoid

```python
# ❌ NEVER hardcode secrets
API_KEY = "sk-1234567890abcdef"  # WRONG!

# ❌ NEVER log secrets
logger.info(f"Using API key: {api_key}")  # WRONG!

# ❌ NEVER commit .env files
# Always add to .gitignore
```

#### Tools Used

- **python-dotenv**: Load environment variables from .env files
- **GitHub Secrets**: Secure CI/CD variable storage
- **Kubernetes Secrets**: Encrypted secret storage in K8s

---

### 2. Data Protection

#### PII (Personally Identifiable Information) Handling

**PII Sanitization Implementation**
```python
"""
scripts/pii_sanitizer.py - Automated PII removal
"""
import re
from typing import Dict, List

PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
}

def sanitize_text(text: str) -> str:
    """Remove PII from text data."""
    for pii_type, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f'[{pii_type.upper()}_REDACTED]', text)
    return text
```

#### Data Encryption

- **At Rest**: AES-256 encryption for sensitive data
- **In Transit**: TLS 1.3 for all network communications
- **Database**: Field-level encryption for PII

#### Data Retention

```yaml
# data_retention_policy.yaml
retention_policies:
  raw_data:
    duration: 90_days
    encryption: required
  processed_data:
    duration: 365_days
    encryption: recommended
  models:
    duration: 730_days  # 2 years
    versioning: required
  logs:
    duration: 30_days
    archival: s3_glacier
```

---

### 3. API Security

#### Authentication & Authorization

**JWT Token Implementation**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

def verify_token(credentials = Depends(security)):
    """Verify JWT token."""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
```

#### Rate Limiting

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/query")
@limiter.limit("100/hour")  # 100 requests per hour
async def query_endpoint(request: Request, query: QueryInput):
    # Process query
    pass
```

#### Input Validation

```python
from pydantic import BaseModel, validator, constr
from typing import List

class QueryInput(BaseModel):
    """Validated query input."""
    question: constr(min_length=5, max_length=500)
    context: constr(max_length=1000) = ""
    max_results: int = 5
    
    @validator('max_results')
    def validate_max_results(cls, v):
        if not 1 <= v <= 20:
            raise ValueError('max_results must be between 1 and 20')
        return v
    
    @validator('question')
    def sanitize_question(cls, v):
        # Remove SQL injection attempts
        dangerous_patterns = ['--', ';', 'DROP', 'DELETE']
        if any(pattern in v.upper() for pattern in dangerous_patterns):
            raise ValueError('Invalid characters detected')
        return v
```

---

### 4. Container Security

#### Dockerfile Security Best Practices

```dockerfile
# Use specific version tags (not :latest)
FROM python:3.10.12-slim

# Run as non-root user
RUN useradd -m -u 1000 appuser

# Copy only necessary files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set working directory
WORKDIR /app
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Use ENTRYPOINT for immutability
ENTRYPOINT ["python", "app.py"]
```

#### Container Scanning

```bash
# Scan Docker images for vulnerabilities
trivy image my-app:latest

# Scan filesystem
trivy fs .

# Scan during CI/CD
docker scan my-app:latest
```

---

### 5. Dependency Security

#### Vulnerability Scanning

```bash
# Python dependencies
pip-audit

# Alternative: safety
safety check --json

# GitHub Actions
- name: Security Scan
  uses: pypa/gh-action-pip-audit@v1.0.0
```

#### Automated Updates

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## 🔍 Security Auditing

### Audit Logging

```python
import logging
import json
from datetime import datetime

class AuditLogger:
    """Structured audit logging."""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
        
    def log_event(
        self, 
        event_type: str, 
        user_id: str, 
        resource: str, 
        action: str,
        metadata: dict = None
    ):
        """Log security-relevant events."""
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'metadata': metadata or {},
            'ip_address': self._get_client_ip(),
        }
        self.logger.info(json.dumps(audit_entry))

# Usage
audit = AuditLogger()
audit.log_event(
    event_type='data_access',
    user_id='user123',
    resource='dataset_v2',
    action='read',
    metadata={'rows_accessed': 1000}
)
```

### What to Audit

- ✅ Authentication attempts (success/failure)
- ✅ Authorization decisions
- ✅ Data access (read/write/delete)
- ✅ Configuration changes
- ✅ Model deployments
- ✅ API calls with sensitive data
- ✅ Error conditions

---

## 🚨 Incident Response

### Incident Response Plan

1. **Detection**
   - Automated alerts (Prometheus, CloudWatch)
   - Log analysis (ELK stack)
   - User reports

2. **Containment**
   - Isolate affected systems
   - Revoke compromised credentials
   - Block malicious IPs

3. **Investigation**
   - Review audit logs
   - Identify root cause
   - Assess impact

4. **Remediation**
   - Patch vulnerabilities
   - Update dependencies
   - Implement fixes

5. **Recovery**
   - Restore from backups
   - Verify system integrity
   - Resume operations

6. **Post-Incident**
   - Document incident
   - Update runbooks
   - Improve detection

### Emergency Contacts

```
Security Team Lead: security@example.com
On-Call Engineer: +1-555-0100
Management: management@example.com
```

---

## 📋 Compliance

### Data Privacy Regulations

#### GDPR Compliance
- ✅ Right to access (data export)
- ✅ Right to erasure (data deletion)
- ✅ Data portability
- ✅ Consent management
- ✅ Breach notification (72 hours)

#### CCPA Compliance
- ✅ Consumer data requests
- ✅ Opt-out mechanisms
- ✅ Data sale disclosures

### Industry Standards

#### ISO 27001
- Information security management system
- Risk assessment procedures
- Security controls implementation

#### SOC 2
- Security
- Availability
- Processing integrity
- Confidentiality
- Privacy

---

## 🧪 Security Testing

### Automated Security Tests

```python
# tests/test_security.py
import pytest
from src.api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_sql_injection_prevention():
    """Test SQL injection protection."""
    malicious_input = "'; DROP TABLE users; --"
    response = client.post(
        "/api/v1/query",
        json={"question": malicious_input}
    )
    assert response.status_code == 422  # Validation error

def test_rate_limiting():
    """Test rate limiting enforcement."""
    for _ in range(101):  # Exceed limit
        response = client.post("/api/v1/query", json={"question": "test"})
    
    assert response.status_code == 429  # Too Many Requests

def test_xss_prevention():
    """Test XSS attack prevention."""
    xss_payload = "<script>alert('XSS')</script>"
    response = client.post(
        "/api/v1/query",
        json={"question": xss_payload}
    )
    # Should sanitize or reject
    assert '<script>' not in response.text
```

### Penetration Testing

```bash
# OWASP ZAP automated scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
    -t http://localhost:8000

# Nuclei vulnerability scanner
nuclei -u http://localhost:8000 -t vulnerabilities/
```

---

## 📚 Security Checklist

### Development Phase
- [ ] No hardcoded secrets
- [ ] Input validation on all endpoints
- [ ] PII sanitization implemented
- [ ] Secrets in environment variables
- [ ] Code reviewed for security issues

### Testing Phase
- [ ] Security tests passing
- [ ] Dependency vulnerability scan clean
- [ ] Container image scan clean
- [ ] Penetration testing completed

### Deployment Phase
- [ ] TLS/HTTPS enabled
- [ ] Rate limiting configured
- [ ] Monitoring and alerting active
- [ ] Backup and recovery tested
- [ ] Incident response plan updated

### Production Phase
- [ ] Regular security audits
- [ ] Dependency updates automated
- [ ] Access logs reviewed
- [ ] Security patches applied promptly

---

## 🔗 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Cloud Security Alliance](https://cloudsecurityalliance.org/)

---

**Document Version:** 1.0  
**Last Updated:** 2024-01-15  
**Review Schedule:** Quarterly  
**Owner:** Security Team
