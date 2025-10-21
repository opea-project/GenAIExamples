"""
Cogniware Core - Authentication Middleware
Protect all API endpoints with licensing validation
"""

import time
from functools import wraps
from flask import request, jsonify
from licensing_service import license_manager

def validate_request():
    """
    Validate API request with license checking
    Returns tuple: (valid: bool, user_info: dict, error: dict)
    """
    # Get API key from header
    api_key = request.headers.get('X-API-Key')
    
    # Get JWT token from Authorization header
    auth_header = request.headers.get('Authorization')
    
    # Try API key first
    if api_key:
        validation = license_manager.validate_api_key(api_key)
        
        if not validation['valid']:
            return False, None, {
                'error': 'Invalid API key',
                'reason': validation.get('reason')
            }
        
        return True, validation, None
    
    # Try JWT token
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header[7:]
        user = license_manager.verify_jwt_token(token)
        
        if not user:
            return False, None, {'error': 'Invalid or expired token'}
        
        # Validate license
        license_key = user.get('license_key')
        org_id = user.get('org_id')
        
        if license_key:
            license_validation = license_manager.validate_license(license_key, org_id)
            
            if not license_validation['valid']:
                return False, None, {
                    'error': 'Invalid license',
                    'reason': license_validation.get('reason')
                }
            
            return True, {
                'user_id': user['user_id'],
                'org_id': user['org_id'],
                'username': user['username'],
                'role': user['role'],
                'license_key': license_key,
                'license_info': license_validation
            }, None
        else:
            # Super admin or user without license - allow with limited info
            return True, {
                'user_id': user['user_id'],
                'org_id': user.get('org_id'),
                'username': user['username'],
                'role': user['role'],
                'license_key': license_key,
                'license_info': {'features': []}  # Empty features for super admin
            }, None
    
    # No auth provided
    return False, None, {'error': 'Authentication required. Provide X-API-Key or Authorization header'}

def require_license(features=None):
    """
    Decorator to require valid license for endpoint
    Optionally check for specific features
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            # Validate request
            valid, user_info, error = validate_request()
            
            if not valid:
                return jsonify(error), 401
            
            # Check feature requirements
            if features:
                if 'license_info' in user_info:
                    license_features = user_info['license_info'].get('features', [])
                elif 'license_info' in user_info.get('license_info', {}):
                    license_features = user_info['license_info']['features']
                else:
                    license_features = []
                
                missing = [f for f in features if f not in license_features]
                
                if missing:
                    return jsonify({
                        'error': 'License missing required features',
                        'missing_features': missing
                    }), 403
            
            # Attach user info to request
            request.user_info = user_info
            
            # Execute endpoint
            response = f(*args, **kwargs)
            
            # Log API usage
            response_time = (time.time() - start_time) * 1000  # ms
            
            try:
                license_manager.log_api_usage(
                    api_key=request.headers.get('X-API-Key', 'jwt_auth'),
                    user_id=user_info.get('user_id', ''),
                    org_id=user_info.get('org_id', ''),
                    endpoint=request.path,
                    method=request.method,
                    response_code=response[1] if isinstance(response, tuple) else 200,
                    response_time=response_time
                )
            except:
                pass  # Don't fail request if logging fails
            
            return response
        
        return decorated_function
    return decorator

def require_role(roles):
    """
    Decorator to require specific user role(s)
    roles: str or list of str
    """
    if isinstance(roles, str):
        roles = [roles]
    
    def decorator(f):
        @wraps(f)
        @require_license()
        def decorated_function(*args, **kwargs):
            user_role = request.user_info.get('role', 'user')
            
            if user_role not in roles:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_roles': roles,
                    'your_role': user_role
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def public_endpoint(f):
    """Mark endpoint as public (no auth required)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Still log the request if possible
        try:
            valid, user_info, _ = validate_request()
            if valid:
                request.user_info = user_info
        except:
            pass
        
        return f(*args, **kwargs)
    
    return decorated_function

def rate_limit(max_calls: int, period_seconds: int):
    """
    Rate limiting decorator
    max_calls: maximum calls allowed
    period_seconds: time period in seconds
    """
    def decorator(f):
        @wraps(f)
        @require_license()
        def decorated_function(*args, **kwargs):
            # Get rate limit info from license
            license_info = request.user_info.get('license_info', {})
            max_api_calls = license_info.get('max_api_calls', 10000)
            
            # Check if limit exceeded
            # (In production, implement Redis-based rate limiting)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

