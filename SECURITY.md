# Security Implementation Guide

## Overview
This document outlines the security measures implemented in the IIoT Predictive Maintenance Dashboard MVP.

## 🔐 Authentication & Authorization

### Authentication Method: **JWT with PostgreSQL**

Users authenticate using username/password credentials. The system uses JWT tokens for stateless authentication with user data persisted in PostgreSQL.

### Microservice Architecture
- **auth-service**: Dedicated microservice handling user management and authentication
- **ai-engine**: Validates JWT tokens but doesn't manage users
- **PostgreSQL**: Persistent storage for user accounts with bcrypt password hashing

### User Roles
1. **Admin** - Full access to all features
   - Manage equipment
   - View all data
   - Configure system
   - Manage maintenance tasks
   - User management (future)

2. **Operator** - Limited access
   - View dashboards
   - View maintenance tasks
   - Cannot modify equipment registry

### Authentication Flow

1. User enters username/password on login page
2. Frontend POSTs credentials to auth-service (`/auth/login`)
3. Auth-service verifies credentials against PostgreSQL database
4. Bcrypt verifies hashed password
5. JWT token issued with user info (username, role)
6. Token stored in browser localStorage
7. User redirected to dashboard
8. All API requests include `Authorization: Bearer <token>` header
9. AI-engine validates token signature for protected endpoints

### Default Accounts

```
Admin Account:
Username: admin
Password: admin123

Operator Account:
Username: operator
Password: operator123
```

⚠️ **CHANGE THESE IN PRODUCTION!**

### JWT Token Authentication
- **Token Type**: Bearer JWT (JSON Web Token)
- **Expiration**: 60 minutes
- **Algorithm**: HS256
- **Secret Key**: Set via `JWT_SECRET_KEY` environment variable (shared across services)

## 🛡️ Implemented Security Features

### 1. Password Hashing with Bcrypt
All passwords stored with bcrypt hashing:
```python
# Auth-service password storage
import bcrypt

def _hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )
```

### 2. PostgreSQL User Storage
User data persists in dedicated database:
```python
# SQLAlchemy User model
class User(Base):
    __tablename__ = "users"
    username = Column(String(50), primary_key=True)
    full_name = Column(String(100))
    email = Column(String(100), unique=True)
    hashed_password = Column(String(255))
    role = Column(String(20))
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### 3. API Authentication
All sensitive endpoints require authentication:
```python
# Protected endpoint example
@app.get("/api/equipment")
async def get_equipment(current_user: dict = Depends(get_current_user)):
    # Only authenticated users can access
    return equipment_list
```

### 4. Role-Based Access Control (RBAC)
Admin-only operations:
```python
@app.post("/api/equipment")
async def add_equipment(
    equipment: dict,
    current_user: dict = Depends(get_current_active_admin)
):
    # Only admins can add equipment
    pass
```

### 4. Password Hashing (Local Accounts Only)
- **Algorithm**: bcrypt
- **Cost Factor**: 12 (default)
- Passwords never stored in plain text
- **Note**: Google OAuth users don't have passwords

### 5. CORS Protection
Limited to localhost for MVP:
```python
allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]
```

### 6. MQTT Security
For MVP (local network):
- **Authentication**: Anonymous (local network only)
- **Encryption**: None (local WiFi)

## 🔧 Configuration

### Environment Variables
Create `.env` file in project root:

```bash
# Security
JWT_SECRET_KEY=your-super-secret-key-min-32-chars-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
INFLUX_HOST=influxdb
INFLUX_PORT=8086
INFLUX_DB=factory_data

# MQTT
MQTT_BROKER=mosquitto
MQTT_PORT=1883
```

### Generate Secure Secret Key
```python
import secrets
print(secrets.token_urlsafe(32))
# Use this as JWT_SECRET_KEY
```

## 🚀 Usage

### Login (Get Token)
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "username": "admin",
    "full_name": "System Administrator",
    "email": "admin@iiot.local",
    "role": "admin"
  }
}
```

### Authenticated Request
```bash
curl -X GET http://localhost:8000/api/equipment \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### Get Current User Info
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📱 Frontend Integration

### Store Token
```typescript
// After login
const response = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password })
});

