
# FurrButler API Guide

## Authentication

All API endpoints require authentication except for registration and login.

### Base URL
- Development: `http://localhost:5000/api`
- Production: `https://furrbutler.replit.app/api`

### Authentication Header
```
Authorization: Bearer <access_token>
```

## Auth Endpoints

### POST /auth/register
Register a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "role": "pet_parent",
  "full_name": "John Doe",
  "phone": "+1234567890"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "pet_parent",
    "is_email_verified": false,
    "is_active": true,
    "full_name": "John Doe",
    "phone": "+1234567890",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

### POST /auth/login
Login user and get JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "pet_parent",
    "is_email_verified": false,
    "is_active": true,
    "full_name": "John Doe",
    "phone": "+1234567890"
  }
}
```

### GET /auth/me
Get current user profile (requires access token).

**Response (200):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "pet_parent",
    "is_email_verified": false,
    "is_active": true,
    "full_name": "John Doe",
    "phone": "+1234567890"
  }
}
```

### POST /auth/refresh
Refresh access token using refresh token.

**Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### POST /auth/logout
Logout and revoke token.

**Headers:**
```
Authorization: Bearer <access_token_or_refresh_token>
```

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

## User Roles

- `pet_parent`: Regular pet owners
- `vendor_groomer`: Grooming service providers
- `vendor_boarding`: Boarding service providers
- `vet`: Veterinarians
- `pharmacy`: Pet pharmacies
- `handler`: International transport handlers
- `isolation`: Isolation center staff
- `ngo`: NGO workers
- `gov_view`: Government officials (read-only)
- `admin`: System administrators

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message"
  }
}
```

### Common Error Codes

- `MISSING_TOKEN`: Authorization token required
- `INVALID_TOKEN`: Token is invalid or malformed
- `TOKEN_EXPIRED`: Token has expired
- `TOKEN_REVOKED`: Token has been revoked
- `INSUFFICIENT_PERMISSIONS`: User lacks required permissions
- `VALIDATION_ERROR`: Request validation failed
- `EMAIL_EXISTS`: Email already registered
- `INVALID_CREDENTIALS`: Invalid email or password

## Rate Limiting

- Registration: 5 requests per minute
- Login: 10 requests per minute
- Other endpoints: 100 requests per minute

## Token Expiration

- Access tokens: 15 minutes
- Refresh tokens: 7 days

Tokens are automatically refreshed by the client when they expire.
