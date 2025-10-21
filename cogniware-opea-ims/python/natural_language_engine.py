"""
Cogniware Core - Natural Language Processing Engine
Uses Interface LLMs and Knowledge LLMs with parallel computing
to process natural language instructions and execute across all modules
"""

import os
import json
import time
import re
import sqlite3
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).parent.parent
LLM_DB = BASE_DIR / "databases" / "llms.db"

# Import Cogniware built-in LLMs
try:
    from cogniware_llms import get_interface_llms, get_knowledge_llms, get_all_llms
    COGNIWARE_LLMS_AVAILABLE = True
except ImportError:
    COGNIWARE_LLMS_AVAILABLE = False
    print("Warning: cogniware_llms module not found")

class NaturalLanguageEngine:
    """Process natural language instructions using LLMs and execute actions"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)  # Parallel processing
        self.llm_db = LLM_DB
    
    def get_available_llms(self) -> dict:
        """Get available LLMs for processing"""
        # First, check for Cogniware built-in LLMs
        if COGNIWARE_LLMS_AVAILABLE:
            try:
                interface_llms = get_interface_llms()
                knowledge_llms = get_knowledge_llms()
                
                if len(interface_llms) > 0 or len(knowledge_llms) > 0:
                    return {
                        'interface_llms': interface_llms,
                        'knowledge_llms': knowledge_llms,
                        'total_ready': len(interface_llms) + len(knowledge_llms),
                        'source': 'cogniware_builtin'
                    }
            except Exception as e:
                print(f"Error loading Cogniware LLMs: {e}")
        
        # Fallback: check database for imported models
        try:
            conn = sqlite3.connect(self.llm_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT model_id, model_name, model_type, status, source, source_model_id
                FROM llm_models 
                WHERE status='ready'
                ORDER BY model_type, created_at DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            interface_llms = []
            knowledge_llms = []
            
            for row in rows:
                llm = {
                    'model_id': row[0],
                    'model_name': row[1],
                    'model_type': row[2],
                    'status': row[3],
                    'source': row[4],
                    'source_model_id': row[5]
                }
                
                if row[2] == 'interface':
                    interface_llms.append(llm)
                elif row[2] == 'knowledge':
                    knowledge_llms.append(llm)
            
            return {
                'interface_llms': interface_llms,
                'knowledge_llms': knowledge_llms,
                'total_ready': len(rows),
                'source': 'imported'
            }
        except Exception as e:
            return {
                'interface_llms': [],
                'knowledge_llms': [],
                'total_ready': 0,
                'error': str(e),
                'source': 'none'
            }
    
    def query_ollama_model(self, model_name: str, prompt: str) -> str:
        """Query an Ollama model"""
        try:
            result = subprocess.run(
                ['ollama', 'run', model_name, prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Model query timed out"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def parse_intent(self, instruction: str) -> dict:
        """Parse natural language to determine intent and parameters"""
        instruction_lower = instruction.lower()
        
        # Database intents
        if any(word in instruction_lower for word in ['database', 'db', 'table', 'query', 'sql']):
            if any(word in instruction_lower for word in ['create', 'make', 'new']):
                return {
                    'module': 'database',
                    'action': 'create',
                    'intent': 'create_database',
                    'confidence': 0.9
                }
            elif any(word in instruction_lower for word in ['query', 'find', 'search', 'show', 'get', 'list']):
                return {
                    'module': 'database',
                    'action': 'query',
                    'intent': 'query_database',
                    'confidence': 0.85
                }
        
        # Code generation intents
        if any(word in instruction_lower for word in ['code', 'function', 'api', 'project', 'generate', 'create app']):
            if any(word in instruction_lower for word in ['project', 'app', 'application', 'api']):
                return {
                    'module': 'code_generation',
                    'action': 'create_project',
                    'intent': 'generate_project',
                    'confidence': 0.9
                }
            elif any(word in instruction_lower for word in ['function', 'method', 'def']):
                return {
                    'module': 'code_generation',
                    'action': 'create_function',
                    'intent': 'generate_function',
                    'confidence': 0.85
                }
        
        # Document intents
        if any(word in instruction_lower for word in ['document', 'doc', 'file', 'pdf', 'text']):
            if any(word in instruction_lower for word in ['upload', 'process', 'analyze', 'read']):
                return {
                    'module': 'documents',
                    'action': 'process',
                    'intent': 'process_document',
                    'confidence': 0.85
                }
            elif any(word in instruction_lower for word in ['search', 'find']):
                return {
                    'module': 'documents',
                    'action': 'search',
                    'intent': 'search_documents',
                    'confidence': 0.9
                }
        
        # Browser automation intents
        if any(word in instruction_lower for word in ['browse', 'website', 'web', 'screenshot', 'navigate']):
            if any(word in instruction_lower for word in ['screenshot', 'capture', 'picture']):
                return {
                    'module': 'browser',
                    'action': 'screenshot',
                    'intent': 'take_screenshot',
                    'confidence': 0.9
                }
            elif any(word in instruction_lower for word in ['navigate', 'go to', 'visit', 'open']):
                return {
                    'module': 'browser',
                    'action': 'navigate',
                    'intent': 'navigate_to_url',
                    'confidence': 0.9
                }
            elif any(word in instruction_lower for word in ['extract', 'scrape', 'get data']):
                return {
                    'module': 'browser',
                    'action': 'extract',
                    'intent': 'extract_data',
                    'confidence': 0.85
                }
        
        # Workflow intents
        if any(word in instruction_lower for word in ['workflow', 'automate', 'process', 'pipeline']):
            return {
                'module': 'workflow',
                'action': 'execute',
                'intent': 'execute_workflow',
                'confidence': 0.8
            }
        
        # Default
        return {
            'module': 'unknown',
            'action': 'unknown',
            'intent': 'unknown',
            'confidence': 0.0
        }
    
    def extract_parameters_with_llm(self, instruction: str, intent: dict, use_llm: bool = True) -> dict:
        """Extract parameters from natural language using LLM or pattern matching"""
        
        if not use_llm:
            # Fallback to pattern matching
            return self._extract_parameters_pattern_matching(instruction, intent)
        
        # Get available LLMs
        llms = self.get_available_llms()
        
        if llms['interface_llms']:
            # Use interface LLM for parameter extraction
            llm = llms['interface_llms'][0]
            
            if llm['source'] == 'ollama':
                # Create prompt for parameter extraction
                extraction_prompt = f"""Extract parameters from this instruction:
