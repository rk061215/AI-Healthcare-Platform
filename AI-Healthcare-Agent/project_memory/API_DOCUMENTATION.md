# API Documentation

> Auto-documented API endpoints for the AI Healthcare Follow-up Assistant.
> Base URL: `/api/v1`

---

## Authentication

### POST /auth/register/patient

Register a new patient account.

**Authentication:** None

#### Request Body
```json
{
  "email": "patient@example.com",
  "password": "StrongPass1!",
  "confirm_password": "StrongPass1!",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "date_of_birth": "1990-01-15",
  "gender": "male",
  "terms_accepted": true
}
```

#### Validation Rules
| Field | Rules |
|-------|-------|
| email | Valid email format, unique |
| password | 8-128 chars, uppercase, lowercase, digit, special char |
| confirm_password | Must match password |
| full_name | 1-255 chars |
| phone | Optional, E.164 format (`^\+?[1-9]\d{1,14}$`) |
| date_of_birth | Optional, ISO format YYYY-MM-DD, must be past date |
| gender | Optional, one of: male, female, other, prefer_not_to_say |
| terms_accepted | Must be true |

#### Response — 201 Created
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid-string",
    "email": "patient@example.com",
    "full_name": "John Doe",
    "role": "patient",
    "phone": "+1234567890"
  }
}
```

#### Status Codes
| Code | Description |
|------|-------------|
| 201 | Patient registered successfully |
| 409 | Email already exists |
| 422 | Validation error (invalid fields, password mismatch, terms not accepted) |

---

### POST /auth/register/doctor

Register a new doctor account.

**Authentication:** None

#### Request Body
```json
{
  "email": "doctor@example.com",
  "password": "StrongPass1!",
  "confirm_password": "StrongPass1!",
  "full_name": "Dr. Jane Smith",
  "phone": "+1987654321",
  "license_number": "LIC-12345",
  "hospital_name": "City General Hospital",
  "specialization": "Cardiology",
  "years_of_experience": 12
}
```

#### Validation Rules
| Field | Rules |
|-------|-------|
| email | Valid email format, unique |
| password | 8-128 chars, uppercase, lowercase, digit, special char |
| confirm_password | Must match password |
| full_name | 1-255 chars |
| phone | Optional, E.164 format |
| license_number | Optional |
| hospital_name | Optional |
| specialization | Optional |
| years_of_experience | Optional, must be 0-70 |

#### Response — 201 Created
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid-string",
    "email": "doctor@example.com",
    "full_name": "Dr. Jane Smith",
    "role": "doctor",
    "phone": "+1987654321",
    "specialization": "Cardiology",
    "license_number": "LIC-12345",
    "hospital_name": "City General Hospital",
    "years_of_experience": 12
  }
}
```

#### Status Codes
| Code | Description |
|------|-------------|
| 201 | Doctor registered successfully |
| 409 | Email already exists |
| 422 | Validation error |

---

### POST /auth/login

Unified login for patients and doctors.

**Authentication:** None

#### Request Body
```json
{
  "email": "user@example.com",
  "password": "StrongPass1!",
  "role": "patient",
  "remember_me": false
}
```

#### Validation Rules
| Field | Rules |
|-------|-------|
| email | Valid email format |
| password | Required |
| role | Must be "patient" or "doctor" |
| remember_me | Boolean, defaults to false |

#### Response — 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "patient",
    "phone": "+1234567890"
  }
}
```

#### Status Codes
| Code | Description |
|------|-------------|
| 200 | Login successful |
| 401 | Invalid email or password / Account deactivated |
| 422 | Validation error |

**Note:** `remember_me=true` returns a refresh token valid for 30 days instead of 7.

---

### POST /auth/logout

Revoke a refresh token (server-side logout).

**Authentication:** None (but requires a valid refresh token in the body)

#### Request Body
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### Response — 204 No Content
No response body.

#### Status Codes
| Code | Description |
|------|-------------|
| 204 | Token revoked successfully |
| 401 | Invalid or expired refresh token / Token already revoked |
| 404 | Refresh token not found in database |

---

### POST /auth/refresh

Refresh access and refresh tokens (token rotation).

**Authentication:** None (uses the refresh token)

#### Request Body
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### Response — 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### Status Codes
| Code | Description |
|------|-------------|
| 200 | New token pair issued (old refresh token revoked) |
| 401 | Invalid, expired, or revoked refresh token |

**Security:** On every refresh, the old refresh token is revoked and a completely new pair is issued. If a revoked token is reused, the request is rejected.

---

### GET /auth/me

Get the currently authenticated user's profile.

**Authentication:** Bearer Token (Access Token)

#### Request Headers
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### Response — 200 OK (Patient)
```json
{
  "id": "uuid-string",
  "email": "patient@example.com",
  "full_name": "John Doe",
  "role": "patient",
  "phone": "+1234567890",
  "date_of_birth": "1990-01-15",
  "gender": "male",
  "is_active": true
}
```

#### Response — 200 OK (Doctor)
```json
{
  "id": "uuid-string",
  "email": "doctor@example.com",
  "full_name": "Dr. Jane Smith",
  "role": "doctor",
  "phone": "+1987654321",
  "specialization": "Cardiology",
  "license_number": "LIC-12345",
  "hospital_name": "City General Hospital",
  "years_of_experience": 12,
  "is_active": true
}
```

#### Status Codes
| Code | Description |
|------|-------------|
| 200 | User profile returned |
| 401 | Missing or invalid access token |
| 404 | User not found in database |

---

## Patients

### GET /patients/me

Get the current patient's full profile.

**Authentication:** Bearer Token (Patient role required)

#### Response — 200 OK
```json
{
  "id": "uuid-string",
  "email": "patient@example.com",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "date_of_birth": "1990-01-15",
  "gender": "male",
  "blood_group": null,
  "address": null,
  "emergency_contact": null,
  "emergency_phone": null,
  "is_active": true,
  "created_at": "2026-07-11T05:00:00Z"
}
```

### PATCH /patients/me

Update the current patient's profile.

**Authentication:** Bearer Token (Patient role required)

#### Request Body
```json
{
  "phone": "+1234567890",
  "blood_group": "A+",
  "address": "123 Main St",
  "emergency_contact": "Jane Doe",
  "emergency_phone": "+1234567891"
}
```

### GET /patients/me/doctors

Get the list of doctors assigned to the current patient.

**Authentication:** Bearer Token (Patient role required)

---

## Doctors

### GET /doctors/me

Get the current doctor's full profile.

**Authentication:** Bearer Token (Doctor role required)

### GET /doctors/me/patients

Get the list of patients assigned to the current doctor.

**Authentication:** Bearer Token (Doctor role required)

### POST /doctors/me/patients/{patient_id}/assign

Assign a patient to the current doctor.

**Authentication:** Bearer Token (Doctor role required)

---

## Health

### GET /health

Health check endpoint.

**Authentication:** None

#### Response
```json
{
  "status": "healthy",
  "service": "AI Healthcare Assistant API",
  "version": "0.1.0"
}
```

### GET /

API root information.

**Authentication:** None

#### Response
```json
{
  "message": "AI Healthcare Follow-up Assistant API",
  "docs": "/docs",
  "health": "/health"
}
```
