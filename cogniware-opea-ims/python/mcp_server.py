#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server
Provides context, data, and capabilities to LLMs by connecting to external systems
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Initialize Flask app for MCP
mcp_app = Flask(__name__)
CORS(mcp_app)

# Projects directory
PROJECTS_DIR = Path("../projects")
PROJECTS_DIR.mkdir(exist_ok=True)


class MCPServer:
    """
    Model Context Protocol Server
    Manages context and capabilities for LLM interactions
    """
    
    def __init__(self, projects_dir: Path = PROJECTS_DIR):
        self.projects_dir = projects_dir
        self.projects_dir.mkdir(exist_ok=True)
        self.active_contexts = {}
        
        # Project templates
        self.templates = {
            'fastapi': self._get_fastapi_template,
            'flask': self._get_flask_template,
            'react': self._get_react_template,
            'django': self._get_django_template,
            'express': self._get_express_template,
            'python-cli': self._get_python_cli_template,
            'blank': self._get_blank_template
        }
    
    def create_project(self, project_name: str, template: str = 'blank', 
                      description: str = '', requirements: List[str] = None) -> Dict:
        """
        Create a new project with specified template
        """
        try:
            project_path = self.projects_dir / project_name
            
            if project_path.exists():
                return {
                    'success': False,
                    'error': f'Project "{project_name}" already exists'
                }
            
            project_path.mkdir(parents=True)
            
            # Get template structure
            if template in self.templates:
                structure = self.templates[template](project_name, description, requirements or [])
            else:
                structure = self._get_blank_template(project_name, description, requirements or [])
            
            # Create files and folders
            self._create_structure(project_path, structure)
            
            # Initialize context for this project
            context_id = f"{project_name}_{datetime.now().timestamp()}"
            self.active_contexts[context_id] = {
                'project_name': project_name,
                'project_path': str(project_path),
                'template': template,
                'created_at': datetime.now().isoformat(),
                'files': self._scan_project_files(project_path)
            }
            
            return {
                'success': True,
                'project_name': project_name,
                'project_path': str(project_path),
                'context_id': context_id,
                'structure': structure,
                'files_created': len(self._scan_project_files(project_path))
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create project: {str(e)}'
            }
    
    def get_project_context(self, project_name: str) -> Dict:
        """
        Get full context of a project for LLM
        """
        try:
            project_path = self.projects_dir / project_name
            
            if not project_path.exists():
                return {
                    'success': False,
                    'error': f'Project "{project_name}" not found'
                }
            
            # Scan project structure
            files = self._scan_project_files(project_path)
            
            print(f"DEBUG: Scanned {len(files)} files in {project_name}")
            if len(files) == 0:
                print(f"DEBUG: Project path: {project_path}")
                print(f"DEBUG: Path exists: {project_path.exists()}")
                # List all items in directory for debugging
                try:
                    all_items = list(project_path.rglob('*'))
                    print(f"DEBUG: Found {len(all_items)} total items")
                    for item in all_items[:10]:
                        print(f"DEBUG:   - {item.relative_to(project_path)} ({'file' if item.is_file() else 'dir'})")
                except Exception as e:
                    print(f"DEBUG: Error listing items: {e}")
            
            # Read important files for context
            context_files = {}
            important_patterns = ['README', 'requirements', 'package.json', 'main', 'app', 'index']
            
            for file_path in files:
                file_name = os.path.basename(file_path)
                if any(pattern in file_name for pattern in important_patterns):
                    try:
                        with open(project_path / file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            context_files[file_path] = f.read()
                    except:
                        pass
            
            return {
                'success': True,
                'project_name': project_name,
                'project_path': str(project_path),
                'files': files,
                'context_files': context_files,
                'file_count': len(files)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get context: {str(e)}'
            }
    
    def create_file(self, project_name: str, file_path: str, content: str) -> Dict:
        """
        Create or update a file in the project
        """
        try:
            project_path = self.projects_dir / project_name
            
            if not project_path.exists():
                return {
                    'success': False,
                    'error': f'Project "{project_name}" not found'
                }
            
            full_path = project_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'file_path': file_path,
                'full_path': str(full_path),
                'size': len(content)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create file: {str(e)}'
            }
    
    def read_file(self, project_name: str, file_path: str) -> Dict:
        """
        Read a file from the project
        """
        try:
            project_path = self.projects_dir / project_name
            full_path = project_path / file_path
            
            if not full_path.exists():
                return {
                    'success': False,
                    'error': f'File "{file_path}" not found'
                }
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return {
                'success': True,
                'file_path': file_path,
                'content': content,
                'size': len(content),
                'lines': len(content.split('\n'))
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to read file: {str(e)}'
            }
    
    def list_projects(self) -> Dict:
        """
        List all projects
        """
        try:
            projects = []
            
            for item in self.projects_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    files = list(self._scan_project_files(item))
                    projects.append({
                        'name': item.name,
                        'path': str(item),
                        'files': len(files),
                        'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })
            
            return {
                'success': True,
                'projects': projects,
                'count': len(projects)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to list projects: {str(e)}'
            }
    
    def generate_code_with_context(self, project_name: str, prompt: str, 
                                   target_file: Optional[str] = None) -> Dict:
        """
        Generate code with full project context for LLM
        """
        try:
            # Get project context
            context = self.get_project_context(project_name)
            
            if not context['success']:
                return context
            
            # Build enhanced prompt with context
            enhanced_prompt = f"""
Project: {project_name}
Files in project: {len(context['files'])}

Project Structure:
{chr(10).join(f'  - {f}' for f in context['files'][:20])}

User Request: {prompt}
"""
            
            if target_file:
                enhanced_prompt += f"\nTarget File: {target_file}"
            
            # Add context from important files
            if context['context_files']:
                enhanced_prompt += "\n\nExisting Code Context:"
                for file_path, content in list(context['context_files'].items())[:3]:
                    enhanced_prompt += f"\n\n=== {file_path} ===\n{content[:500]}"
            
            return {
                'success': True,
                'enhanced_prompt': enhanced_prompt,
                'context': context,
                'ready_for_llm': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to generate context: {str(e)}'
            }
    
    def auto_generate_files(self, project_name: str, prompt: str) -> Dict:
        """
        Automatically generate and create files based on prompt
        Returns plan and creates files in real-time
        """
        try:
            project_path = self.projects_dir / project_name
            
            if not project_path.exists():
                return {
                    'success': False,
                    'error': f'Project "{project_name}" not found'
                }
            
            # Analyze prompt to determine what to generate
            plan = self._create_generation_plan(prompt, project_name)
            
            print(f"DEBUG: Generation plan has {len(plan['items'])} items")
            
            # Execute the plan and create files
            created_files = []
            for item in plan['items']:
                print(f"DEBUG: Creating file: {item['file_path']}")
                
                file_result = self.create_file(
                    project_name,
                    item['file_path'],
                    item['content']
                )
                
                print(f"DEBUG: File creation result: {file_result.get('success')}, path: {file_result.get('full_path')}")
                
                if file_result['success']:
                    created_files.append({
                        'path': item['file_path'],
                        'type': item['type'],
                        'description': item['description'],
                        'size': file_result['size']
                    })
            
            print(f"DEBUG: Successfully created {len(created_files)} files")
            
            # Verify files exist
            files_after = self._scan_project_files(project_path)
            print(f"DEBUG: Project now has {len(files_after)} files total")
            
            return {
                'success': True,
                'plan': plan,
                'files_created': created_files,
                'count': len(created_files),
                'total_files_in_project': len(files_after)
            }
            
        except Exception as e:
            print(f"ERROR: Auto-generation failed: {e}")
            return {
                'success': False,
                'error': f'Auto-generation failed: {str(e)}'
            }
    
    def _create_generation_plan(self, prompt: str, project_name: str) -> Dict:
        """
        Create a plan for file generation based on prompt
        """
        prompt_lower = prompt.lower()
        items = []
        
        # Detect what needs to be created
        if 'auth' in prompt_lower or 'jwt' in prompt_lower or 'login' in prompt_lower:
            items.extend([
                {
                    'file_path': 'app/auth.py',
                    'type': 'module',
                    'description': 'Authentication module with JWT',
                    'content': self._generate_auth_code()
                },
                {
                    'file_path': 'app/middleware/auth_middleware.py',
                    'type': 'middleware',
                    'description': 'JWT authentication middleware',
                    'content': self._generate_auth_middleware()
                }
            ])
        
        if 'crud' in prompt_lower or 'endpoint' in prompt_lower or 'api' in prompt_lower:
            entity = 'customer' if 'customer' in prompt_lower else 'item'
            items.extend([
                {
                    'file_path': f'app/routes/{entity}.py',
                    'type': 'routes',
                    'description': f'{entity.capitalize()} CRUD endpoints',
                    'content': self._generate_crud_routes(entity)
                },
                {
                    'file_path': f'app/models/{entity}.py',
                    'type': 'model',
                    'description': f'{entity.capitalize()} data model',
                    'content': self._generate_model(entity)
                }
            ])
        
        if 'database' in prompt_lower or 'db' in prompt_lower:
            items.append({
                'file_path': 'app/database.py',
                'type': 'config',
                'description': 'Database configuration and connection',
                'content': self._generate_database_config()
            })
        
        if 'test' in prompt_lower:
            items.append({
                'file_path': 'tests/test_api.py',
                'type': 'test',
                'description': 'API endpoint tests',
                'content': self._generate_tests()
            })
        
        # If no specific items, create a generic file
        if not items:
            items.append({
                'file_path': 'app/generated.py',
                'type': 'module',
                'description': 'Generated code based on request',
                'content': f'# Generated code for: {prompt}\n\n# TODO: Implement functionality\n'
            })
        
        return {
            'description': f'Plan to generate {len(items)} files',
            'items': items,
            'estimated_time': len(items) * 0.5  # seconds
        }
    
    def _generate_auth_code(self) -> str:
        return '''"""
Authentication module with JWT token support
"""
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def decode_access_token(token: str):
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
'''
    
    def _generate_auth_middleware(self) -> str:
        return '''"""
JWT Authentication Middleware
"""
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth import decode_access_token

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token from request"""
    token = credentials.credentials
    
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(status_code=403, detail="Invalid authentication credentials")
    
    return payload
'''
    
    def _generate_crud_routes(self, entity: str) -> str:
        entity_cap = entity.capitalize()
        return f'''"""
{entity_cap} CRUD endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.{entity} import {entity_cap}, {entity_cap}Create, {entity_cap}Update

router = APIRouter(prefix="/{entity}s", tags=["{entity}s"])

# In-memory storage (replace with database)
{entity}_db = []

@router.get("/", response_model=List[{entity_cap}])
async def get_{entity}s():
    """Get all {entity}s"""
    return {entity}_db

@router.get("/{{item_id}}", response_model={entity_cap})
async def get_{entity}(item_id: int):
    """Get {entity} by ID"""
    for item in {entity}_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="{entity_cap} not found")

@router.post("/", response_model={entity_cap}, status_code=201)
async def create_{entity}(item: {entity_cap}Create):
    """Create new {entity}"""
    new_item = {entity_cap}(
        id=len({entity}_db) + 1,
        **item.dict()
    )
    {entity}_db.append(new_item)
    return new_item

@router.put("/{{item_id}}", response_model={entity_cap})
async def update_{entity}(item_id: int, item: {entity_cap}Update):
    """Update {entity}"""
    for idx, existing in enumerate({entity}_db):
        if existing.id == item_id:
            updated = existing.copy(update=item.dict(exclude_unset=True))
            {entity}_db[idx] = updated
            return updated
    raise HTTPException(status_code=404, detail="{entity_cap} not found")

@router.delete("/{{item_id}}")
async def delete_{entity}(item_id: int):
    """Delete {entity}"""
    for idx, item in enumerate({entity}_db):
        if item.id == item_id:
            {entity}_db.pop(idx)
            return {{"message": "{entity_cap} deleted successfully"}}
    raise HTTPException(status_code=404, detail="{entity_cap} not found")
'''
    
    def _generate_model(self, entity: str) -> str:
        entity_cap = entity.capitalize()
        return f'''"""
{entity_cap} data models
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class {entity_cap}Base(BaseModel):
    """Base {entity} model"""
    name: str
    description: Optional[str] = None

class {entity_cap}Create({entity_cap}Base):
    """Model for creating {entity}"""
    pass

class {entity_cap}Update({entity_cap}Base):
    """Model for updating {entity}"""
    name: Optional[str] = None

class {entity_cap}(BaseModel):
    """Complete {entity} model"""
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime = datetime.now()
    
    class Config:
        from_attributes = True
'''
    
    def _generate_database_config(self) -> str:
        return '''"""
Database configuration and connection
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
# For PostgreSQL: "postgresql://user:password@localhost/dbname"
# For MySQL: "mysql://user:password@localhost/dbname"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Only for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''
    
    def _generate_tests(self) -> str:
        return '''"""
API endpoint tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_create_item():
    """Test item creation"""
    response = client.post(
        "/items",
        json={"name": "Test Item", "description": "Test description"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert "id" in data

def test_get_items():
    """Test getting all items"""
    response = client.get("/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
'''
    
    def _create_structure(self, base_path: Path, structure: Dict):
        """
        Recursively create folder structure and files
        """
        for key, value in structure.items():
            if key == '_files':
                # Create files
                for file_name, content in value.items():
                    file_path = base_path / file_name
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
            else:
                # Create directory
                dir_path = base_path / key
                dir_path.mkdir(exist_ok=True)
                
                # Recursively create subdirectories
                if isinstance(value, dict):
                    self._create_structure(dir_path, value)
    
    def _scan_project_files(self, project_path: Path) -> List[str]:
        """
        Scan and return all files in project (relative paths)
        """
        files = []
        try:
            for item in project_path.rglob('*'):
                if item.is_file():
                    relative = item.relative_to(project_path)
                    # Skip hidden files and __pycache__
                    if not any(part.startswith('.') or part == '__pycache__' for part in relative.parts):
                        files.append(str(relative))
        except Exception as e:
            print(f"Error scanning project files: {e}")
        return sorted(files)
    
    # =============== PROJECT TEMPLATES ===============
    
    def _get_fastapi_template(self, name: str, desc: str, reqs: List[str]) -> Dict:
        """FastAPI project template"""
        return {
            'app': {
                '_files': {
                    '__init__.py': '',
                    'main.py': f'''"""
{name} - FastAPI Application
{desc}
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="{name}", description="{desc}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None

# In-memory storage
items_db = []

@app.get("/")
async def root():
    return {{"message": "Welcome to {name} API", "version": "1.0.0"}}

@app.get("/items", response_model=List[Item])
async def get_items():
    return items_db

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    item.id = len(items_db) + 1
    items_db.append(item)
    return item

@app.get("/items/{{item_id}}", response_model=Item)
async def get_item(item_id: int):
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''',
                    'models.py': '# Data models\n',
                    'database.py': '# Database configuration\n',
                }
            },
            'tests': {
                '_files': {
                    '__init__.py': '',
                    'test_main.py': '# Tests\nimport pytest\n'
                }
            },
            '_files': {
                'requirements.txt': 'fastapi>=0.104.0\nuvicorn>=0.24.0\npydantic>=2.0.0\n',
                'README.md': f'# {name}\n\n{desc}\n\n## Installation\n```bash\npip install -r requirements.txt\n```\n\n## Run\n```bash\npython app/main.py\n```\n',
                '.gitignore': '__pycache__/\n*.pyc\n.env\nvenv/\n'
            }
        }
    
    def _get_flask_template(self, name: str, desc: str, reqs: List[str]) -> Dict:
        """Flask project template"""
        return {
            'app': {
                '_files': {
                    '__init__.py': f'''from flask import Flask, jsonify
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/')
    def home():
        return jsonify({{"message": "Welcome to {name}"}})
    
    return app
''',
                    'routes.py': '# API routes\n',
                }
            },
            '_files': {
                'run.py': 'from app import create_app\n\napp = create_app()\n\nif __name__ == "__main__":\n    app.run(debug=True)\n',
                'requirements.txt': 'Flask>=3.0.0\nFlask-CORS>=4.0.0\n',
                'README.md': f'# {name}\n\n{desc}\n',
            }
        }
    
    def _get_react_template(self, name: str, desc: str, reqs: List[str]) -> Dict:
        """React project template"""
        return {
            'src': {
                '_files': {
                    'App.js': f'''import React from 'react';
import './App.css';

function App() {{
  return (
    <div className="App">
      <h1>{name}</h1>
      <p>{desc}</p>
    </div>
  );
}}

export default App;
''',
                    'index.js': '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
''',
                    'App.css': '.App { text-align: center; padding: 20px; }'
                }
            },
            'public': {
                '_files': {
                    'index.html': f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>{name}</title>
</head>
<body>
    <div id="root"></div>
</body>
</html>'''
                }
            },
            '_files': {
                'package.json': json.dumps({
                    'name': name.lower().replace(' ', '-'),
                    'version': '1.0.0',
                    'dependencies': {
                        'react': '^18.2.0',
                        'react-dom': '^18.2.0'
                    }
                }, indent=2),
                'README.md': f'# {name}\n\n{desc}\n'
            }
        }
    
    def _get_django_template(self, name: str, desc: str, reqs: List[str]) -> Dict:
        """Django project template"""
        app_name = name.lower().replace(' ', '_').replace('-', '_')
        return {
            app_name: {
                '_files': {
                    '__init__.py': '',
                    'settings.py': '# Django settings\n',
                    'urls.py': 'from django.contrib import admin\nfrom django.urls import path\n\nurlpatterns = [path("admin/", admin.site.urls)]\n',
                    'wsgi.py': '# WSGI config\n',
                }
            },
            '_files': {
                'manage.py': f'#!/usr/bin/env python\nimport os\nimport sys\n\nif __name__ == "__main__":\n    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{app_name}.settings")\n',
                'requirements.txt': 'Django>=4.2.0\n',
                'README.md': f'# {name}\n\n{desc}\n'
            }
        }
    
    def _get_express_template(self, name: str, desc: str, reqs: List[str]) -> Dict:
        """Express.js project template"""
        return {
            'src': {
                '_files': {
                    'server.js': f'''const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

app.get('/', (req, res) => {{
    res.json({{ message: 'Welcome to {name}' }});
}});

app.listen(PORT, () => {{
    console.log(`Server running on port ${{PORT}}`);
}});
''',
                }
            },
            '_files': {
                'package.json': json.dumps({
                    'name': name.lower().replace(' ', '-'),
                    'version': '1.0.0',
                    'main': 'src/server.js',
                    'scripts': {
                        'start': 'node src/server.js'
                    },
                    'dependencies': {
                        'express': '^4.18.0',
                        'cors': '^2.8.5'
                    }
                }, indent=2),
                'README.md': f'# {name}\n\n{desc}\n'
            }
        }
    
    def _get_python_cli_template(self, name: str, desc: str, reqs: List[str]) -> Dict:
        """Python CLI tool template"""
        return {
            'src': {
                '_files': {
                    '__init__.py': '',
                    'main.py': f'''#!/usr/bin/env python3
"""
{name}
{desc}
"""
import argparse

def main():
    parser = argparse.ArgumentParser(description="{desc}")
    parser.add_argument('--version', action='version', version='1.0.0')
    
    args = parser.parse_args()
    print("Hello from {name}!")

if __name__ == "__main__":
    main()
''',
                }
            },
            'tests': {
                '_files': {
                    '__init__.py': '',
                    'test_main.py': 'import pytest\n'
                }
            },
            '_files': {
                'requirements.txt': 'click>=8.0.0\n',
                'setup.py': f'''from setuptools import setup, find_packages

setup(
    name="{name.lower().replace(" ", "-")}",
    version="1.0.0",
    packages=find_packages(),
    entry_points={{
        'console_scripts': [
            '{name.lower()}=src.main:main',
        ],
    }},
)
''',
                'README.md': f'# {name}\n\n{desc}\n'
            }
        }
    
    def _get_blank_template(self, name: str, desc: str, reqs: List[str]) -> Dict:
        """Blank project template"""
        return {
            'src': {
                '_files': {
                    'main.py': f'''"""
{name}
{desc}
"""

def main():
    print("Hello from {name}!")

if __name__ == "__main__":
    main()
'''
                }
            },
            '_files': {
                'README.md': f'# {name}\n\n{desc}\n',
                'requirements.txt': '\n'.join(reqs) if reqs else ''
            }
        }


# Global MCP instance
mcp_server = MCPServer()


# =============== API ENDPOINTS ===============

@mcp_app.route('/mcp/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'service': 'MCP Server'})

@mcp_app.route('/mcp/projects', methods=['GET'])
def list_projects():
    """List all projects"""
    result = mcp_server.list_projects()
    return jsonify(result)

@mcp_app.route('/mcp/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    data = request.get_json()
    result = mcp_server.create_project(
        project_name=data.get('name'),
        template=data.get('template', 'blank'),
        description=data.get('description', ''),
        requirements=data.get('requirements', [])
    )
    return jsonify(result)

@mcp_app.route('/mcp/projects/<project_name>/context', methods=['GET'])
def get_project_context(project_name):
    """Get project context"""
    result = mcp_server.get_project_context(project_name)
    return jsonify(result)

@mcp_app.route('/mcp/projects/<project_name>/files', methods=['POST'])
def create_file(project_name):
    """Create a file in project"""
    data = request.get_json()
    result = mcp_server.create_file(
        project_name=project_name,
        file_path=data.get('file_path'),
        content=data.get('content', '')
    )
    return jsonify(result)

@mcp_app.route('/mcp/projects/<project_name>/files/<path:file_path>', methods=['GET'])
def read_file(project_name, file_path):
    """Read a file from project"""
    result = mcp_server.read_file(project_name, file_path)
    return jsonify(result)

@mcp_app.route('/mcp/projects/<project_name>/generate', methods=['POST'])
def generate_code(project_name):
    """Generate code with context"""
    data = request.get_json()
    result = mcp_server.generate_code_with_context(
        project_name=project_name,
        prompt=data.get('prompt'),
        target_file=data.get('target_file')
    )
    return jsonify(result)

@mcp_app.route('/mcp/projects/<project_name>/auto-generate', methods=['POST'])
def auto_generate_files(project_name):
    """
    Automatically generate and create files based on prompt
    Creates plan and executes it, returning created files
    """
    data = request.get_json()
    result = mcp_server.auto_generate_files(
        project_name=project_name,
        prompt=data.get('prompt')
    )
    return jsonify(result)

@mcp_app.route('/mcp/projects/<project_name>/build-summary', methods=['GET'])
def get_build_summary(project_name):
    """
    Get comprehensive project build summary
    Similar to VS Code/Cursor summary display
    """
    try:
        context = mcp_server.get_project_context(project_name)
        
        if not context['success']:
            return jsonify(context)
        
        # Analyze project
        total_files = len(context['files'])
        total_lines = 0
        file_types = {}
        
        project_path = mcp_server.projects_dir / project_name
        
        for file_path in context['files']:
            full_path = project_path / file_path
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                    total_lines += lines
                    
                    ext = file_path.split('.')[-1] if '.' in file_path else 'other'
                    file_types[ext] = file_types.get(ext, 0) + 1
            except:
                pass
        
        # Get folder structure
        folders = set()
        for file_path in context['files']:
            parts = file_path.split('/')
            for i in range(len(parts) - 1):
                folder_path = '/'.join(parts[:i+1])
                folders.add(folder_path)
        
        return jsonify({
            'success': True,
            'project_name': project_name,
            'summary': {
                'total_files': total_files,
                'total_lines': total_lines,
                'total_folders': len(folders),
                'file_types': file_types,
                'folders': sorted(list(folders))
            },
            'files': context['files']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


if __name__ == '__main__':
    print("=" * 60)
    print("🔧 Model Context Protocol (MCP) Server")
    print("=" * 60)
    print("Provides context and capabilities to LLMs")
    print(f"Projects Directory: {PROJECTS_DIR.absolute()}")
    print("")
    print("Starting server on http://0.0.0.0:8091")
    print("=" * 60)
    
    mcp_app.run(host='0.0.0.0', port=8091, debug=True)

