#!/usr/bin/env python3
"""
Cogniware Core - LLM Manager
Manage interface LLMs, knowledge LLMs, and model downloads from Ollama/HuggingFace
"""

import os
import json
import time
import sqlite3
import requests
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"
LLM_DB = BASE_DIR / "databases" / "llms.db"

MODELS_DIR.mkdir(exist_ok=True)

class LLMManager:
    """Manage LLM models - download, configure, and monitor"""
    
    def __init__(self):
        self.db_path = LLM_DB
        self.models_dir = MODELS_DIR
        self.download_threads = {}
        self._init_database()
    
    def _init_database(self):
        """Initialize LLM database"""
        LLM_DB.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # LLM Models table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_models (
                model_id TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                model_type TEXT NOT NULL,
                source TEXT NOT NULL,
                source_model_id TEXT,
                version TEXT,
                size_gb REAL,
                parameters TEXT,
                capabilities TEXT,
                status TEXT DEFAULT 'pending',
                download_progress REAL DEFAULT 0,
                download_started TEXT,
                download_completed TEXT,
                error_message TEXT,
                created_at TEXT,
                created_by TEXT,
                last_used TEXT,
                usage_count INTEGER DEFAULT 0
            )
        """)
        
        # Model Configurations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_configs (
                config_id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                config_name TEXT,
                parameters TEXT,
                temperature REAL DEFAULT 0.7,
                max_tokens INTEGER DEFAULT 2048,
                top_p REAL DEFAULT 0.9,
                created_at TEXT,
                FOREIGN KEY (model_id) REFERENCES llm_models(model_id)
            )
        """)
        
        # Model Usage Log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT NOT NULL,
                user_id TEXT,
                org_id TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                response_time REAL,
                timestamp TEXT,
                FOREIGN KEY (model_id) REFERENCES llm_models(model_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        import secrets
        timestamp = int(time.time() * 1000)
        random = secrets.token_hex(4)
        return f"{prefix}-{timestamp}-{random}"
    
    # ========================================================================
    # OLLAMA INTEGRATION
    # ========================================================================
    
    def get_ollama_models(self) -> dict:
        """Get available models from Ollama"""
        try:
            # Check if Ollama is installed
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': 'Ollama not installed or not running',
                    'install_command': 'curl https://ollama.ai/install.sh | sh'
                }
            
            # Get list of available models
            available_models = [
                {
                    'id': 'llama2',
                    'name': 'Llama 2',
                    'size': '3.8 GB',
                    'parameters': '7B',
                    'description': 'Meta\'s Llama 2 model'
                },
                {
                    'id': 'llama2:13b',
                    'name': 'Llama 2 13B',
                    'size': '7.3 GB',
                    'parameters': '13B',
                    'description': 'Larger Llama 2 model'
                },
                {
                    'id': 'mistral',
                    'name': 'Mistral',
                    'size': '4.1 GB',
                    'parameters': '7B',
                    'description': 'Mistral 7B model'
                },
                {
                    'id': 'mixtral',
                    'name': 'Mixtral 8x7B',
                    'size': '26 GB',
                    'parameters': '8x7B',
                    'description': 'Mixtral mixture of experts'
                },
                {
                    'id': 'codellama',
                    'name': 'Code Llama',
                    'size': '3.8 GB',
                    'parameters': '7B',
                    'description': 'Specialized for code generation'
                },
                {
                    'id': 'phi',
                    'name': 'Phi-2',
                    'size': '1.7 GB',
                    'parameters': '2.7B',
                    'description': 'Microsoft Phi-2 small model'
                },
                {
                    'id': 'neural-chat',
                    'name': 'Neural Chat',
                    'size': '4.1 GB',
                    'parameters': '7B',
                    'description': 'Optimized for conversations'
                },
                {
                    'id': 'starling-lm',
                    'name': 'Starling',
                    'size': '4.1 GB',
                    'parameters': '7B',
                    'description': 'High-quality chat model'
                }
            ]
            
            # Get installed models
            installed = []
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 1:
                        installed.append(parts[0])
            
            return {
                'success': True,
                'source': 'ollama',
                'available_models': available_models,
                'installed_models': installed,
                'ollama_running': True
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'Ollama not installed',
                'install_command': 'curl https://ollama.ai/install.sh | sh',
                'available_models': []
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'available_models': []
            }
    
    def get_huggingface_models(self) -> dict:
        """Get popular models from HuggingFace"""
        popular_models = [
            {
                'id': 'meta-llama/Llama-2-7b-chat-hf',
                'name': 'Llama 2 7B Chat',
                'size': '13 GB',
                'parameters': '7B',
                'description': 'Meta Llama 2 optimized for chat'
            },
            {
                'id': 'meta-llama/Llama-2-13b-chat-hf',
                'name': 'Llama 2 13B Chat',
                'size': '26 GB',
                'parameters': '13B',
                'description': 'Larger Llama 2 chat model'
            },
            {
                'id': 'mistralai/Mistral-7B-Instruct-v0.2',
                'name': 'Mistral 7B Instruct',
                'size': '14 GB',
                'parameters': '7B',
                'description': 'Mistral AI instruction-tuned'
            },
            {
                'id': 'microsoft/phi-2',
                'name': 'Phi-2',
                'size': '5 GB',
                'parameters': '2.7B',
                'description': 'Microsoft small language model'
            },
            {
                'id': 'google/flan-t5-large',
                'name': 'FLAN-T5 Large',
                'size': '3 GB',
                'parameters': '780M',
                'description': 'Google instruction-tuned T5'
            },
            {
                'id': 'bigcode/starcoder',
                'name': 'StarCoder',
                'size': '15 GB',
                'parameters': '15B',
                'description': 'Specialized for code generation'
            },
            {
                'id': 'tiiuae/falcon-7b-instruct',
                'name': 'Falcon 7B Instruct',
                'size': '15 GB',
                'parameters': '7B',
                'description': 'TII Falcon instruction model'
            },
            {
                'id': 'EleutherAI/gpt-neox-20b',
                'name': 'GPT-NeoX 20B',
                'size': '40 GB',
                'parameters': '20B',
                'description': 'EleutherAI large model'
            }
        ]
        
        return {
            'success': True,
            'source': 'huggingface',
            'available_models': popular_models
        }
    
    # ========================================================================
    # MODEL MANAGEMENT
    # ========================================================================
    
    def create_model_entry(self, model_name: str, model_type: str, source: str,
                          source_model_id: str, size_gb: float, parameters: str,
                          capabilities: List[str], created_by: str) -> dict:
        """Create model entry in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        model_id = self._generate_id('LLM')
        
        cursor.execute("""
            INSERT INTO llm_models (model_id, model_name, model_type, source, source_model_id,
                                   size_gb, parameters, capabilities, status, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            model_id, model_name, model_type, source, source_model_id,
            size_gb, parameters, json.dumps(capabilities), 'downloading',
            datetime.now().isoformat(), created_by
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'model_id': model_id,
            'model_name': model_name
        }
    
    def download_ollama_model_async(self, model_id: str, ollama_model_name: str):
        """Download Ollama model asynchronously"""
        def download():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # Update status
                cursor.execute("""
                    UPDATE llm_models 
                    SET status='downloading', download_started=?, download_progress=0
                    WHERE model_id=?
                """, (datetime.now().isoformat(), model_id))
                conn.commit()
                
                # Download model using ollama
                process = subprocess.Popen(
                    ['ollama', 'pull', ollama_model_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Monitor progress
                for line in process.stdout:
                    if 'pulling' in line.lower():
                        # Update progress (simple progress tracking)
                        cursor.execute("""
                            UPDATE llm_models SET download_progress=50 WHERE model_id=?
                        """, (model_id,))
                        conn.commit()
                
                process.wait()
                
                if process.returncode == 0:
                    # Success
                    cursor.execute("""
                        UPDATE llm_models 
                        SET status='ready', download_progress=100, 
                            download_completed=?
                        WHERE model_id=?
                    """, (datetime.now().isoformat(), model_id))
                else:
                    # Error
                    error_msg = process.stderr.read()
                    cursor.execute("""
                        UPDATE llm_models 
                        SET status='error', error_message=?
                        WHERE model_id=?
                    """, (error_msg, model_id))
                
                conn.commit()
                
            except Exception as e:
                cursor.execute("""
                    UPDATE llm_models 
                    SET status='error', error_message=?
                    WHERE model_id=?
                """, (str(e), model_id))
                conn.commit()
            finally:
                conn.close()
        
        # Start download in background thread
        thread = threading.Thread(target=download, daemon=True)
        thread.start()
        self.download_threads[model_id] = thread
    
    def download_huggingface_model_async(self, model_id: str, hf_model_id: str):
        """Download HuggingFace model asynchronously"""
        def download():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # Update status
                cursor.execute("""
                    UPDATE llm_models 
                    SET status='downloading', download_started=?, download_progress=10
                    WHERE model_id=?
                """, (datetime.now().isoformat(), model_id))
                conn.commit()
                
                # Download using huggingface-cli
                cursor.execute("UPDATE llm_models SET download_progress=30 WHERE model_id=?", (model_id,))
                conn.commit()
                
                # Try to download (requires huggingface_hub)
                try:
                    from huggingface_hub import snapshot_download
                    
                    cursor.execute("UPDATE llm_models SET download_progress=50 WHERE model_id=?", (model_id,))
                    conn.commit()
                    
                    model_path = snapshot_download(
                        repo_id=hf_model_id,
                        cache_dir=str(self.models_dir)
                    )
                    
                    cursor.execute("""
                        UPDATE llm_models 
                        SET status='ready', download_progress=100,
                            download_completed=?
                        WHERE model_id=?
                    """, (datetime.now().isoformat(), model_id))
                    
                except ImportError:
                    # Fallback: Use git clone
                    cursor.execute("UPDATE llm_models SET download_progress=40 WHERE model_id=?", (model_id,))
                    conn.commit()
                    
                    repo_url = f"https://huggingface.co/{hf_model_id}"
                    model_path = self.models_dir / hf_model_id.replace('/', '_')
                    
                    result = subprocess.run(
                        ['git', 'clone', repo_url, str(model_path)],
                        capture_output=True,
                        text=True,
                        timeout=3600  # 1 hour timeout
                    )
                    
                    if result.returncode == 0:
                        cursor.execute("""
                            UPDATE llm_models 
                            SET status='ready', download_progress=100,
                                download_completed=?
                            WHERE model_id=?
                        """, (datetime.now().isoformat(), model_id))
                    else:
                        cursor.execute("""
                            UPDATE llm_models 
                            SET status='error', error_message=?
                            WHERE model_id=?
                        """, (result.stderr, model_id))
                
                conn.commit()
                
            except Exception as e:
                cursor.execute("""
                    UPDATE llm_models 
                    SET status='error', error_message=?
                    WHERE model_id=?
                """, (str(e), model_id))
                conn.commit()
            finally:
                conn.close()
        
        # Start download in background
        thread = threading.Thread(target=download, daemon=True)
        thread.start()
        self.download_threads[model_id] = thread
    
    def create_interface_llm(self, model_name: str, source: str, source_model_id: str,
                           size_gb: float, parameters: str, created_by: str) -> dict:
        """Create interface LLM (for user interaction)"""
        result = self.create_model_entry(
            model_name=model_name,
            model_type='interface',
            source=source,
            source_model_id=source_model_id,
            size_gb=size_gb,
            parameters=parameters,
            capabilities=['chat', 'instruction', 'dialogue'],
            created_by=created_by
        )
        
        if result['success']:
            model_id = result['model_id']
            
            # Start async download
            if source == 'ollama':
                self.download_ollama_model_async(model_id, source_model_id)
            elif source == 'huggingface':
                self.download_huggingface_model_async(model_id, source_model_id)
            
            return {
                'success': True,
                'model_id': model_id,
                'model_name': model_name,
                'status': 'downloading',
                'message': f'Model download started. Check status for progress.'
            }
        
        return result
    
    def create_knowledge_llm(self, model_name: str, source: str, source_model_id: str,
                           size_gb: float, parameters: str, created_by: str) -> dict:
        """Create knowledge LLM (for information retrieval)"""
        result = self.create_model_entry(
            model_name=model_name,
            model_type='knowledge',
            source=source,
            source_model_id=source_model_id,
            size_gb=size_gb,
            parameters=parameters,
            capabilities=['knowledge', 'retrieval', 'qa'],
            created_by=created_by
        )
        
        if result['success']:
            model_id = result['model_id']
            
            # Start async download
            if source == 'ollama':
                self.download_ollama_model_async(model_id, source_model_id)
            elif source == 'huggingface':
                self.download_huggingface_model_async(model_id, source_model_id)
            
            return {
                'success': True,
                'model_id': model_id,
                'model_name': model_name,
                'status': 'downloading',
                'message': f'Model download started. Check status for progress.'
            }
        
        return result
    
    def get_model_status(self, model_id: str) -> Optional[dict]:
        """Get model status and progress"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM llm_models WHERE model_id=?", (model_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'model_id': row[0],
            'model_name': row[1],
            'model_type': row[2],
            'source': row[3],
            'source_model_id': row[4],
            'version': row[5],
            'size_gb': row[6],
            'parameters': row[7],
            'capabilities': json.loads(row[8]) if row[8] else [],
            'status': row[9],
            'download_progress': row[10],
            'download_started': row[11],
            'download_completed': row[12],
            'error_message': row[13],
            'created_at': row[14],
            'usage_count': row[17]
        }
    
    def list_models(self, model_type: str = None) -> List[dict]:
        """List all models"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if model_type:
            cursor.execute("""
                SELECT model_id, model_name, model_type, source, parameters, 
                       size_gb, status, download_progress, usage_count
                FROM llm_models 
                WHERE model_type=?
                ORDER BY created_at DESC
            """, (model_type,))
        else:
            cursor.execute("""
                SELECT model_id, model_name, model_type, source, parameters, 
                       size_gb, status, download_progress, usage_count
                FROM llm_models 
                ORDER BY created_at DESC
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'model_id': row[0],
            'model_name': row[1],
            'model_type': row[2],
            'source': row[3],
            'parameters': row[4],
            'size_gb': row[5],
            'status': row[6],
            'download_progress': row[7],
            'usage_count': row[8]
        } for row in rows]
    
    def delete_model(self, model_id: str) -> bool:
        """Delete model and its files"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get model info
        cursor.execute("SELECT source, source_model_id FROM llm_models WHERE model_id=?", (model_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return False
        
        source, source_model_id = row
        
        # Delete from database
        cursor.execute("DELETE FROM llm_models WHERE model_id=?", (model_id,))
        cursor.execute("DELETE FROM model_configs WHERE model_id=?", (model_id,))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        # Delete files if Ollama
        if source == 'ollama':
            try:
                subprocess.run(['ollama', 'rm', source_model_id], timeout=30)
            except:
                pass
        
        return affected > 0
    
    def get_statistics(self) -> dict:
        """Get LLM statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count by type
        cursor.execute("SELECT model_type, COUNT(*) FROM llm_models GROUP BY model_type")
        type_counts = dict(cursor.fetchall())
        
        # Count by status
        cursor.execute("SELECT status, COUNT(*) FROM llm_models GROUP BY status")
        status_counts = dict(cursor.fetchall())
        
        # Total models
        cursor.execute("SELECT COUNT(*) FROM llm_models")
        total = cursor.fetchone()[0]
        
        # Total usage
        cursor.execute("SELECT SUM(usage_count) FROM llm_models")
        total_usage = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_models': total,
            'interface_llms': type_counts.get('interface', 0),
            'knowledge_llms': type_counts.get('knowledge', 0),
            'ready': status_counts.get('ready', 0),
            'downloading': status_counts.get('downloading', 0),
            'error': status_counts.get('error', 0),
            'total_usage': total_usage
        }

# Global LLM manager instance
llm_manager = LLMManager()

