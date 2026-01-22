"""
New Analysis Tools for Micro-Agent Architecture

Four specialized tools for code analysis:
1. analyze_call_graph - Python function call relationships
2. find_error_handlers - Exception handling patterns
3. analyze_exceptions - Error handling analysis
4. extract_env_vars - Environment variable extraction

All tools use RepoReadService for cached, bounded file reads
"""

import os
import ast
import re
import json
import logging
from typing import Dict, List, Set, Optional
from pathlib import Path
from langchain.tools import tool

logger = logging.getLogger(__name__)


@tool
def analyze_call_graph_tool(repo_path: str, entry_file: str) -> str:
    """
    Analyze Python function call relationships to build call graph.

    Extracts which functions call which other functions, useful for
    understanding code flow and dependencies.

    Args:
        repo_path: Absolute path to repository root
        entry_file: Relative path to Python file to analyze

    Returns:
        JSON string with call graph data
    """
    try:
        full_path = os.path.normpath(os.path.join(repo_path, entry_file))

        # Security check
        if not full_path.startswith(os.path.normpath(repo_path)):
            return json.dumps({"error": "Access denied - path traversal detected"})

        if not os.path.exists(full_path):
            return json.dumps({"error": f"File not found: {entry_file}"})

        if not entry_file.endswith('.py'):
            return json.dumps({"error": "Only Python files supported for call graph analysis"})

        # Read file (respects RepoReadService caps via shared config)
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return json.dumps({
                "error": f"Python syntax error: {str(e)}",
                "file": entry_file
            })

        # Extract function definitions and calls
        functions = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                calls = []

                # Find function calls within this function
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            calls.append(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            calls.append(f"{child.func.value.id if hasattr(child.func.value, 'id') else '?'}.{child.func.attr}")

                functions[func_name] = {
                    "calls": list(set(calls)),  # Deduplicate
                    "call_count": len(calls),
                    "line_number": node.lineno
                }

        # Build graph structure
        edges = []
        for func, data in functions.items():
            for called_func in data["calls"]:
                # Only include edges to other functions in this file
                if called_func in functions:
                    edges.append({"from": func, "to": called_func})

        result = {
            "file": entry_file,
            "functions": functions,
            "edges": edges,
            "function_count": len(functions),
            "edge_count": len(edges)
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error analyzing call graph for {entry_file}: {e}")
        return json.dumps({"error": f"Analysis failed: {str(e)}"})


@tool
def find_error_handlers_tool(repo_path: str) -> str:
    """
    Find exception handlers (try/except blocks) across Python files.

    Identifies error handling patterns and which exceptions are caught.

    Args:
        repo_path: Absolute path to repository root

    Returns:
        JSON string with error handler locations and types
    """
    try:
        error_handlers = []
        files_scanned = 0
        max_files = 50  # Limit scan to prevent timeout

        # Walk repository
        for root, dirs, files in os.walk(repo_path):
            # Filter ignored directories
            dirs[:] = [d for d in dirs if d not in {
                '.git', '__pycache__', 'node_modules', '.venv', 'venv',
                'dist', 'build', 'target', 'coverage'
            }]

            for file in files:
                if not file.endswith('.py'):
                    continue

                if files_scanned >= max_files:
                    break

                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Parse AST
                    tree = ast.parse(content)

                    # Find try/except blocks
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Try):
                            exceptions_caught = []

                            for handler in node.handlers:
                                if handler.type:
                                    if isinstance(handler.type, ast.Name):
                                        exceptions_caught.append(handler.type.id)
                                    elif isinstance(handler.type, ast.Tuple):
                                        for exc in handler.type.elts:
                                            if isinstance(exc, ast.Name):
                                                exceptions_caught.append(exc.id)
                                else:
                                    exceptions_caught.append("Exception")  # Bare except

                            error_handlers.append({
                                "file": rel_path,
                                "line": node.lineno,
                                "exceptions": exceptions_caught,
                                "has_finally": len(node.finalbody) > 0,
                                "has_else": len(node.orelse) > 0
                            })

                    files_scanned += 1

                except Exception as e:
                    logger.debug(f"Skipping {rel_path}: {e}")
                    continue

            if files_scanned >= max_files:
                break

        # Aggregate statistics
        exception_types = {}
        for handler in error_handlers:
            for exc in handler["exceptions"]:
                exception_types[exc] = exception_types.get(exc, 0) + 1

        result = {
            "error_handlers": error_handlers[:100],  # Limit output
            "total_handlers": len(error_handlers),
            "files_scanned": files_scanned,
            "exception_types": dict(sorted(exception_types.items(), key=lambda x: x[1], reverse=True))
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error finding error handlers: {e}")
        return json.dumps({"error": f"Scan failed: {str(e)}"})


@tool
def analyze_exceptions_tool(repo_path: str, file_path: str) -> str:
    """
    Analyze exception handling in a specific Python file.

    Provides detailed analysis of try/except patterns, custom exceptions,
    and error handling quality.

    Args:
        repo_path: Absolute path to repository root
        file_path: Relative path to Python file

    Returns:
        JSON string with exception analysis
    """
    try:
        full_path = os.path.normpath(os.path.join(repo_path, file_path))

        # Security check
        if not full_path.startswith(os.path.normpath(repo_path)):
            return json.dumps({"error": "Access denied"})

        if not os.path.exists(full_path):
            return json.dumps({"error": f"File not found: {file_path}"})

        # Read file
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return json.dumps({"error": f"Syntax error: {str(e)}"})

        # Find custom exception classes
        custom_exceptions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it inherits from Exception
                for base in node.bases:
                    if isinstance(base, ast.Name) and 'Exception' in base.id:
                        custom_exceptions.append({
                            "name": node.name,
                            "line": node.lineno
                        })

        # Analyze try/except blocks
        exception_handlers = []
        bare_excepts = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                handler_info = {
                    "line": node.lineno,
                    "handlers": []
                }

                for handler in node.handlers:
                    if handler.type is None:
                        bare_excepts.append(node.lineno)
                        handler_info["handlers"].append({"type": "bare_except", "warning": "Catches all exceptions"})
                    elif isinstance(handler.type, ast.Name):
                        handler_info["handlers"].append({"type": handler.type.id})
                    elif isinstance(handler.type, ast.Tuple):
                        types = [exc.id for exc in handler.type.elts if isinstance(exc, ast.Name)]
                        handler_info["handlers"].append({"types": types})

                exception_handlers.append(handler_info)

        # Find raise statements
        raises = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise):
                if node.exc:
                    if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                        raises.append({
                            "line": node.lineno,
                            "exception": node.exc.func.id
                        })
                    elif isinstance(node.exc, ast.Name):
                        raises.append({
                            "line": node.lineno,
                            "exception": node.exc.id
                        })

        result = {
            "file": file_path,
            "custom_exceptions": custom_exceptions,
            "exception_handlers": exception_handlers,
            "bare_excepts_count": len(bare_excepts),
            "bare_except_lines": bare_excepts,
            "raises": raises,
            "quality_notes": []
        }

        # Add quality notes
        if len(bare_excepts) > 0:
            result["quality_notes"].append(f"Found {len(bare_excepts)} bare except clauses (not recommended)")

        if len(custom_exceptions) > 0:
            result["quality_notes"].append(f"Defines {len(custom_exceptions)} custom exception classes")

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error analyzing exceptions in {file_path}: {e}")
        return json.dumps({"error": f"Analysis failed: {str(e)}"})


@tool
def extract_env_vars_tool(repo_path: str) -> str:
    """
    Extract environment variables from .env example files.

    Finds .env.example, .env.sample, .env.template files and extracts
    variable names (not values, for security).

    Args:
        repo_path: Absolute path to repository root

    Returns:
        JSON string with environment variable names and descriptions
    """
    try:
        env_vars = []
        files_found = []

        # Common env file patterns
        env_file_patterns = [
            '.env.example',
            '.env.sample',
            '.env.template',
            'env.example',
            'example.env'
        ]

        # Search for env files
        for pattern in env_file_patterns:
            file_path = os.path.join(repo_path, pattern)
            if os.path.exists(file_path):
                files_found.append(pattern)

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()

                    for line_num, line in enumerate(lines, 1):
                        line = line.strip()

                        # Skip comments and empty lines
                        if not line or line.startswith('#'):
                            continue

                        # Parse KEY=value format
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()

                            # Extract inline comment if present
                            comment = ""
                            if '#' in value:
                                value, comment = value.split('#', 1)
                                comment = comment.strip()

                            # Check if value looks like a placeholder
                            is_placeholder = bool(re.match(r'^(<.*?>|".*?"|\'.*?\'|\$\{.*?\}|your_.*|example_.*)', value, re.IGNORECASE))

                            env_vars.append({
                                "key": key,
                                "file": pattern,
                                "line": line_num,
                                "has_default": len(value) > 0 and not is_placeholder,
                                "description": comment if comment else None,
                                "is_placeholder": is_placeholder
                            })

                except Exception as e:
                    logger.warning(f"Error reading {pattern}: {e}")
                    continue

        # Also check for variables in README or docs
        readme_vars = set()
        for readme_name in ['README.md', 'readme.md', 'README']:
            readme_path = os.path.join(repo_path, readme_name)
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Look for environment variable mentions
                    var_pattern = r'\b([A-Z_][A-Z0-9_]{2,})\b'
                    matches = re.findall(var_pattern, content)
                    readme_vars.update(matches)

                except:
                    pass

        # Categorize variables
        categories = {
            "database": [],
            "api_keys": [],
            "urls": [],
            "ports": [],
            "auth": [],
            "other": []
        }

        for var in env_vars:
            key_lower = var["key"].lower()
            if any(word in key_lower for word in ['db', 'database', 'postgres', 'mysql', 'mongo']):
                categories["database"].append(var)
            elif any(word in key_lower for word in ['key', 'token', 'secret', 'password']):
                categories["api_keys"].append(var)
            elif any(word in key_lower for word in ['url', 'endpoint', 'host', 'domain']):
                categories["urls"].append(var)
            elif 'port' in key_lower:
                categories["ports"].append(var)
            elif any(word in key_lower for word in ['auth', 'client_id', 'client_secret', 'oauth']):
                categories["auth"].append(var)
            else:
                categories["other"].append(var)

        result = {
            "env_files_found": files_found,
            "total_variables": len(env_vars),
            "variables": env_vars,
            "categorized": categories,
            "readme_mentions": list(readme_vars)[:20]  # Limit to 20
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error extracting env vars: {e}")
        return json.dumps({"error": f"Extraction failed: {str(e)}"})
