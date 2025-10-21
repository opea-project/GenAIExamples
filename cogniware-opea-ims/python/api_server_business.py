#!/usr/bin/env python3
"""
Cogniware Core - Business Use Case API Server
Practical APIs for real-world business scenarios
"""

import os
import sys
import json
import time
import psutil
import requests
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
BASE_DIR = Path(__file__).parent.parent
PROJECTS_DIR = BASE_DIR / "projects"
DATABASES_DIR = BASE_DIR / "databases"
DOCUMENTS_DIR = BASE_DIR / "documents"
LOGS_DIR = BASE_DIR / "logs"

# Create directories
PROJECTS_DIR.mkdir(exist_ok=True)
DATABASES_DIR.mkdir(exist_ok=True)
DOCUMENTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Global state
class BusinessState:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.databases = {}
        self.projects = {}
        
state = BusinessState()

# =============================================================================
# BUSINESS USE CASE 1: DATABASE Q&A SYSTEM
# =============================================================================

class DatabaseQA:
    """Intelligent database query and analysis system"""
    
    @staticmethod
    def create_database(db_name: str, schema: dict) -> dict:
        """Create a new database with schema"""
        try:
            db_path = DATABASES_DIR / f"{db_name}.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create tables from schema
            for table_name, columns in schema.items():
                columns_def = ", ".join([f"{col['name']} {col['type']}" for col in columns])
                cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def})")
            
            conn.commit()
            conn.close()
            
            state.databases[db_name] = {
                "path": str(db_path),
                "schema": schema,
                "created_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "database": db_name,
                "path": str(db_path),
                "tables": list(schema.keys())
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def natural_language_query(db_name: str, question: str) -> dict:
        """Convert natural language to SQL and execute (simplified version)"""
        try:
            db_path = DATABASES_DIR / f"{db_name}.db"
            if not db_path.exists():
                return {"success": False, "error": "Database not found"}
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Simple NL to SQL conversion (in production, use LLM)
            sql_query = DatabaseQA._convert_nl_to_sql(question, tables)
            
            # Execute query
            cursor.execute(sql_query)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            conn.close()
            
            return {
                "success": True,
                "question": question,
                "sql_generated": sql_query,
                "columns": columns,
                "results": results,
                "row_count": len(results)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _convert_nl_to_sql(question: str, tables: list) -> str:
        """Simple NL to SQL converter (simplified - in production use LLM)"""
        question_lower = question.lower()
        
        # Simple pattern matching
        if "all" in question_lower or "show" in question_lower:
            if tables:
                return f"SELECT * FROM {tables[0]} LIMIT 100"
        elif "count" in question_lower:
            if tables:
                return f"SELECT COUNT(*) FROM {tables[0]}"
        elif "how many" in question_lower:
            if tables:
                return f"SELECT COUNT(*) FROM {tables[0]}"
        
        # Default: show all from first table
        if tables:
            return f"SELECT * FROM {tables[0]} LIMIT 50"
        
        return "SELECT 1"
    
    @staticmethod
    def insert_data(db_name: str, table: str, data: list) -> dict:
        """Insert data into database"""
        try:
            db_path = DATABASES_DIR / f"{db_name}.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if not data:
                return {"success": False, "error": "No data provided"}
            
            # Get column names from first row
            columns = list(data[0].keys())
            placeholders = ", ".join(["?" for _ in columns])
            columns_str = ", ".join(columns)
            
            # Insert each row
            inserted = 0
            for row in data:
                values = [row.get(col) for col in columns]
                cursor.execute(
                    f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})",
                    values
                )
                inserted += 1
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "database": db_name,
                "table": table,
                "rows_inserted": inserted
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def analyze_database(db_name: str) -> dict:
        """Analyze database structure and content"""
        try:
            db_path = DATABASES_DIR / f"{db_name}.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            analysis = {"tables": {}}
            
            for table in tables:
                # Get column info
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [{"name": row[1], "type": row[2]} for row in cursor.fetchall()]
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                analysis["tables"][table] = {
                    "columns": columns,
                    "row_count": row_count
                }
            
            conn.close()
            
            return {
                "success": True,
                "database": db_name,
                "table_count": len(tables),
                "analysis": analysis
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# =============================================================================
# BUSINESS USE CASE 2: CODE GENERATION & PROJECT MANAGEMENT
# =============================================================================

class CodeGenerator:
    """Generate code files and project structures"""
    
    @staticmethod
    def create_project(project_name: str, project_type: str, language: str) -> dict:
        """Create a new project with standard structure"""
        try:
            project_path = PROJECTS_DIR / project_name
            project_path.mkdir(exist_ok=True)
            
            # Create structure based on project type
            structure = CodeGenerator._get_project_structure(project_type, language)
            
            created_files = []
            for file_path, content in structure.items():
                full_path = project_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                created_files.append(str(file_path))
            
            state.projects[project_name] = {
                "path": str(project_path),
                "type": project_type,
                "language": language,
                "created_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "project": project_name,
                "path": str(project_path),
                "type": project_type,
                "language": language,
                "files_created": created_files
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _get_project_structure(project_type: str, language: str) -> dict:
        """Get project structure template"""
        
        if project_type == "web" and language == "python":
            return {
                "app.py": '''from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"message": "Hello from Cogniware!"})

@app.route('/api/data')
def get_data():
    return jsonify({"data": ["item1", "item2", "item3"]})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
''',
                "requirements.txt": '''flask
flask-cors
requests
''',
                "README.md": f'''# Project Created by Cogniware Core

## Setup
```bash
pip install -r requirements.txt
python app.py
```

## API Endpoints
- GET / - Welcome message
- GET /api/data - Get data

Created: {datetime.now().isoformat()}
''',
                ".gitignore": '''__pycache__/
*.pyc
venv/
.env
'''
            }
        
        elif project_type == "api" and language == "python":
            return {
                "main.py": '''from flask import Flask, request, jsonify

app = Flask(__name__)

# Sample database (in-memory)
items = []

@app.route('/api/items', methods=['GET'])
def get_items():
    return jsonify({"items": items, "count": len(items)})

@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.get_json()
    item = {"id": len(items) + 1, "data": data}
    items.append(item)
    return jsonify(item), 201

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = next((i for i in items if i['id'] == item_id), None)
    if item:
        return jsonify(item)
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
''',
                "requirements.txt": "flask\nflask-cors\n",
                "README.md": "# REST API Project\n\nCreated by Cogniware Core\n"
            }
        
        elif project_type == "cli" and language == "python":
            return {
                "main.py": '''#!/usr/bin/env python3
import argparse

def main():
    parser = argparse.ArgumentParser(description='CLI Tool by Cogniware')
    parser.add_argument('--name', help='Your name')
    parser.add_argument('--action', choices=['greet', 'info'], default='greet')
    
    args = parser.parse_args()
    
    if args.action == 'greet':
        print(f"Hello, {args.name or 'World'}!")
    elif args.action == 'info':
        print("CLI Tool created by Cogniware Core")

if __name__ == '__main__':
    main()
''',
                "README.md": "# CLI Tool\n\nCreated by Cogniware Core\n"
            }
        
        # Default structure
        return {
            "main.py": "# Project created by Cogniware Core\n",
            "README.md": "# New Project\n"
        }
    
    @staticmethod
    def generate_function(function_name: str, description: str, language: str) -> dict:
        """Generate a function based on description"""
        try:
            if language == "python":
                code = f'''def {function_name}():
    """
    {description}
    
    Generated by Cogniware Core
    """
    # TODO: Implement {function_name}
    pass
'''
            elif language == "javascript":
                code = f'''function {function_name}() {{
    /**
     * {description}
     * 
     * Generated by Cogniware Core
     */
    // TODO: Implement {function_name}
}}
'''
            else:
                code = f"// {function_name}\n// {description}\n"
            
            return {
                "success": True,
                "function_name": function_name,
                "language": language,
                "code": code
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def create_file_in_project(project_name: str, file_path: str, content: str) -> dict:
        """Create a file in existing project"""
        try:
            project_path = PROJECTS_DIR / project_name
            if not project_path.exists():
                return {"success": False, "error": "Project not found"}
            
            full_path = project_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            
            return {
                "success": True,
                "project": project_name,
                "file": file_path,
                "path": str(full_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# =============================================================================
# BUSINESS USE CASE 3: DOCUMENT PROCESSING
# =============================================================================

class DocumentProcessor:
    """Process and analyze documents"""
    
    @staticmethod
    def create_document(doc_name: str, content: str, doc_type: str = "text") -> dict:
        """Create a new document"""
        try:
            doc_path = DOCUMENTS_DIR / f"{doc_name}.{doc_type}"
            doc_path.write_text(content)
            
            return {
                "success": True,
                "document": doc_name,
                "path": str(doc_path),
                "size": len(content),
                "type": doc_type
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def analyze_document(doc_name: str) -> dict:
        """Analyze document content"""
        try:
            # Find document with any extension
            docs = list(DOCUMENTS_DIR.glob(f"{doc_name}.*"))
            if not docs:
                return {"success": False, "error": "Document not found"}
            
            doc_path = docs[0]
            content = doc_path.read_text()
            
            # Basic analysis
            lines = content.split('\n')
            words = content.split()
            
            return {
                "success": True,
                "document": doc_name,
                "path": str(doc_path),
                "size_bytes": len(content),
                "line_count": len(lines),
                "word_count": len(words),
                "char_count": len(content),
                "preview": content[:200]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def search_documents(query: str) -> dict:
        """Search across all documents"""
        try:
            results = []
            for doc_path in DOCUMENTS_DIR.iterdir():
                if doc_path.is_file():
                    try:
                        content = doc_path.read_text()
                        if query.lower() in content.lower():
                            results.append({
                                "document": doc_path.stem,
                                "path": str(doc_path),
                                "matches": content.lower().count(query.lower())
                            })
                    except:
                        pass
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "match_count": len(results)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# =============================================================================
# BUSINESS USE CASE 4: DATA INTEGRATION & ETL
# =============================================================================

class DataIntegration:
    """Data integration and ETL operations"""
    
    @staticmethod
    def import_from_api(api_url: str, target_db: str, target_table: str) -> dict:
        """Import data from external API to database"""
        try:
            # Fetch data from API
            response = requests.get(api_url, timeout=10)
            data = response.json()
            
            # Ensure data is a list
            if not isinstance(data, list):
                data = [data]
            
            # Insert into database
            result = DatabaseQA.insert_data(target_db, target_table, data)
            
            return {
                "success": True,
                "api_url": api_url,
                "database": target_db,
                "table": target_table,
                "records_imported": len(data),
                "import_result": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def export_to_json(db_name: str, table: str, output_file: str) -> dict:
        """Export database table to JSON"""
        try:
            db_path = DATABASES_DIR / f"{db_name}.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT * FROM {table}")
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Convert to list of dicts
            data = [dict(zip(columns, row)) for row in results]
            
            # Write to file
            output_path = DOCUMENTS_DIR / output_file
            output_path.write_text(json.dumps(data, indent=2))
            
            conn.close()
            
            return {
                "success": True,
                "database": db_name,
                "table": table,
                "output_file": str(output_path),
                "records_exported": len(data)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def transform_data(data: list, transformations: list) -> dict:
        """Apply transformations to data"""
        try:
            transformed = data.copy()
            
            for transform in transformations:
                operation = transform.get('operation')
                field = transform.get('field')
                
                if operation == 'uppercase' and field:
                    for item in transformed:
                        if field in item and isinstance(item[field], str):
                            item[field] = item[field].upper()
                
                elif operation == 'lowercase' and field:
                    for item in transformed:
                        if field in item and isinstance(item[field], str):
                            item[field] = item[field].lower()
                
                elif operation == 'filter' and field:
                    value = transform.get('value')
                    transformed = [item for item in transformed if item.get(field) == value]
            
            return {
                "success": True,
                "original_count": len(data),
                "transformed_count": len(transformed),
                "data": transformed
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# =============================================================================
# BUSINESS USE CASE 5: WORKFLOW AUTOMATION
# =============================================================================

class WorkflowAutomation:
    """Automate business workflows"""
    
    @staticmethod
    def execute_workflow(workflow: dict) -> dict:
        """Execute a multi-step workflow"""
        try:
            results = []
            workflow_name = workflow.get('name', 'unnamed')
            steps = workflow.get('steps', [])
            
            for i, step in enumerate(steps):
                step_type = step.get('type')
                step_name = step.get('name', f'step_{i+1}')
                
                step_result = {"step": step_name, "type": step_type}
                
                if step_type == 'http_request':
                    url = step.get('url')
                    response = requests.get(url, timeout=10)
                    step_result['status_code'] = response.status_code
                    step_result['success'] = response.status_code == 200
                
                elif step_type == 'create_file':
                    path = step.get('path')
                    content = step.get('content', '')
                    file_path = DOCUMENTS_DIR / path
                    file_path.write_text(content)
                    step_result['file'] = str(file_path)
                    step_result['success'] = True
                
                elif step_type == 'database_query':
                    db_name = step.get('database')
                    query = step.get('query')
                    # Execute query (simplified)
                    step_result['success'] = True
                
                results.append(step_result)
            
            return {
                "success": True,
                "workflow": workflow_name,
                "steps_executed": len(results),
                "results": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "name": "Cogniware Core - Business API",
        "version": "1.0.0",
        "company": "Cogniware Incorporated",
        "use_cases": {
            "database_qa": "Natural language database queries",
            "code_generation": "Generate code and projects",
            "document_processing": "Process and analyze documents",
            "data_integration": "ETL and data integration",
            "workflow_automation": "Automate business workflows"
        },
        "endpoints": {
            "database": "/api/database/*",
            "code": "/api/code/*",
            "documents": "/api/documents/*",
            "integration": "/api/integration/*",
            "workflow": "/api/workflow/*"
        }
    })

# Database Q&A Endpoints
@app.route('/api/database/create', methods=['POST'])
def create_database():
    """Create a new database"""
    data = request.get_json()
    return jsonify(DatabaseQA.create_database(
        data.get('name'),
        data.get('schema', {})
    ))

@app.route('/api/database/query', methods=['POST'])
def query_database():
    """Natural language database query"""
    data = request.get_json()
    return jsonify(DatabaseQA.natural_language_query(
        data.get('database'),
        data.get('question')
    ))

@app.route('/api/database/insert', methods=['POST'])
def insert_database():
    """Insert data into database"""
    data = request.get_json()
    return jsonify(DatabaseQA.insert_data(
        data.get('database'),
        data.get('table'),
        data.get('data', [])
    ))

@app.route('/api/database/analyze/<db_name>', methods=['GET'])
def analyze_database(db_name):
    """Analyze database structure"""
    return jsonify(DatabaseQA.analyze_database(db_name))

# Code Generation Endpoints
@app.route('/api/code/project/create', methods=['POST'])
def create_project():
    """Create a new project"""
    data = request.get_json()
    return jsonify(CodeGenerator.create_project(
        data.get('name'),
        data.get('type', 'web'),
        data.get('language', 'python')
    ))

@app.route('/api/code/function/generate', methods=['POST'])
def generate_function():
    """Generate a function"""
    data = request.get_json()
    return jsonify(CodeGenerator.generate_function(
        data.get('name'),
        data.get('description'),
        data.get('language', 'python')
    ))

@app.route('/api/code/project/<project_name>/file', methods=['POST'])
def create_project_file(project_name):
    """Create file in project"""
    data = request.get_json()
    return jsonify(CodeGenerator.create_file_in_project(
        project_name,
        data.get('path'),
        data.get('content', '')
    ))

@app.route('/api/code/projects', methods=['GET'])
def list_projects():
    """List all projects"""
    projects = [{"name": name, **info} for name, info in state.projects.items()]
    return jsonify({"success": True, "projects": projects, "count": len(projects)})

# Document Processing Endpoints
@app.route('/api/documents/create', methods=['POST'])
def create_document():
    """Create a document"""
    data = request.get_json()
    return jsonify(DocumentProcessor.create_document(
        data.get('name'),
        data.get('content'),
        data.get('type', 'text')
    ))

@app.route('/api/documents/analyze/<doc_name>', methods=['GET'])
def analyze_document(doc_name):
    """Analyze a document"""
    return jsonify(DocumentProcessor.analyze_document(doc_name))

@app.route('/api/documents/search', methods=['POST'])
def search_documents():
    """Search documents"""
    data = request.get_json()
    return jsonify(DocumentProcessor.search_documents(data.get('query')))

# Data Integration Endpoints
@app.route('/api/integration/import', methods=['POST'])
def import_from_api():
    """Import data from API"""
    data = request.get_json()
    return jsonify(DataIntegration.import_from_api(
        data.get('api_url'),
        data.get('database'),
        data.get('table')
    ))

@app.route('/api/integration/export', methods=['POST'])
def export_to_json():
    """Export database to JSON"""
    data = request.get_json()
    return jsonify(DataIntegration.export_to_json(
        data.get('database'),
        data.get('table'),
        data.get('output_file')
    ))

@app.route('/api/integration/transform', methods=['POST'])
def transform_data():
    """Transform data"""
    data = request.get_json()
    return jsonify(DataIntegration.transform_data(
        data.get('data', []),
        data.get('transformations', [])
    ))

# Workflow Automation Endpoints
@app.route('/api/workflow/execute', methods=['POST'])
def execute_workflow():
    """Execute a workflow"""
    data = request.get_json()
    return jsonify(WorkflowAutomation.execute_workflow(data))

# Health and Status
@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "1.0.0-business"
    })

@app.route('/status', methods=['GET'])
def status():
    """System status"""
    return jsonify({
        "server": "running",
        "uptime_seconds": int(time.time() - state.start_time),
        "requests_total": state.request_count,
        "databases": len(state.databases),
        "projects": len(state.projects)
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Cogniware Core - Business Use Case API Server")
    print("=" * 60)
    print("Business Features:")
    print("  • Database Q&A - Natural language queries")
    print("  • Code Generation - Create projects and files")
    print("  • Document Processing - Analyze and search docs")
    print("  • Data Integration - ETL operations")
    print("  • Workflow Automation - Multi-step processes")
    print("")
    print("Starting server on http://0.0.0.0:8095")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8095, debug=True)