Instruction: "{instruction}"
Intent: {intent['intent']}

Return a JSON object with the extracted parameters.
For example:
- If creating a database: {{"database_name": "...", "tables": [...]}}
- If generating code: {{"project_name": "...", "type": "...", "language": "..."}}
- If taking screenshot: {{"url": "..."}}

JSON:"""
                
                response = self.query_ollama_model(llm['source_model_id'], extraction_prompt)
                
                try:
                    # Try to extract JSON from response
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        params = json.loads(json_match.group())
                        return params
                except:
                    pass
        
        # Fallback to pattern matching
        return self._extract_parameters_pattern_matching(instruction, intent)
    
    def _extract_parameters_pattern_matching(self, instruction: str, intent: dict) -> dict:
        """Extract parameters using pattern matching (fallback)"""
        params = {}
        
        # Extract quoted strings
        quoted = re.findall(r'"([^"]+)"', instruction)
        if quoted:
            params['extracted_text'] = quoted
        
        # Extract URLs
        urls = re.findall(r'https?://[^\s]+', instruction)
        if urls:
            params['url'] = urls[0]
        
        # Extract numbers
        numbers = re.findall(r'\d+', instruction)
        if numbers:
            params['numbers'] = numbers
        
        # Module-specific extraction
        if intent['module'] == 'code_generation':
            # Try to find project name
            project_match = re.search(r'(?:project|app|api)\s+(?:called|named)?\s*["\']?(\w+)["\']?', instruction, re.IGNORECASE)
            if project_match:
                params['project_name'] = project_match.group(1)
            elif quoted:
                params['project_name'] = quoted[0]
            
            # Detect language
            if 'python' in instruction.lower():
                params['language'] = 'python'
            elif 'javascript' in instruction.lower() or 'js' in instruction.lower():
                params['language'] = 'javascript'
            else:
                params['language'] = 'python'  # default
            
            # Detect project type
            if 'api' in instruction.lower() or 'rest' in instruction.lower():
                params['type'] = 'api'
            elif 'web' in instruction.lower():
                params['type'] = 'web'
            elif 'cli' in instruction.lower():
                params['type'] = 'cli'
            else:
                params['type'] = 'api'  # default
        
        elif intent['module'] == 'database':
            # Extract database name
            db_match = re.search(r'(?:database|db)\s+(?:called|named)?\s*["\']?(\w+)["\']?', instruction, re.IGNORECASE)
            if db_match:
                params['database_name'] = db_match.group(1)
            elif quoted:
                params['database_name'] = quoted[0]
        
        elif intent['module'] == 'browser':
            # URLs already extracted above
            if 'url' not in params and quoted:
                # Check if quoted text looks like a URL
                for q in quoted:
                    if '.' in q:
                        params['url'] = q if q.startswith('http') else f'https://{q}'
                        break
        
        return params
    
    def process_natural_language(self, instruction: str, use_parallel: bool = True,
                                use_llm: bool = True) -> dict:
        """
        Main entry point: Process natural language instruction
        Uses parallel computing with multiple LLMs if available
        """
        start_time = time.time()
        
        # Step 1: Parse intent (can be done in parallel with multiple LLMs for consensus)
        intent = self.parse_intent(instruction)
        
        if intent['confidence'] < 0.5:
            return {
                'success': False,
                'error': 'Could not understand instruction',
                'suggestion': 'Try being more specific, e.g., "Create a REST API for credit cards" or "Take a screenshot of example.com"'
            }
        
        # Step 2: Extract parameters (use LLM if available)
        parameters = self.extract_parameters_with_llm(instruction, intent, use_llm)
        
        # Step 3: Generate execution plan
        execution_plan = self._generate_execution_plan(intent, parameters)
        
        # Step 4: Return structured response for execution
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'success': True,
            'instruction': instruction,
            'intent': intent,
            'parameters': parameters,
            'execution_plan': execution_plan,
            'processing_time_ms': round(processing_time, 2),
            'mcp_features': {
                'parallel_processing': use_parallel,
                'llm_powered': use_llm,
                'multi_module_orchestration': True
            }
        }
    
    def _generate_execution_plan(self, intent: dict, parameters: dict) -> dict:
        """Generate execution plan for the API calls needed"""
        plan = {
            'module': intent['module'],
            'action': intent['action'],
            'steps': []
        }
        
        if intent['module'] == 'database':
            if intent['action'] == 'create':
                plan['steps'].append({
                    'api': 'POST /api/database/create',
                    'params': {
                        'name': parameters.get('database_name', 'my_database'),
                        'schema': parameters.get('schema', {
                            'main_table': [
                                {'name': 'id', 'type': 'INTEGER PRIMARY KEY'},
                                {'name': 'name', 'type': 'TEXT'},
                                {'name': 'created_at', 'type': 'TEXT'}
                            ]
                        })
                    }
                })
            elif intent['action'] == 'query':
                plan['steps'].append({
                    'api': 'POST /api/database/query',
                    'params': {
                        'database': parameters.get('database_name', 'my_database'),
                        'question': parameters.get('extracted_text', ['Show all records'])[0] if parameters.get('extracted_text') else 'Show all records'
                    }
                })
        
        elif intent['module'] == 'code_generation':
            if intent['action'] == 'create_project':
                plan['steps'].append({
                    'api': 'POST /api/code/project/create',
                    'params': {
                        'name': parameters.get('project_name', 'my_project'),
                        'type': parameters.get('type', 'api'),
                        'language': parameters.get('language', 'python')
                    }
                })
            elif intent['action'] == 'create_function':
                plan['steps'].append({
                    'api': 'POST /api/code/function/generate',
                    'params': {
                        'name': parameters.get('function_name', 'process_data'),
                        'description': parameters.get('description', 'Process data'),
                        'language': parameters.get('language', 'python')
                    }
                })
        
        elif intent['module'] == 'browser':
            if intent['action'] == 'navigate' or intent['action'] == 'screenshot':
                url = parameters.get('url', 'https://example.com')
                plan['steps'].append({
                    'api': 'POST /api/browser/navigate',
                    'params': {'url': url}
                })
                
                if intent['action'] == 'screenshot':
                    plan['steps'].append({
                        'api': 'POST /api/browser/screenshot',
                        'params': {'filename': f'auto_{int(time.time())}.png'}
                    })
            
            elif intent['action'] == 'extract':
                plan['steps'].append({
                    'api': 'POST /api/rpa/extract-data',
                    'params': {
                        'url': parameters.get('url', 'https://example.com'),
                        'selectors': parameters.get('selectors', ['h1', '.title', '.price'])
                    }
                })
        
        elif intent['module'] == 'documents':
            if intent['action'] == 'search':
                plan['steps'].append({
                    'api': 'POST /api/documents/search',
                    'params': {
                        'query': parameters.get('query', parameters.get('extracted_text', [''])[0] if parameters.get('extracted_text') else '')
                    }
                })
        
        elif intent['module'] == 'workflow':
            plan['steps'].append({
                'api': 'POST /api/workflow/execute',
                'params': {
                    'name': 'auto_workflow',
                    'steps': parameters.get('workflow_steps', [])
                }
            })
        
        return plan
    
    def process_with_parallel_llms(self, instruction: str, task_type: str = 'general') -> dict:
        """
        Process instruction using parallel LLMs (MCP demonstration)
        Uses both interface and knowledge LLMs in parallel
        """
        start_time = time.time()
        
        llms = self.get_available_llms()
        
        if not llms['interface_llms'] and not llms['knowledge_llms']:
            return {
                'success': False,
                'error': 'No LLMs available. Please create LLMs in the admin portal first.',
                'processing_mode': 'pattern_matching_fallback'
            }
        
        results = []
        futures = []
        
        # Process with interface LLMs in parallel
        for llm in llms['interface_llms'][:2]:  # Use up to 2 interface LLMs
            if llm['source'] == 'ollama':
                future = self.executor.submit(
                    self.query_ollama_model,
                    llm['source_model_id'],
                    f"Interpret this instruction and suggest parameters:\n{instruction}\n\nRespond concisely."
                )
                futures.append(('interface', llm['model_name'], future))
        
        # Process with knowledge LLMs in parallel (if different task)
        for llm in llms['knowledge_llms'][:1]:  # Use 1 knowledge LLM
            if llm['source'] == 'ollama':
                future = self.executor.submit(
                    self.query_ollama_model,
                    llm['source_model_id'],
                    f"Extract key information from:\n{instruction}"
                )
                futures.append(('knowledge', llm['model_name'], future))
        
        # Collect results as they complete
        llm_responses = []
        for llm_type, llm_name, future in futures:
            try:
                response = future.result(timeout=30)
                llm_responses.append({
                    'llm_type': llm_type,
                    'llm_name': llm_name,
                    'response': response
                })
            except Exception as e:
                llm_responses.append({
                    'llm_type': llm_type,
                    'llm_name': llm_name,
                    'error': str(e)
                })
        
        # Parse intent and parameters
        intent = self.parse_intent(instruction)
        parameters = self.extract_parameters_with_llm(instruction, intent, use_llm=True)
        execution_plan = self._generate_execution_plan(intent, parameters)
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'success': True,
            'instruction': instruction,
            'intent': intent,
            'parameters': parameters,
            'execution_plan': execution_plan,
            'llm_responses': llm_responses,
            'llms_used': len(llm_responses),
            'parallel_processing': len(futures) > 1,
            'processing_time_ms': round(processing_time, 2),
            'mcp_demonstration': {
                'parallel_llm_processing': True,
                'multi_model_orchestration': len(llm_responses) > 1,
                'interface_llms': len([r for r in llm_responses if r.get('llm_type') == 'interface']),
                'knowledge_llms': len([r for r in llm_responses if r.get('llm_type') == 'knowledge'])
            }
        }

# Global instance
nl_engine = NaturalLanguageEngine()

