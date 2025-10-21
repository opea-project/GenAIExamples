#!/usr/bin/env python3
"""
Cogniware Core - Super Admin API Server
Complete admin portal for license and customer management
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from functools import wraps

# Import licensing service
from licensing_service import license_manager
from llm_manager import llm_manager
from cogniware_llms import (
    get_all_llms, get_interface_llms, get_knowledge_llms,
    get_embedding_llms, get_specialized_llms, get_llm_by_id,
    get_llms_summary, get_external_sources
)
from parallel_llm_executor import execute_with_parallel_llms, get_executor_statistics

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
BASE_DIR = Path(__file__).parent.parent

# =============================================================================
# AUTHENTICATION MIDDLEWARE
# =============================================================================

def require_auth(f):
    """Require valid JWT token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'No authorization token provided'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        user = license_manager.verify_jwt_token(token)
        
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Attach user to request
        request.user = user
        return f(*args, **kwargs)
    
    return decorated_function

def require_super_admin(f):
    """Require super admin role"""
    @wraps(f)
    @require_auth
    def decorated_function(*args, **kwargs):
        if request.user.get('role') != 'super_admin':
            return jsonify({'error': 'Super admin access required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin(f):
    """Require admin or super_admin role"""
    @wraps(f)
    @require_auth
    def decorated_function(*args, **kwargs):
        role = request.user.get('role')
        if role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_license(features=None):
    """Require valid license with optional features"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            license_key = request.user.get('license_key')
            org_id = request.user.get('org_id')
            
            if not license_key:
                return jsonify({'error': 'No license assigned'}), 403
            
            validation = license_manager.validate_license(license_key, org_id)
            
            if not validation['valid']:
                return jsonify({
                    'error': 'Invalid license',
                    'reason': validation.get('reason')
                }), 403
            
            # Check features if specified
            if features:
                license_features = validation.get('features', [])
                missing_features = [f for f in features if f not in license_features]
                
                if missing_features:
                    return jsonify({
                        'error': 'License missing required features',
                        'missing': missing_features
                    }), 403
            
            # Attach license info to request
            request.license = validation
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# =============================================================================
# PUBLIC ENDPOINTS (No Auth Required)
# =============================================================================

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "name": "Cogniware Core - Admin API",
        "version": "1.0.0",
        "company": "Cogniware Incorporated",
        "description": "Super Admin portal for licensing and customer management"
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "1.0.0-admin"
    })

@app.route('/auth/login', methods=['POST'])
def login():
    """User login - returns JWT token"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = license_manager.authenticate_user(username, password)
    
    if not user:
        # Log failed attempt
        license_manager.log_audit(
            None, None, 'login_failed', 'auth',
            f'Failed login attempt for username: {username}',
            request.remote_addr
        )
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Get user's license
    conn = license_manager.db_path
    import sqlite3
    conn = sqlite3.connect(license_manager.db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT license_key FROM licenses
        WHERE org_id=? AND status='active'
        ORDER BY expiry_date DESC LIMIT 1
    """, (user['org_id'],))
    
    row = cursor.fetchone()
    conn.close()
    
    license_key = row[0] if row else None
    
    # Generate JWT
    token = license_manager.generate_jwt_token(user, license_key or '')
    
    # Log successful login
    license_manager.log_audit(
        user['user_id'], user['org_id'], 'login_success', 'auth',
        f"User {username} logged in",
        request.remote_addr
    )
    
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user['email'],
            'full_name': user['full_name'],
            'role': user['role'],
            'org_id': user['org_id']
        },
        'license_key': license_key
    })

# =============================================================================
# ORGANIZATION MANAGEMENT (Super Admin Only)
# =============================================================================

@app.route('/admin/organizations', methods=['POST'])
@require_super_admin
def create_organization():
    """Create new organization"""
    data = request.get_json()
    
    result = license_manager.create_organization(
        org_name=data.get('org_name'),
        org_type=data.get('org_type', 'customer'),
        contact_email=data.get('contact_email'),
        contact_phone=data.get('contact_phone'),
        address=data.get('address')
    )
    
    if result['success']:
        license_manager.log_audit(
            request.user['user_id'], request.user['org_id'],
            'create_organization', 'organization',
            json.dumps(result),
            request.remote_addr
        )
    
    return jsonify(result)

@app.route('/admin/organizations', methods=['GET'])
@require_super_admin
def list_organizations():
    """List all organizations"""
    orgs = license_manager.list_organizations()
    return jsonify({
        'success': True,
        'organizations': orgs,
        'count': len(orgs)
    })

@app.route('/admin/organizations/<org_id>', methods=['GET'])
@require_admin
def get_organization(org_id):
    """Get organization details"""
    # Super admin can see any org, admin can only see their own
    if request.user['role'] != 'super_admin' and request.user['org_id'] != org_id:
        return jsonify({'error': 'Access denied'}), 403
    
    org = license_manager.get_organization(org_id)
    
    if not org:
        return jsonify({'error': 'Organization not found'}), 404
    
    return jsonify({'success': True, 'organization': org})

# =============================================================================
# USER MANAGEMENT
# =============================================================================

@app.route('/admin/users', methods=['POST'])
@require_admin
def create_user():
    """Create new user"""
    data = request.get_json()
    
    # Determine org_id
    if request.user['role'] == 'super_admin':
        org_id = data.get('org_id')  # Super admin can specify org
    else:
        org_id = request.user['org_id']  # Admin can only create in their org
    
    result = license_manager.create_user(
        org_id=org_id,
        username=data.get('username'),
        email=data.get('email'),
        password=data.get('password'),
        full_name=data.get('full_name'),
        role=data.get('role', 'user')
    )
    
    if result['success']:
        license_manager.log_audit(
            request.user['user_id'], org_id,
            'create_user', 'user',
            json.dumps(result),
            request.remote_addr
        )
    
    return jsonify(result)

@app.route('/admin/users/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user info"""
    return jsonify({
        'success': True,
        'user': request.user
    })

@app.route('/admin/users', methods=['GET'])
@require_admin
def list_users():
    """List all users"""
    org_id = request.args.get('org_id')
    
    # Super admin can see all users, admin can only see their org
    if request.user['role'] != 'super_admin':
        org_id = request.user['org_id']
    
    import sqlite3
    conn = sqlite3.connect(license_manager.db_path)
    cursor = conn.cursor()
    
    if org_id:
        cursor.execute("""
            SELECT user_id, username, email, full_name, role, org_id, status, created_at
            FROM users WHERE org_id=? ORDER BY created_at DESC
        """, (org_id,))
    else:
        cursor.execute("""
            SELECT user_id, username, email, full_name, role, org_id, status, created_at
            FROM users ORDER BY created_at DESC
        """)
    
    rows = cursor.fetchall()
    conn.close()
    
    users = [{
        'user_id': row[0],
        'username': row[1],
        'email': row[2],
        'full_name': row[3],
        'role': row[4],
        'org_id': row[5],
        'status': row[6],
        'created_at': row[7]
    } for row in rows]
    
    return jsonify({
        'success': True,
        'users': users,
        'count': len(users)
    })

@app.route('/admin/users/<user_id>/password', methods=['POST'])
@require_super_admin
def change_user_password(user_id):
    """Change user password - super admin only"""
    data = request.get_json()
    new_password = data.get('new_password')
    
    if not new_password or len(new_password) < 8:
        return jsonify({
            'success': False,
            'error': 'Password must be at least 8 characters'
        }), 400
    
    success = license_manager.change_password(user_id, new_password)
    
    if success:
        license_manager.log_audit(
            request.user['user_id'], request.user['org_id'],
            'change_password', 'user',
            f'Changed password for user: {user_id}',
            request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'User not found'
        }), 404

@app.route('/admin/users/<user_id>/status', methods=['POST'])
@require_super_admin
def update_user_status(user_id):
    """Update user status - super admin only"""
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['active', 'inactive', 'suspended']:
        return jsonify({
            'success': False,
            'error': 'Invalid status. Must be: active, inactive, or suspended'
        }), 400
    
    success = license_manager.update_user_status(user_id, status)
    
    if success:
        license_manager.log_audit(
            request.user['user_id'], request.user['org_id'],
            'update_user_status', 'user',
            f'Changed status to {status} for user: {user_id}',
            request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'message': f'User status changed to {status}'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'User not found'
        }), 404

# =============================================================================
# LICENSE MANAGEMENT
# =============================================================================

@app.route('/admin/licenses', methods=['POST'])
@require_super_admin
def create_license():
    """Create new license"""
    data = request.get_json()
    
    result = license_manager.create_license(
        org_id=data.get('org_id'),
        license_type=data.get('license_type'),
        features=data.get('features', []),
        max_users=data.get('max_users', 1),
        max_api_calls=data.get('max_api_calls', 10000),
        days_valid=data.get('days_valid', 365),
        created_by=request.user['user_id']
    )
    
    if result['success']:
        license_manager.log_audit(
            request.user['user_id'], data.get('org_id'),
            'create_license', 'license',
            json.dumps(result),
            request.remote_addr
        )
    
    return jsonify(result)

@app.route('/admin/licenses', methods=['GET'])
@require_admin
def list_licenses():
    """List licenses"""
    # Super admin sees all, admin sees their org only
    if request.user['role'] == 'super_admin':
        org_id = request.args.get('org_id')
    else:
        org_id = request.user['org_id']
    
    licenses = license_manager.list_licenses(org_id)
    
    return jsonify({
        'success': True,
        'licenses': licenses,
        'count': len(licenses)
    })

@app.route('/admin/licenses/<license_key>', methods=['GET'])
@require_admin
def get_license(license_key):
    """Get license details"""
    license_info = license_manager.get_license(license_key)
    
    if not license_info:
        return jsonify({'error': 'License not found'}), 404
    
    # Check access
    if request.user['role'] != 'super_admin' and license_info['org_id'] != request.user['org_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    # Validate license
    validation = license_manager.validate_license(license_key, license_info['org_id'])
    license_info['validation'] = validation
    
    return jsonify({'success': True, 'license': license_info})

@app.route('/admin/licenses/<license_key>/revoke', methods=['POST'])
@require_super_admin
def revoke_license(license_key):
    """Revoke a license"""
    success = license_manager.revoke_license(license_key)
    
    if success:
        license_manager.log_audit(
            request.user['user_id'], request.user['org_id'],
            'revoke_license', 'license',
            f'Revoked license: {license_key}',
            request.remote_addr
        )
    
    return jsonify({
        'success': success,
        'message': 'License revoked' if success else 'License not found'
    })

# =============================================================================
# API KEY MANAGEMENT
# =============================================================================

@app.route('/admin/api-keys', methods=['POST'])
@require_auth
def create_api_key():
    """Create API key"""
    data = request.get_json()
    
    # User can only create API keys for themselves unless admin
    if request.user['role'] not in ['admin', 'super_admin']:
        user_id = request.user['user_id']
        org_id = request.user['org_id']
    else:
        user_id = data.get('user_id', request.user['user_id'])
        org_id = data.get('org_id', request.user['org_id'])
    
    license_key = data.get('license_key') or request.user.get('license_key')
    
    result = license_manager.create_api_key(
        user_id=user_id,
        org_id=org_id,
        license_key=license_key,
        name=data.get('name', 'API Key'),
        permissions=data.get('permissions', ['read', 'write']),
        days_valid=data.get('days_valid', 365)
    )
    
    if result['success']:
        license_manager.log_audit(
            request.user['user_id'], org_id,
            'create_api_key', 'api_key',
            json.dumps({'key_name': data.get('name')}),
            request.remote_addr
        )
    
    return jsonify(result)

# =============================================================================
# USAGE STATISTICS
# =============================================================================

@app.route('/admin/usage/<org_id>', methods=['GET'])
@require_admin
def get_usage_stats(org_id):
    """Get usage statistics"""
    # Check access
    if request.user['role'] != 'super_admin' and request.user['org_id'] != org_id:
        return jsonify({'error': 'Access denied'}), 403
    
    days = int(request.args.get('days', 30))
    stats = license_manager.get_usage_stats(org_id, days)
    
    return jsonify({
        'success': True,
        'stats': stats
    })

# =============================================================================
# SYSTEM MANAGEMENT (Super Admin Only)
# =============================================================================

@app.route('/admin/system/services', methods=['GET'])
@require_super_admin
def list_services():
    """List all Cogniware services"""
    try:
        # Get service status
        result = subprocess.run(
            ['systemctl', 'list-units', '--type=service', '--all', 'cogniware-*'],
            capture_output=True, text=True, timeout=5
        )
        
        services = []
        for line in result.stdout.split('\n'):
            if 'cogniware-' in line:
                parts = line.split()
                if len(parts) >= 4:
                    services.append({
                        'name': parts[0],
                        'load': parts[1],
                        'active': parts[2],
                        'sub': parts[3]
                    })
        
        return jsonify({
            'success': True,
            'services': services
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/admin/system/services/<service_name>/<action>', methods=['POST'])
@require_super_admin
def control_service(service_name, action):
    """Control system services"""
    valid_services = ['cogniware-demo', 'cogniware-production', 'cogniware-business']
    valid_actions = ['start', 'stop', 'restart', 'status']
    
    if service_name not in valid_services:
        return jsonify({'error': 'Invalid service name'}), 400
    
    if action not in valid_actions:
        return jsonify({'error': 'Invalid action'}), 400
    
    try:
        result = subprocess.run(
            ['sudo', 'systemctl', action, service_name],
            capture_output=True, text=True, timeout=10
        )
        
        license_manager.log_audit(
            request.user['user_id'], request.user['org_id'],
            f'service_{action}', 'system',
            f'{action.capitalize()} service: {service_name}',
            request.remote_addr
        )
        
        return jsonify({
            'success': result.returncode == 0,
            'service': service_name,
            'action': action,
            'output': result.stdout,
            'error': result.stderr
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# =============================================================================
# AUDIT LOG
# =============================================================================

@app.route('/admin/audit', methods=['GET'])
@require_admin
def get_audit_log():
    """Get audit log"""
    org_id = request.args.get('org_id')
    limit = int(request.args.get('limit', 100))
    
    # Check access
    if request.user['role'] != 'super_admin':
        org_id = request.user['org_id']
    
    import sqlite3
    conn = sqlite3.connect(license_manager.db_path)
    cursor = conn.cursor()
    
    if org_id:
        cursor.execute("""
            SELECT * FROM audit_log WHERE org_id=?
            ORDER BY timestamp DESC LIMIT ?
        """, (org_id, limit))
    else:
        cursor.execute("""
            SELECT * FROM audit_log
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    logs = [{
        'id': row[0],
        'user_id': row[1],
        'org_id': row[2],
        'action': row[3],
        'resource': row[4],
        'details': row[5],
        'timestamp': row[6],
        'ip_address': row[7]
    } for row in rows]
    
    return jsonify({
        'success': True,
        'logs': logs,
        'count': len(logs)
    })

# =============================================================================
# LLM MANAGEMENT (Super Admin Only)
# =============================================================================

# Cogniware Built-in LLMs (NEW)
@app.route('/admin/llm/cogniware/all', methods=['GET'])
@require_super_admin
def get_cogniware_llms():
    """Get all built-in Cogniware LLMs"""
    return jsonify({
        'success': True,
        'llms': get_all_llms(),
        'count': len(get_all_llms()),
        'summary': get_llms_summary()
    })

@app.route('/admin/llm/cogniware/interface', methods=['GET'])
@require_super_admin
def get_cogniware_interface_llms():
    """Get Cogniware interface LLMs"""
    return jsonify({
        'success': True,
        'llms': get_interface_llms(),
        'count': len(get_interface_llms())
    })

@app.route('/admin/llm/cogniware/knowledge', methods=['GET'])
@require_super_admin
def get_cogniware_knowledge_llms():
    """Get Cogniware knowledge LLMs"""
    return jsonify({
        'success': True,
        'llms': get_knowledge_llms(),
        'count': len(get_knowledge_llms())
    })

@app.route('/admin/llm/cogniware/embedding', methods=['GET'])
@require_super_admin
def get_cogniware_embedding_llms():
    """Get Cogniware embedding models"""
    return jsonify({
        'success': True,
        'llms': get_embedding_llms(),
        'count': len(get_embedding_llms())
    })

@app.route('/admin/llm/cogniware/specialized', methods=['GET'])
@require_super_admin
def get_cogniware_specialized_llms():
    """Get Cogniware specialized models"""
    return jsonify({
        'success': True,
        'llms': get_specialized_llms(),
        'count': len(get_specialized_llms())
    })

@app.route('/admin/llm/cogniware/<model_id>', methods=['GET'])
@require_super_admin
def get_cogniware_llm_details(model_id):
    """Get details of a specific Cogniware LLM"""
    llm = get_llm_by_id(model_id)
    if not llm:
        return jsonify({'error': 'Model not found'}), 404
    
    return jsonify({
        'success': True,
        'llm': llm
    })

# External sources for downloading/importing models
@app.route('/admin/llm/sources/external', methods=['GET'])
@require_super_admin
def get_external_model_sources():
    """Get external sources for importing models (Ollama, HuggingFace)"""
    return jsonify({
        'success': True,
        'sources': get_external_sources(),
        'description': 'External sources to download and import models from'
    })

@app.route('/admin/llm/sources/ollama', methods=['GET'])
@require_super_admin
def get_ollama_models():
    """Get available Ollama models for importing"""
    sources = get_external_sources()
    return jsonify({
        'success': True,
        'source': 'ollama',
        'models': sources['ollama']['models'],
        'description': 'Models available from Ollama for downloading and importing'
    })

@app.route('/admin/llm/sources/huggingface', methods=['GET'])
@require_super_admin
def get_huggingface_models():
    """Get popular HuggingFace models for importing"""
    sources = get_external_sources()
    return jsonify({
        'success': True,
        'source': 'huggingface',
        'models': sources['huggingface']['models'],
        'description': 'Models available from HuggingFace for downloading and importing'
    })

@app.route('/admin/llm/interface', methods=['POST'])
@require_super_admin
def create_interface_llm():
    """Create interface LLM"""
    data = request.get_json()
    
    result = llm_manager.create_interface_llm(
        model_name=data.get('model_name'),
        source=data.get('source'),
        source_model_id=data.get('source_model_id'),
        size_gb=data.get('size_gb', 0),
        parameters=data.get('parameters', ''),
        created_by=request.user['user_id']
    )
    
    if result['success']:
        license_manager.log_audit(
            request.user['user_id'], request.user['org_id'],
            'create_interface_llm', 'llm',
            json.dumps(result),
            request.remote_addr
        )
    
    return jsonify(result)

@app.route('/admin/llm/knowledge', methods=['POST'])
@require_super_admin
def create_knowledge_llm():
    """Create knowledge LLM"""
    data = request.get_json()
    
    result = llm_manager.create_knowledge_llm(
        model_name=data.get('model_name'),
        source=data.get('source'),
        source_model_id=data.get('source_model_id'),
        size_gb=data.get('size_gb', 0),
        parameters=data.get('parameters', ''),
        created_by=request.user['user_id']
    )
    
    if result['success']:
        license_manager.log_audit(
            request.user['user_id'], request.user['org_id'],
            'create_knowledge_llm', 'llm',
            json.dumps(result),
            request.remote_addr
        )
    
    return jsonify(result)

@app.route('/admin/llm/models', methods=['GET'])
@require_super_admin
def list_llm_models():
    """List all LLM models"""
    model_type = request.args.get('type')
    models = llm_manager.list_models(model_type)
    
    return jsonify({
        'success': True,
        'models': models,
        'count': len(models)
    })

@app.route('/admin/llm/models/<model_id>', methods=['GET'])
@require_super_admin
def get_llm_model_status(model_id):
    """Get model status"""
    status = llm_manager.get_model_status(model_id)
    
    if not status:
        return jsonify({'error': 'Model not found'}), 404
    
    return jsonify({
        'success': True,
        'model': status
    })

@app.route('/admin/llm/models/<model_id>', methods=['DELETE'])
@require_super_admin
def delete_llm_model(model_id):
    """Delete LLM model"""
    success = llm_manager.delete_model(model_id)
    
    if success:
        license_manager.log_audit(
            request.user['user_id'], request.user['org_id'],
            'delete_llm', 'llm',
            f'Deleted model: {model_id}',
            request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'message': 'Model deleted successfully'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Model not found'
        }), 404

@app.route('/admin/llm/statistics', methods=['GET'])
@require_super_admin
def get_llm_statistics():
    """Get LLM statistics"""
    stats = llm_manager.get_statistics()
    return jsonify({
        'success': True,
        'statistics': stats
    })

# =============================================================================
# USER-ACCESSIBLE LLM ENDPOINTS (All authenticated users)
# =============================================================================

@app.route('/api/llms/available', methods=['GET'])
@require_auth
def get_user_available_llms():
    """Get available LLMs for regular users"""
    interface_llms = get_interface_llms()
    knowledge_llms = get_knowledge_llms()
    
    return jsonify({
        'success': True,
        'llms': {
            'interface_llms': interface_llms,
            'knowledge_llms': knowledge_llms,
            'total': len(interface_llms) + len(knowledge_llms)
        },
        'message': f'{len(interface_llms)} interface and {len(knowledge_llms)} knowledge LLMs available'
    })

@app.route('/api/nl/llms/available', methods=['GET'])
@require_auth
def get_nl_available_llms():
    """Get available LLMs (alias for compatibility)"""
    interface_llms = get_interface_llms()
    knowledge_llms = get_knowledge_llms()
    
    return jsonify({
        'success': True,
        'llms': {
            'interface_llms': interface_llms,
            'knowledge_llms': knowledge_llms,
            'total': len(interface_llms) + len(knowledge_llms)
        },
        'message': f'{len(interface_llms)} interface and {len(knowledge_llms)} knowledge LLMs available'
    })

@app.route('/api/llms/list', methods=['GET'])
@require_auth
def list_user_llms():
    """List all LLMs available to users"""
    all_llms = get_all_llms()
    return jsonify({
        'success': True,
        'llms': all_llms,
        'count': len(all_llms)
    })

@app.route('/api/llms/<model_id>', methods=['GET'])
@require_auth
def get_user_llm_details(model_id):
    """Get LLM details for users"""
    llm = get_llm_by_id(model_id)
    if not llm:
        return jsonify({'error': 'Model not found'}), 404
    
    return jsonify({
        'success': True,
        'llm': llm
    })

# =============================================================================
# PARALLEL LLM EXECUTION (Patent-Compliant MCP)
# =============================================================================

@app.route('/api/nl/process', methods=['POST'])
@require_auth
def process_natural_language():
    """
    Process natural language using PARALLEL LLM execution (PATENT CLAIM)
    Executes Interface + Knowledge LLMs simultaneously for superior results
    """
    data = request.get_json()
    instruction = data.get('instruction', '')
    strategy = data.get('strategy', 'parallel')
    num_interface = data.get('num_interface_llms', 2)
    num_knowledge = data.get('num_knowledge_llms', 1)
    
    if not instruction:
        return jsonify({'success': False, 'error': 'No instruction provided'}), 400
    
    result = execute_with_parallel_llms(
        prompt=instruction,
        strategy=strategy,
        num_interface=num_interface,
        num_knowledge=num_knowledge
    )
    
    # Add execution plan and intent for frontend compatibility
    result['execution_plan'] = {
        'module': 'general',
        'steps': [{'description': 'Execute with parallel LLMs'}]
    }
    result['intent'] = {'module': 'general', 'action': 'process'}
    result['generated_output'] = result.pop('result', '')
    
    return jsonify(result)

@app.route('/api/nl/statistics', methods=['GET'])
@require_auth
def get_nl_statistics():
    """Get parallel LLM execution statistics"""
    stats = get_executor_statistics()
    return jsonify({
        'success': True,
        'statistics': stats,
        'description': 'Patent-compliant Multi-Context Processing (MCP) statistics'
    })

# =============================================================================
# STARTUP
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Cogniware Core - Super Admin API Server")
    print("=" * 70)
    print("Features:")
    print("  • Complete licensing system")
    print("  • Customer & user management")
    print("  • Organization management")
    print("  • API key management")
    print("  • Usage tracking & analytics")
    print("  • System service control")
    print("  • Audit logging")
    print("")
    print("Default Super Admin:")
    print("  Username: superadmin")
    print("  Password: Cogniware@2025")
    print("  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!")
    print("")
    print("Starting server on http://0.0.0.0:8099")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=8099, debug=True)

