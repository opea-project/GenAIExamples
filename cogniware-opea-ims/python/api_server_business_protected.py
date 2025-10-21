#!/usr/bin/env python3
"""
Cogniware Core - Protected Business API Server
All endpoints require valid license and authentication
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

# Import authentication middleware
from auth_middleware import require_license, require_role, public_endpoint
from api_server_business import (
    DatabaseQA, CodeGenerator, DocumentProcessor,
    DataIntegration, WorkflowAutomation,
    state, PROJECTS_DIR, DATABASES_DIR, DOCUMENTS_DIR
)
from mcp_browser_automation import browser_automation
from document_processor_advanced import get_advanced_processor
from natural_language_engine import nl_engine
from cogniware_llms import get_interface_llms, get_knowledge_llms, get_all_llms
from parallel_llm_executor import execute_with_parallel_llms, get_executor_statistics

# Initialize advanced document processor
advanced_processor = get_advanced_processor(DOCUMENTS_DIR)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# =============================================================================
# PUBLIC ENDPOINTS
# =============================================================================

@app.route('/', methods=['GET'])
@public_endpoint
def root():
    """Root endpoint - public"""
    return jsonify({
        "name": "Cogniware Core - Protected Business API",
        "version": "1.0.0-protected",
        "company": "Cogniware Incorporated",
        "authentication": "Required for all endpoints",
        "auth_methods": {
            "api_key": "X-API-Key header",
            "jwt": "Authorization: Bearer <token> header"
        },
        "endpoints": {
            "login": "POST /auth/login",
            "database": "/api/database/* (requires 'database' feature)",
            "code": "/api/code/* (requires 'code_generation' feature)",
            "documents": "/api/documents/* (requires 'documents' feature)",
            "integration": "/api/integration/* (requires 'integration' feature)",
            "workflow": "/api/workflow/* (requires 'workflow' feature)"
        }
    })

@app.route('/health', methods=['GET'])
@public_endpoint
def health():
    """Health check - public"""
    return jsonify({
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "1.0.0-protected"
    })

@app.route('/status', methods=['GET'])
@require_license()
def status():
    """System status - requires auth"""
    return jsonify({
        "server": "running",
        "uptime_seconds": int(time.time() - state.start_time),
        "requests_total": state.request_count,
        "databases": len(state.databases),
        "projects": len(state.projects),
        "user": {
            "user_id": request.user_info.get('user_id'),
            "org_id": request.user_info.get('org_id'),
            "username": request.user_info.get('username')
        },
        "license": {
            "valid": True,
            "type": request.user_info.get('license_info', {}).get('license_type'),
            "expires": request.user_info.get('license_info', {}).get('expiry_date')
        }
    })

# =============================================================================
# DATABASE Q&A - Requires 'database' feature
# =============================================================================

@app.route('/api/database/create', methods=['POST'])
@require_license(features=['database'])
def create_database():
    """Create database - requires 'database' feature"""
    data = request.get_json()
    return jsonify(DatabaseQA.create_database(
        data.get('name'),
        data.get('schema', {})
    ))

@app.route('/api/database/insert', methods=['POST'])
@require_license(features=['database'])
def insert_database():
    """Insert data - requires 'database' feature"""
    data = request.get_json()
    return jsonify(DatabaseQA.insert_data(
        data.get('database'),
        data.get('table'),
        data.get('data', [])
    ))

@app.route('/api/database/query', methods=['POST'])
@require_license(features=['database'])
def query_database():
    """Natural language query - requires 'database' feature"""
    data = request.get_json()
    return jsonify(DatabaseQA.natural_language_query(
        data.get('database'),
        data.get('question')
    ))

@app.route('/api/database/analyze/<db_name>', methods=['GET'])
@require_license(features=['database'])
def analyze_database(db_name):
    """Analyze database - requires 'database' feature"""
    return jsonify(DatabaseQA.analyze_database(db_name))

# =============================================================================
# CODE GENERATION - Requires 'code_generation' feature
# =============================================================================

@app.route('/api/code/project/create', methods=['POST'])
@require_license(features=['code_generation'])
def create_project():
    """Create project - requires 'code_generation' feature"""
    data = request.get_json()
    return jsonify(CodeGenerator.create_project(
        data.get('name'),
        data.get('type', 'web'),
        data.get('language', 'python')
    ))

@app.route('/api/code/function/generate', methods=['POST'])
@require_license(features=['code_generation'])
def generate_function():
    """Generate function - requires 'code_generation' feature"""
    data = request.get_json()
    return jsonify(CodeGenerator.generate_function(
        data.get('name'),
        data.get('description'),
        data.get('language', 'python')
    ))

@app.route('/api/code/project/<project_name>/file', methods=['POST'])
@require_license(features=['code_generation'])
def create_project_file(project_name):
    """Create file in project - requires 'code_generation' feature"""
    data = request.get_json()
    return jsonify(CodeGenerator.create_file_in_project(
        project_name,
        data.get('path'),
        data.get('content', '')
    ))

@app.route('/api/code/projects', methods=['GET'])
@require_license(features=['code_generation'])
def list_projects():
    """List projects - requires 'code_generation' feature"""
    projects = [{"name": name, **info} for name, info in state.projects.items()]
    return jsonify({"success": True, "projects": projects, "count": len(projects)})

# =============================================================================
# DOCUMENT PROCESSING - Requires 'documents' feature
# =============================================================================

@app.route('/api/documents/create', methods=['POST'])
@require_license(features=['documents'])
def create_document():
    """Create document - requires 'documents' feature"""
    data = request.get_json()
    return jsonify(DocumentProcessor.create_document(
        data.get('name'),
        data.get('content'),
        data.get('type', 'text')
    ))

@app.route('/api/documents/analyze/<doc_name>', methods=['GET'])
@require_license(features=['documents'])
def analyze_document(doc_name):
    """Analyze document - requires 'documents' feature"""
    return jsonify(DocumentProcessor.analyze_document(doc_name))

@app.route('/api/documents/search', methods=['POST'])
@require_license(features=['documents'])
def search_documents():
    """Search documents - requires 'documents' feature"""
    data = request.get_json()
    return jsonify(DocumentProcessor.search_documents(data.get('query')))

@app.route('/api/documents/formats', methods=['GET'])
@require_license(features=['documents'])
def get_supported_formats():
    """Get supported document formats"""
    return jsonify(advanced_processor.get_supported_formats())

@app.route('/api/documents/upload', methods=['POST'])
@require_license(features=['documents'])
def upload_document():
    """Upload document (base64 encoded)"""
    data = request.get_json()
    return jsonify(advanced_processor.upload_document_base64(
        data.get('filename'),
        data.get('file_data'),  # base64 encoded
        data.get('type')
    ))

@app.route('/api/documents/process/<doc_name>', methods=['GET'])
@require_license(features=['documents'])
def process_document(doc_name):
    """Process uploaded document (PDF, DOCX, XLSX, PPTX, etc.)"""
    return jsonify(advanced_processor.process_document(doc_name))

@app.route('/api/documents/search-in/<doc_name>', methods=['POST'])
@require_license(features=['documents'])
def search_in_document(doc_name):
    """Search within a specific document"""
    data = request.get_json()
    return jsonify(advanced_processor.search_in_document(
        doc_name,
        data.get('query')
    ))

# =============================================================================
# DATA INTEGRATION - Requires 'integration' feature
# =============================================================================

@app.route('/api/integration/import', methods=['POST'])
@require_license(features=['integration'])
def import_from_api():
    """Import from API - requires 'integration' feature"""
    data = request.get_json()
    return jsonify(DataIntegration.import_from_api(
        data.get('api_url'),
        data.get('database'),
        data.get('table')
    ))

@app.route('/api/integration/export', methods=['POST'])
@require_license(features=['integration'])
def export_to_json():
    """Export to JSON - requires 'integration' feature"""
    data = request.get_json()
    return jsonify(DataIntegration.export_to_json(
        data.get('database'),
        data.get('table'),
        data.get('output_file')
    ))

@app.route('/api/integration/transform', methods=['POST'])
@require_license(features=['integration'])
def transform_data():
    """Transform data - requires 'integration' feature"""
    data = request.get_json()
    return jsonify(DataIntegration.transform_data(
        data.get('data', []),
        data.get('transformations', [])
    ))

# =============================================================================
# WORKFLOW AUTOMATION - Requires 'workflow' feature
# =============================================================================

@app.route('/api/workflow/execute', methods=['POST'])
@require_license(features=['workflow'])
def execute_workflow():
    """Execute workflow - requires 'workflow' feature"""
    data = request.get_json()
    return jsonify(WorkflowAutomation.execute_workflow(data))

# =============================================================================
# BROWSER AUTOMATION & RPA - Requires 'browser_automation' feature
# =============================================================================

@app.route('/api/browser/navigate', methods=['POST'])
@require_license(features=['browser_automation'])
def browser_navigate():
    """Navigate to URL - requires 'browser_automation' feature"""
    data = request.get_json()
    return jsonify(browser_automation.navigate_to(data.get('url')))

@app.route('/api/browser/screenshot', methods=['POST'])
@require_license(features=['browser_automation'])
def browser_screenshot():
    """Take screenshot - requires 'browser_automation' feature"""
    data = request.get_json()
    return jsonify(browser_automation.take_screenshot(data.get('filename')))

@app.route('/api/browser/click', methods=['POST'])
@require_license(features=['browser_automation'])
def browser_click():
    """Click element - requires 'browser_automation' feature"""
    data = request.get_json()
    return jsonify(browser_automation.click_element(
        data.get('selector'),
        data.get('by', 'css')
    ))

@app.route('/api/browser/fill', methods=['POST'])
@require_license(features=['browser_automation'])
def browser_fill():
    """Fill form field - requires 'browser_automation' feature"""
    data = request.get_json()
    return jsonify(browser_automation.fill_form(
        data.get('selector'),
        data.get('value'),
        data.get('by', 'css')
    ))

@app.route('/api/browser/extract-text', methods=['POST'])
@require_license(features=['browser_automation'])
def browser_extract_text():
    """Extract text - requires 'browser_automation' feature"""
    data = request.get_json()
    return jsonify(browser_automation.extract_text(
        data.get('selector'),
        data.get('by', 'css')
    ))

@app.route('/api/browser/extract-table', methods=['POST'])
@require_license(features=['browser_automation'])
def browser_extract_table():
    """Extract table data - requires 'browser_automation' feature"""
    data = request.get_json()
    return jsonify(browser_automation.extract_table(data.get('selector')))

@app.route('/api/browser/scroll', methods=['POST'])
@require_license(features=['browser_automation'])
def browser_scroll():
    """Scroll page - requires 'browser_automation' feature"""
    data = request.get_json()
    return jsonify(browser_automation.scroll_page(
        data.get('direction', 'down'),
        data.get('amount', 500)
    ))

@app.route('/api/browser/execute-script', methods=['POST'])
@require_license(features=['browser_automation'])
def browser_execute_script():
    """Execute JavaScript - requires 'browser_automation' feature"""
    data = request.get_json()
    return jsonify(browser_automation.execute_script(data.get('script')))

@app.route('/api/browser/close', methods=['POST'])
@require_license(features=['browser_automation'])
def browser_close():
    """Close browser - requires 'browser_automation' feature"""
    return jsonify(browser_automation.close_browser())

# RPA Workflows
@app.route('/api/rpa/login', methods=['POST'])
@require_license(features=['browser_automation', 'rpa'])
def rpa_login():
    """RPA: Automated login - requires 'browser_automation' and 'rpa' features"""
    data = request.get_json()
    return jsonify(browser_automation.rpa_login_workflow(
        data.get('url'),
        data.get('username_selector'),
        data.get('password_selector'),
        data.get('submit_selector'),
        data.get('username'),
        data.get('password')
    ))

@app.route('/api/rpa/form-fill', methods=['POST'])
@require_license(features=['browser_automation', 'rpa'])
def rpa_form_fill():
    """RPA: Fill form - requires 'browser_automation' and 'rpa' features"""
    data = request.get_json()
    return jsonify(browser_automation.rpa_form_fill_workflow(data.get('form_data', {})))

@app.route('/api/rpa/extract-data', methods=['POST'])
@require_license(features=['browser_automation', 'rpa'])
def rpa_extract_data():
    """RPA: Extract data - requires 'browser_automation' and 'rpa' features"""
    data = request.get_json()
    return jsonify(browser_automation.rpa_data_extraction_workflow(
        data.get('url'),
        data.get('selectors', [])
    ))

@app.route('/api/rpa/screenshot-batch', methods=['POST'])
@require_license(features=['browser_automation', 'rpa'])
def rpa_screenshot_batch():
    """RPA: Batch screenshots - requires 'browser_automation' and 'rpa' features"""
    data = request.get_json()
    return jsonify(browser_automation.rpa_screenshot_workflow(data.get('urls', [])))

# =============================================================================
# NATURAL LANGUAGE PROCESSING - MCP Demonstration
# =============================================================================

@app.route('/api/nl/process', methods=['POST'])
@require_license()
def process_natural_language():
    """
    Process natural language instruction using PARALLEL LLM execution
    
    PATENT IMPLEMENTATION: Multi-Context Processing (MCP)
    - Executes Interface LLMs + Knowledge LLMs in parallel
    - Synthesizes results for superior output
    """
    data = request.get_json()
    instruction = data.get('instruction', '')
    use_parallel = data.get('use_parallel', True)
    use_llm = data.get('use_llm', True)
    strategy = data.get('strategy', 'parallel')
    num_interface = data.get('num_interface_llms', 2)
    num_knowledge = data.get('num_knowledge_llms', 1)
    
    if not instruction:
        return jsonify({
            'success': False,
            'error': 'No instruction provided'
        }), 400
    
    # Use patent-compliant parallel execution
    result = execute_with_parallel_llms(
        prompt=instruction,
        strategy=strategy if use_parallel else "interface_only",
        num_interface=num_interface,
        num_knowledge=num_knowledge
    )
    
    # Add execution plan for frontend
    result['execution_plan'] = {
        'module': 'general',
        'steps': [{'description': 'Execute with parallel LLMs'}]
    }
    result['intent'] = {'module': 'general', 'action': 'process'}
    result['generated_output'] = result.pop('result', '')
    
    return jsonify(result)

@app.route('/api/nl/parse', methods=['POST'])
@require_license()
def parse_intent_only():
    """Parse intent from natural language (faster, no LLM)"""
    data = request.get_json()
    instruction = data.get('instruction', '')
    
    result = nl_engine.process_natural_language(instruction, use_parallel=False, use_llm=False)
    return jsonify(result)

@app.route('/api/nl/llms/available', methods=['GET'])
@require_license()
def get_available_llms():
    """Get available LLMs for natural language processing"""
    # Return Cogniware built-in LLMs
    interface_llms = get_interface_llms()
    knowledge_llms = get_knowledge_llms()
    
    return jsonify({
        'success': True,
        'llms': {
            'interface_llms': interface_llms,
            'knowledge_llms': knowledge_llms,
            'total': len(interface_llms) + len(knowledge_llms)
        },
        'message': f'{len(interface_llms)} interface and {len(knowledge_llms)} knowledge LLMs ready for use'
    })

# =============================================================================
# ADMIN ENDPOINTS - Requires admin role
# =============================================================================

@app.route('/api/admin/stats', methods=['GET'])
@require_role(['admin', 'super_admin'])
def get_admin_stats():
    """Get admin statistics - requires admin role"""
    return jsonify({
        "success": True,
        "stats": {
            "total_databases": len(state.databases),
            "total_projects": len(state.projects),
            "uptime_seconds": int(time.time() - state.start_time),
            "org_id": request.user_info.get('org_id')
        }
    })

# =============================================================================
# STARTUP
# =============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Cogniware Core - Protected Business API Server")
    print("=" * 70)
    print("Features:")
    print("  ✅ License validation on all endpoints")
    print("  ✅ Feature-based access control")
    print("  ✅ Role-based permissions")
    print("  ✅ API usage tracking")
    print("  ✅ Online/offline license validation")
    print("  ✅ Browser Automation & RPA (NEW!)")
    print("  ✅ Chrome automation & screen capture")
    print("")
    print("Available Modules:")
    print("  • Database Q&A")
    print("  • Code Generation")
    print("  • Document Processing")
    print("  • Data Integration & ETL")
    print("  • Workflow Automation")
    print("  • Browser Automation & RPA")
    print("")
    print("Authentication Methods:")
    print("  • API Key: X-API-Key: cw_xxxxx")
    print("  • JWT Token: Authorization: Bearer <token>")
    print("")
    print("Starting server on http://0.0.0.0:8096")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=8096, debug=True)