const data = await response.json();
localStorage.setItem('token', data.access_token);
localStorage.setItem('user', JSON.stringify(data.user));
```

### Authenticated Requests
```typescript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:8000/api/equipment', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### Logout
```typescript
localStorage.removeItem('token');
localStorage.removeItem('user');
// Redirect to login page
```

## 🔒 Production Security Checklist

### Before Deployment:

- [ ] Change default passwords
  ```python
  # In services/ai-engine/src/auth.py
  users_db = {
      "admin": {
          "hashed_password": pwd_context.hash("YOUR_STRONG_PASSWORD")
      }
  }
  ```

- [ ] Set strong JWT secret key
  ```bash
  JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
  ```

- [ ] Enable HTTPS/TLS
  - Use reverse proxy (Nginx/Caddy)
  - Get SSL certificate (Let's Encrypt)
  - Force HTTPS redirect

- [ ] Update CORS origins
  ```python
  allow_origins=[
      "https://yourdomain.com",
      "https://www.yourdomain.com"
  ]
  ```

- [ ] Enable MQTT authentication
  ```conf
  # mosquitto.conf
  allow_anonymous false
  password_file /mosquitto/config/passwd
  ```

- [ ] Add rate limiting
  ```python
  from slowapi import Limiter
  limiter = Limiter(key_func=get_remote_address)
  
  @app.post("/api/auth/login")
  @limiter.limit("5/minute")  # Max 5 login attempts per minute
  async def login(...):
      pass
  ```

- [ ] Implement database for users (replace in-memory dict)
  - PostgreSQL
  - MongoDB
  - SQLite (minimum)

- [ ] Add logging & monitoring
  ```python
  import logging
  logging.basicConfig(level=logging.INFO)
  logger = logging.getLogger(__name__)
  
  @app.post("/api/auth/login")
  async def login(...):
      logger.info(f"Login attempt: {username}")
  ```

- [ ] Enable audit trail
  - Log all admin actions
  - Track equipment changes
  - Monitor failed login attempts

- [ ] Add session management
  - Token refresh mechanism
  - Token revocation list
  - Multi-device session management

- [ ] Implement input validation
  ```python
  from pydantic import BaseModel, Field, validator
  
  class EquipmentCreate(BaseModel):
      id: str = Field(..., regex=r'^[A-Z0-9_]{3,20}$')
      name: str = Field(..., min_length=3, max_length=100)
  ```

- [ ] Add security headers
  ```python
  from fastapi.middleware.trustedhost import TrustedHostMiddleware
  
  app.add_middleware(
      TrustedHostMiddleware,
      allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
  )
  ```

## 🛡️ Network Security

### Firewall Rules (Production)
```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 1883/tcp  # MQTT (if external)
sudo ufw enable
```

### Docker Network Isolation
```yaml
# docker-compose.yml
networks:
  backend:
    internal: true  # No external access
  frontend:
    # Internet-facing

services:
  influxdb:
    networks:
      - backend  # Isolated from internet
  
  web-frontend:
    networks:
      - frontend
      - backend
```

## 📊 Security Monitoring

### Check for Vulnerabilities
```bash
# Python dependencies
pip install safety
safety check --json

# Docker images
docker scan iiot-predictive-maintenance-ai-engine
```

### Monitor Logs
```bash
# Failed login attempts
docker logs iiot_ai_engine | grep "Login attempt"

# Unauthorized access
docker logs iiot_ai_engine | grep "401\|403"

# System errors
docker logs iiot_ai_engine | grep "ERROR"
```

## 🚨 Incident Response

### Suspected Breach
1. **Immediately change JWT secret key**
   - All existing tokens will be invalidated
   - Users must re-login

2. **Review logs**
   ```bash
   docker logs iiot_ai_engine > security_audit.log
   ```

3. **Check for unauthorized equipment**
   ```bash
   curl http://localhost:8000/api/equipment
   ```

4. **Rotate all credentials**
   - Database passwords
   - MQTT credentials
   - API keys

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Docker Security](https://docs.docker.com/engine/security/)

## 📞 Support

For security concerns or vulnerabilities:
- Email: security@iiot.local
- Create private GitHub issue
- Report via security.txt

---

**Remember**: Security is a process, not a product. Regularly review and update security measures!
