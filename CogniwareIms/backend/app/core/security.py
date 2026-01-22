# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Security utilities - JWT, password hashing, authentication
Industry-standard security implementation

UPDATED: Migrated from python-jose to PyJWT (security fix for CRITICAL CVE)
"""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Security Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


class SecurityManager:
    """Manages authentication and authorization."""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token.

        Args:
            data: Payload data to encode in token
            expires_delta: Token expiration time

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),
                "jti": secrets.token_hex(16),  # Unique token ID
            }
        )

        # PyJWT encode (same API as python-jose)
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # PyJWT decode (same API as python-jose)
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except InvalidTokenError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def create_api_key() -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for storage."""
        return pwd_context.hash(api_key)

    @staticmethod
    def verify_api_key(api_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash."""
        return pwd_context.verify(api_key, hashed_key)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict[str, Any]:
    """Dependency to get current authenticated user from JWT token.

    Usage:
        @app.get("/protected")
        def protected_route(user: Dict = Depends(get_current_user)):
            return {"user": user["email"]}
    """
    token = credentials.credentials
    payload = SecurityManager.verify_token(token)

    # Extract user info from payload
    email = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    return payload


def require_role(required_role: str):
    """Dependency factory for role-based access control.

    Usage:
        @app.get("/admin")
        def admin_route(user: Dict = Depends(require_role("Super Admin"))):
            return {"message": "Admin access granted"}
    """

    def role_checker(current_user: Dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role != required_role:
            raise HTTPException(status_code=403, detail=f"Access denied. Required role: {required_role}")
        return current_user

    return role_checker


# Password strength validation
def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets security requirements.

    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    # Optional: special characters
    # if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
    #     return False, "Password must contain at least one special character"

    return True, ""


# Security headers middleware
def get_security_headers() -> Dict[str, str]:
    """Get recommended security headers."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }


# Input sanitization
def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks.

    Args:
        text: Input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""

    # Limit length
    text = text[:max_length]

    # Remove potentially dangerous characters
    # (This is basic; consider using bleach or similar for HTML)
    dangerous_chars = ["<", ">", '"', "'", "&", "`"]
    for char in dangerous_chars:
        text = text.replace(char, "")

    return text.strip()


# Rate limiting helper
class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        self.requests = {}

    def is_allowed(self, identifier: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        """Check if request is allowed under rate limit.

        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if request is allowed, False otherwise
        """
        now = datetime.utcnow()

        if identifier not in self.requests:
            self.requests[identifier] = []

        # Clean old requests
        cutoff = now - timedelta(seconds=window_seconds)
        self.requests[identifier] = [req_time for req_time in self.requests[identifier] if req_time > cutoff]

        # Check limit
        if len(self.requests[identifier]) >= max_requests:
            return False

        # Add current request
        self.requests[identifier].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


# Audit logging
def log_security_event(
    event_type: str,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
):
    """Log security-related events for audit trail.

    Args:
        event_type: Type of event (login, logout, failed_auth, etc.)
        user_id: User identifier
        details: Additional event details
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "details": details or {},
    }

    # In production, this should write to a secure audit log
    logger.info(f"SECURITY_EVENT: {log_entry}")


# CSRF token generation (for forms)
def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, stored_token: str) -> bool:
    """Verify CSRF token."""
    return secrets.compare_digest(token, stored_token)
