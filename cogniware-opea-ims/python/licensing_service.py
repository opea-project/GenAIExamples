#!/usr/bin/env python3
"""
Cogniware Core - Licensing Service
Complete licensing system with online/offline validation
"""

import os
import json
import time
import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
import jwt

# Configuration
BASE_DIR = Path(__file__).parent.parent
LICENSE_DB = BASE_DIR / "databases" / "licenses.db"
LICENSE_SECRET = os.environ.get('LICENSE_SECRET', secrets.token_urlsafe(32))

class LicenseManager:
    """Manage licenses, users, and organizations"""
    
    def __init__(self):
        self.db_path = LICENSE_DB
        self.secret = LICENSE_SECRET
        self._init_database()
    
    def _init_database(self):
        """Initialize license database with all tables"""
        LICENSE_DB.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Organizations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                org_id TEXT PRIMARY KEY,
                org_name TEXT NOT NULL,
                org_type TEXT,
                contact_email TEXT,
                contact_phone TEXT,
                address TEXT,
                created_at TEXT,
                updated_at TEXT,
                status TEXT DEFAULT 'active'
            )
        """)
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                status TEXT DEFAULT 'active',
                created_at TEXT,
                last_login TEXT,
                FOREIGN KEY (org_id) REFERENCES organizations(org_id)
            )
        """)
        
        # Licenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                license_key TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                license_type TEXT NOT NULL,
                features TEXT,
                max_users INTEGER DEFAULT 1,
                max_api_calls INTEGER DEFAULT 10000,
                issued_date TEXT,
                expiry_date TEXT,
                status TEXT DEFAULT 'active',
                created_by TEXT,
                FOREIGN KEY (org_id) REFERENCES organizations(org_id)
            )
        """)
        
        # API Keys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                api_key TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                license_key TEXT NOT NULL,
                name TEXT,
                permissions TEXT,
                created_at TEXT,
                expires_at TEXT,
                last_used TEXT,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (org_id) REFERENCES organizations(org_id),
                FOREIGN KEY (license_key) REFERENCES licenses(license_key)
            )
        """)
        
        # API Usage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT NOT NULL,
                user_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                endpoint TEXT,
                method TEXT,
                timestamp TEXT,
                response_code INTEGER,
                response_time REAL,
                FOREIGN KEY (api_key) REFERENCES api_keys(api_key)
            )
        """)
        
        # Audit Log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                org_id TEXT,
                action TEXT,
                resource TEXT,
                details TEXT,
                timestamp TEXT,
                ip_address TEXT
            )
        """)
        
        # Create super admin if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='super_admin'")
        if cursor.fetchone()[0] == 0:
            self._create_super_admin(cursor)
        
        conn.commit()
        conn.close()
    
    def _create_super_admin(self, cursor):
        """Create default super admin user"""
        admin_org_id = self._generate_id('ORG')
        admin_user_id = self._generate_id('USR')
        admin_password = 'Cogniware@2025'  # Default password - CHANGE IN PRODUCTION!
        
        # Create Cogniware organization
        cursor.execute("""
            INSERT INTO organizations (org_id, org_name, org_type, contact_email, 
                                      created_at, updated_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            admin_org_id,
            'Cogniware Incorporated',
            'system',
            'admin@cogniware.com',
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            'active'
        ))
        
        # Create super admin user
        password_hash = self._hash_password(admin_password)
        cursor.execute("""
            INSERT INTO users (user_id, org_id, username, email, password_hash,
                              full_name, role, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            admin_user_id,
            admin_org_id,
            'superadmin',
            'admin@cogniware.com',
            password_hash,
            'Super Administrator',
            'super_admin',
            'active',
            datetime.now().isoformat()
        ))
        
        print(f"✅ Super Admin Created!")
        print(f"   Username: superadmin")
        print(f"   Password: {admin_password}")
        print(f"   ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!")
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID with prefix"""
        timestamp = int(time.time() * 1000)
        random = secrets.token_hex(4)
        return f"{prefix}-{timestamp}-{random}"
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_license_key(self) -> str:
        """Generate cryptographic license key"""
        parts = []
        for _ in range(4):
            parts.append(secrets.token_hex(4).upper())
        return '-'.join(parts)
    
    def _generate_api_key(self) -> str:
        """Generate API key"""
        return f"cw_{secrets.token_urlsafe(32)}"
    
    # ========================================================================
    # ORGANIZATION MANAGEMENT
    # ========================================================================
    
    def create_organization(self, org_name: str, org_type: str, contact_email: str,
                           contact_phone: str = None, address: str = None) -> dict:
        """Create new organization"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        org_id = self._generate_id('ORG')
        
        cursor.execute("""
            INSERT INTO organizations (org_id, org_name, org_type, contact_email,
                                      contact_phone, address, created_at, updated_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            org_id, org_name, org_type, contact_email, contact_phone, address,
            datetime.now().isoformat(), datetime.now().isoformat(), 'active'
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'org_id': org_id,
            'org_name': org_name
        }
    
    def get_organization(self, org_id: str) -> Optional[dict]:
        """Get organization details"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM organizations WHERE org_id=?", (org_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'org_id': row[0],
            'org_name': row[1],
            'org_type': row[2],
            'contact_email': row[3],
            'contact_phone': row[4],
            'address': row[5],
            'created_at': row[6],
            'updated_at': row[7],
            'status': row[8]
        }
    
    def list_organizations(self) -> List[dict]:
        """List all organizations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM organizations ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'org_id': row[0],
            'org_name': row[1],
            'org_type': row[2],
            'contact_email': row[3],
            'status': row[8]
        } for row in rows]
    
    # ========================================================================
    # USER MANAGEMENT
    # ========================================================================
    
    def create_user(self, org_id: str, username: str, email: str, password: str,
                   full_name: str, role: str = 'user') -> dict:
        """Create new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if username/email exists
        cursor.execute("SELECT user_id FROM users WHERE username=? OR email=?",
                      (username, email))
        if cursor.fetchone():
            conn.close()
            return {'success': False, 'error': 'Username or email already exists'}
        
        user_id = self._generate_id('USR')
        password_hash = self._hash_password(password)
        
        cursor.execute("""
            INSERT INTO users (user_id, org_id, username, email, password_hash,
                              full_name, role, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, org_id, username, email, password_hash,
            full_name, role, 'active', datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'user_id': user_id,
            'username': username
        }
    
    def change_password(self, user_id: str, new_password: str) -> bool:
        """Change user password"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = self._hash_password(new_password)
        
        cursor.execute("""
            UPDATE users SET password_hash=? WHERE user_id=?
        """, (password_hash, user_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def update_user_status(self, user_id: str, status: str) -> bool:
        """Update user status (active, inactive, suspended)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET status=? WHERE user_id=?
        """, (status, user_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate user credentials"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = self._hash_password(password)
        
        cursor.execute("""
            SELECT user_id, org_id, username, email, full_name, role, status
            FROM users WHERE username=? AND password_hash=? AND status='active'
        """, (username, password_hash))
        
        row = cursor.fetchone()
        
        if row:
            # Update last login
            cursor.execute("UPDATE users SET last_login=? WHERE user_id=?",
                          (datetime.now().isoformat(), row[0]))
            conn.commit()
        
        conn.close()
        
        if not row:
            return None
        
        return {
            'user_id': row[0],
            'org_id': row[1],
            'username': row[2],
            'email': row[3],
            'full_name': row[4],
            'role': row[5],
            'status': row[6]
        }
    
    def generate_jwt_token(self, user: dict, license_key: str) -> str:
        """Generate JWT token for authenticated user"""
        payload = {
            'user_id': user['user_id'],
            'org_id': user['org_id'],
            'username': user['username'],
            'role': user['role'],
            'license_key': license_key,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Optional[dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    # ========================================================================
    # LICENSE MANAGEMENT
    # ========================================================================
    
    def create_license(self, org_id: str, license_type: str, features: List[str],
                      max_users: int, max_api_calls: int, days_valid: int,
                      created_by: str) -> dict:
        """Create new license"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        license_key = self._generate_license_key()
        issued_date = datetime.now()
        expiry_date = issued_date + timedelta(days=days_valid)
        
        cursor.execute("""
            INSERT INTO licenses (license_key, org_id, license_type, features,
                                 max_users, max_api_calls, issued_date, expiry_date,
                                 status, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            license_key, org_id, license_type, json.dumps(features),
            max_users, max_api_calls, issued_date.isoformat(),
            expiry_date.isoformat(), 'active', created_by
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'license_key': license_key,
            'org_id': org_id,
            'license_type': license_type,
            'expiry_date': expiry_date.isoformat()
        }
    
    def validate_license(self, license_key: str, org_id: str) -> dict:
        """Validate license - works online and offline"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT license_key, org_id, license_type, features, max_users,
                   max_api_calls, issued_date, expiry_date, status
            FROM licenses WHERE license_key=? AND org_id=?
        """, (license_key, org_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {
                'valid': False,
                'reason': 'License not found'
            }
        
        # Check status
        if row[8] != 'active':
            return {
                'valid': False,
                'reason': f'License status: {row[8]}'
            }
        
        # Check expiry
        expiry_date = datetime.fromisoformat(row[7])
        if datetime.now() > expiry_date:
            return {
                'valid': False,
                'reason': 'License expired',
                'expired_at': row[7]
            }
        
        return {
            'valid': True,
            'license_key': row[0],
            'org_id': row[1],
            'license_type': row[2],
            'features': json.loads(row[3]),
            'max_users': row[4],
            'max_api_calls': row[5],
            'expiry_date': row[7],
            'days_remaining': (expiry_date - datetime.now()).days
        }
    
    def get_license(self, license_key: str) -> Optional[dict]:
        """Get license details"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM licenses WHERE license_key=?", (license_key,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'license_key': row[0],
            'org_id': row[1],
            'license_type': row[2],
            'features': json.loads(row[3]),
            'max_users': row[4],
            'max_api_calls': row[5],
            'issued_date': row[6],
            'expiry_date': row[7],
            'status': row[8]
        }
    
    def list_licenses(self, org_id: str = None) -> List[dict]:
        """List licenses"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if org_id:
            cursor.execute("SELECT * FROM licenses WHERE org_id=? ORDER BY issued_date DESC",
                          (org_id,))
        else:
            cursor.execute("SELECT * FROM licenses ORDER BY issued_date DESC")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'license_key': row[0],
            'org_id': row[1],
            'license_type': row[2],
            'expiry_date': row[7],
            'status': row[8]
        } for row in rows]
    
    def revoke_license(self, license_key: str) -> bool:
        """Revoke a license"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE licenses SET status='revoked' WHERE license_key=?",
                      (license_key,))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    # ========================================================================
    # API KEY MANAGEMENT
    # ========================================================================
    
    def create_api_key(self, user_id: str, org_id: str, license_key: str,
                      name: str, permissions: List[str], days_valid: int = 365) -> dict:
        """Create API key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        api_key = self._generate_api_key()
        created_at = datetime.now()
        expires_at = created_at + timedelta(days=days_valid)
        
        cursor.execute("""
            INSERT INTO api_keys (api_key, user_id, org_id, license_key, name,
                                 permissions, created_at, expires_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            api_key, user_id, org_id, license_key, name,
            json.dumps(permissions), created_at.isoformat(),
            expires_at.isoformat(), 'active'
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'api_key': api_key,
            'expires_at': expires_at.isoformat()
        }
    
    def validate_api_key(self, api_key: str) -> dict:
        """Validate API key and check permissions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT api_key, user_id, org_id, license_key, permissions,
                   expires_at, status
            FROM api_keys WHERE api_key=?
        """, (api_key,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return {
                'valid': False,
                'reason': 'Invalid API key'
            }
        
        # Check status
        if row[6] != 'active':
            conn.close()
            return {
                'valid': False,
                'reason': f'API key status: {row[6]}'
            }
        
        # Check expiry
        expires_at = datetime.fromisoformat(row[5])
        if datetime.now() > expires_at:
            conn.close()
            return {
                'valid': False,
                'reason': 'API key expired'
            }
        
        # Validate license
        license_validation = self.validate_license(row[3], row[2])
        if not license_validation['valid']:
            conn.close()
            return {
                'valid': False,
                'reason': f"License invalid: {license_validation['reason']}"
            }
        
        # Update last used
        cursor.execute("UPDATE api_keys SET last_used=? WHERE api_key=?",
                      (datetime.now().isoformat(), api_key))
        conn.commit()
        conn.close()
        
        return {
            'valid': True,
            'user_id': row[1],
            'org_id': row[2],
            'license_key': row[3],
            'permissions': json.loads(row[4]),
            'license_info': license_validation
        }
    
    # ========================================================================
    # USAGE TRACKING
    # ========================================================================
    
    def log_api_usage(self, api_key: str, user_id: str, org_id: str,
                     endpoint: str, method: str, response_code: int,
                     response_time: float):
        """Log API usage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO api_usage (api_key, user_id, org_id, endpoint, method,
                                  timestamp, response_code, response_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            api_key, user_id, org_id, endpoint, method,
            datetime.now().isoformat(), response_code, response_time
        ))
        
        conn.commit()
        conn.close()
    
    def get_usage_stats(self, org_id: str, days: int = 30) -> dict:
        """Get usage statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Total API calls
        cursor.execute("""
            SELECT COUNT(*) FROM api_usage
            WHERE org_id=? AND timestamp > ?
        """, (org_id, since_date))
        total_calls = cursor.fetchone()[0]
        
        # Calls by endpoint
        cursor.execute("""
            SELECT endpoint, COUNT(*) as count
            FROM api_usage
            WHERE org_id=? AND timestamp > ?
            GROUP BY endpoint
            ORDER BY count DESC
            LIMIT 10
        """, (org_id, since_date))
        
        top_endpoints = [{'endpoint': row[0], 'count': row[1]}
                        for row in cursor.fetchall()]
        
        # Average response time
        cursor.execute("""
            SELECT AVG(response_time) FROM api_usage
            WHERE org_id=? AND timestamp > ?
        """, (org_id, since_date))
        
        avg_response_time = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'org_id': org_id,
            'period_days': days,
            'total_api_calls': total_calls,
            'average_response_time_ms': round(avg_response_time, 2),
            'top_endpoints': top_endpoints
        }
    
    # ========================================================================
    # AUDIT LOG
    # ========================================================================
    
    def log_audit(self, user_id: str, org_id: str, action: str,
                 resource: str, details: str, ip_address: str = None):
        """Log audit event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO audit_log (user_id, org_id, action, resource, details,
                                  timestamp, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, org_id, action, resource, details,
            datetime.now().isoformat(), ip_address
        ))
        
        conn.commit()
        conn.close()

# Global license manager instance
license_manager = LicenseManager()

