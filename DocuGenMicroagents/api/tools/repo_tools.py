"""
LangChain tools for repository analysis
Uses @tool decorator for automatic integration with agents

FIXED VERSION: Strengthened Mermaid validation for render-safe diagrams
ENHANCED: Strategic file reading with pattern_window mode
"""

import os
import json
import re
from pathlib import Path
from collections import Counter
from typing import Dict, List, Literal
from langchain.tools import tool
import logging

from config import settings

logger = logging.getLogger(__name__)

# Ignore patterns for directory listing
IGNORE_DIRS = {
    '.git', '__pycache__', 'node_modules', '.venv', 'venv',
    'dist', 'build', '.next', '.nuxt', 'target', 'coverage',
    '.idea', '.vscode', 'DS_Store'
}

# Language detection mapping
LANGUAGE_MAP = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.jsx': 'JavaScript (JSX)',
    '.tsx': 'TypeScript (TSX)',
    '.java': 'Java',
    '.go': 'Go',
    '.rs': 'Rust',
    '.c': 'C',
    '.cpp': 'C++',
    '.cs': 'C#',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
}


@tool
def list_directory_tool(repo_path: str, relative_path: str = ".") -> str:
    """
    List contents of a directory in the repository.
    Shows files and subdirectories with their types.

    Args:
        repo_path: Absolute path to the repository root
        relative_path: Relative path from repo root (default: ".")

    Returns:
        Formatted string listing files and directories
    """
    try:
        full_path = os.path.normpath(os.path.join(repo_path, relative_path))

        # Security check
        if not full_path.startswith(os.path.normpath(repo_path)):
            return f"Error: Access denied - path traversal detected"

        if not os.path.exists(full_path):
            return f"Error: Directory not found: {relative_path}"

        if not os.path.isdir(full_path):
            return f"Error: Path is not a directory: {relative_path}"

        items = []
        for entry in os.listdir(full_path):
            if entry in IGNORE_DIRS or entry.startswith('.'):
                continue

            entry_path = os.path.join(full_path, entry)
            item_type = "DIR" if os.path.isdir(entry_path) else "FILE"
            items.append(f"[{item_type}] {entry}")

        if not items:
            return f"Directory '{relative_path}' is empty or contains only ignored files"

        return f"Contents of {relative_path}:\n" + "\n".join(sorted(items))

    except Exception as e:
        logger.error(f"Error listing directory {relative_path}: {e}")
        return f"Error listing directory: {str(e)}"


def _smart_sample_lines(lines: List[str], max_lines: int) -> tuple[list[str], bool]:
    """
    Smart sampling: top + function/class signatures + bottom

    Args:
        lines: All file lines
        max_lines: Budget for total lines

    Returns:
        (selected_lines, was_truncated)
    """
    if len(lines) <= max_lines:
        return lines, False

    top_n = min(50, max_lines)
    bottom_n = min(30, max_lines - top_n)
    middle_budget = max(0, max_lines - top_n - bottom_n)

    top = lines[:top_n]
    bottom = lines[-bottom_n:] if bottom_n > 0 else []

    # Extract function/class signatures
    sigs = []
    for ln in lines[top_n:len(lines) - bottom_n]:
        s = ln.lstrip()
        if s.startswith(("def ", "async def ", "class ")):
            sigs.append(ln)
            if len(sigs) >= middle_budget:
                break

    out = top + ["\n... [middle omitted] ...\n"] + sigs + ["\n... [end] ...\n"] + bottom
    return out[:max_lines], True


def _pattern_window_lines(lines: List[str], max_lines: int) -> tuple[list[str], bool]:
    """
    Pattern window sampling: detect high-value patterns, extract ±6 lines around matches

    Patterns detected:
    - FastAPI/Flask routes: @app.get, @router.post, APIRouter, include_router
    - Error handling: try, except, raise
    - Entry points: if __name__ == "__main__", uvicorn.run, def main

    Args:
        lines: All file lines
        max_lines: Budget for total lines

    Returns:
        (selected_lines, was_truncated)
    """
    if len(lines) <= max_lines:
        return lines, False

    patterns = [
        r"@app\.(get|post|put|delete)\b",
        r"@router\.(get|post|put|delete)\b",
        r"\bAPIRouter\b",
        r"\binclude_router\b",
        r"\btry:\b",
        r"\bexcept\b",
        r"\braise\b",
        r'if __name__\s*==\s*[\'"]__main__[\'"]',
        r"\buvicorn\.run\b",
        r"\bdef main\(",
    ]

    top_n = min(40, max_lines)
    bottom_n = min(25, max_lines - top_n)
    budget = max_lines - top_n - bottom_n

    # Find match line numbers
    match_lines: list[int] = []
    for i, ln in enumerate(lines):
        for pat in patterns:
            if re.search(pat, ln):
                match_lines.append(i)
                break

    # Fallback to smart if no patterns found
    if not match_lines:
        logger.debug("No patterns found, falling back to smart strategy")
        return _smart_sample_lines(lines, max_lines)

    # Make windows ±6 lines around matches
    windows: list[tuple[int, int]] = []
    for i in match_lines[:50]:  # Cap matches
        start = max(0, i - 6)
        end = min(len(lines), i + 7)
        windows.append((start, end))

    # Merge overlapping windows
    windows.sort()
    merged: list[tuple[int, int]] = []
    for s, e in windows:
        if not merged or s > merged[-1][1]:
            merged.append((s, e))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))

    # Emit lines within budget
    out = lines[:top_n]
    used = len(out)
    last_end = top_n

    for s, e in merged:
        if used >= top_n + budget:
            break
        if e <= top_n or s >= len(lines) - bottom_n:
            continue  # Already in top/bottom

        if s > last_end:
            out.append("\n... [omitted] ...\n")
            used += 1

        chunk = lines[s:e]
        room = top_n + budget - used
        if room <= 0:
            break
        out.extend(chunk[:room])
        used = len(out)
        last_end = e

    out.append("\n... [end] ...\n")
    out.extend(lines[-bottom_n:])

    # Final clamp
    out = out[:max_lines]
    return out, True


@tool
def read_file_tool(
    repo_path: str,
    file_path: str,
    max_lines: int = None,
    strategy: Literal["full", "smart", "pattern_window"] = "full"
) -> str:
    """
    Read contents of a file from the repository.

    Args:
        repo_path: Absolute path to the repository root
        file_path: Relative path to the file from repo root
        max_lines: Maximum lines to read (default: from settings.MAX_LINES_PER_FILE)
        strategy: Reading strategy:
          - "full": first N lines (default, backwards compatible)
          - "smart": top + signatures + bottom
          - "pattern_window": extract windows around high-value patterns (routes, errors, entrypoints)

    Returns:
        File contents as string
    """
    try:
        # Use config setting if not specified
        if max_lines is None:
            max_lines = settings.MAX_LINES_PER_FILE

        full_path = os.path.normpath(os.path.join(repo_path, file_path))

        # Security check
        if not full_path.startswith(os.path.normpath(repo_path)):
            return "Error: Access denied - path traversal detected"

        if not os.path.exists(full_path):
            return f"Error: File not found: {file_path}"

        if not os.path.isfile(full_path):
            return f"Error: Path is not a file: {file_path}"

        # Check file size using config setting
        file_size = os.path.getsize(full_path)
        max_file_size_mb = settings.MAX_FILE_SIZE / 1_000_000
        if file_size > settings.MAX_FILE_SIZE:
            return f"Error: File too large ({file_size} bytes). Maximum is {max_file_size_mb:.1f}MB."

        # Read file
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        # Strategy dispatch
        if strategy == "full":
            selected = lines[:max_lines]
            truncated = len(lines) > max_lines

        elif strategy == "smart":
            selected, truncated = _smart_sample_lines(lines, max_lines=max_lines)

        elif strategy == "pattern_window":
            selected, truncated = _pattern_window_lines(lines, max_lines=max_lines)

        else:
            selected = lines[:max_lines]
            truncated = len(lines) > max_lines

        content = "".join(selected)

        # Deterministic header for verification
        header = f"File: {file_path} | strategy: {strategy} | lines: {len(selected)}/{len(lines)}"
        if truncated:
            return f"{header}\n\n{content}\n\n[File truncated...]"
        return f"{header}\n\n{content}"

    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return f"Error reading file: {str(e)}"


@tool
def detect_languages_tool(repo_path: str) -> str:
    """
    Detect programming languages used in the repository.
    Analyzes file extensions and provides statistics.

    Args:
        repo_path: Absolute path to the repository root

    Returns:
        JSON string with language statistics
    """
    try:
        language_counter = Counter()
        total_files = 0

        for root, dirs, files in os.walk(repo_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]

            for file in files:
                if file.startswith('.'):
                    continue

                ext = Path(file).suffix.lower()
                if ext in LANGUAGE_MAP:
                    language = LANGUAGE_MAP[ext]
                    language_counter[language] += 1
                    total_files += 1

        if not language_counter:
            return "No recognized programming languages detected"

        # Format output
        result = {
            "total_files": total_files,
            "languages": dict(language_counter.most_common()),
            "primary_language": language_counter.most_common(1)[0][0] if language_counter else "Unknown"
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error detecting languages: {e}")
        return f"Error detecting languages: {str(e)}"


@tool
def extract_dependencies_tool(repo_path: str) -> str:
    """
    Extract dependencies from common dependency files.
    Recursively scans subdirectories for package.json, requirements.txt, go.mod, Cargo.toml, etc.

    Args:
        repo_path: Absolute path to the repository root

    Returns:
        JSON string with dependencies by ecosystem
    """
    try:
        dependencies = {}
        found_files = []

        # Recursively walk directory tree to find dependency files
        for root, dirs, files in os.walk(repo_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]

            # Python - requirements.txt
            if 'requirements.txt' in files:
                req_file = os.path.join(root, 'requirements.txt')
                rel_path = os.path.relpath(req_file, repo_path)
                try:
                    with open(req_file, 'r') as f:
                        deps = [line.strip().split('==')[0].split('>=')[0].split('[')[0]
                                for line in f if line.strip() and not line.startswith('#')]
                        if deps and "Python" not in dependencies:
                            dependencies["Python"] = deps[:20]  # Limit to 20
                            found_files.append(f"requirements.txt ({rel_path})")
                except:
                    pass

            # Node.js - package.json
            if 'package.json' in files:
                pkg_file = os.path.join(root, 'package.json')
                rel_path = os.path.relpath(pkg_file, repo_path)
                try:
                    with open(pkg_file, 'r') as f:
                        pkg_data = json.load(f)
                        deps = list(pkg_data.get("dependencies", {}).keys())
                        if deps and "Node.js" not in dependencies:
                            dependencies["Node.js"] = deps[:20]
                            found_files.append(f"package.json ({rel_path})")
                except:
                    pass

            # Go - go.mod
            if 'go.mod' in files:
                go_file = os.path.join(root, 'go.mod')
                rel_path = os.path.relpath(go_file, repo_path)
                try:
                    with open(go_file, 'r') as f:
                        deps = [line.split()[0] for line in f if line.strip().startswith('require')]
                        if deps and "Go" not in dependencies:
                            dependencies["Go"] = deps[:20]
                            found_files.append(f"go.mod ({rel_path})")
                except:
                    pass

            # Rust - Cargo.toml
            if 'Cargo.toml' in files:
                cargo_file = os.path.join(root, 'Cargo.toml')
                rel_path = os.path.relpath(cargo_file, repo_path)
                try:
                    with open(cargo_file, 'r') as f:
                        in_deps = False
                        deps = []
                        for line in f:
                            if '[dependencies]' in line:
                                in_deps = True
                                continue
                            if in_deps and line.strip() and line.startswith('['):
                                break
                            if in_deps and '=' in line:
                                dep_name = line.split('=')[0].strip()
                                deps.append(dep_name)
                        if deps and "Rust" not in dependencies:
                            dependencies["Rust"] = deps[:20]
                            found_files.append(f"Cargo.toml ({rel_path})")
                except:
                    pass

        if not dependencies:
            return "No dependency files found"

        result = {
            "dependencies": dependencies,
            "files_found": found_files
        }
        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error extracting dependencies: {e}")
        return f"Error extracting dependencies: {str(e)}"


@tool
def analyze_code_structure_tool(repo_path: str, file_path: str) -> str:
    """
    Analyze code structure of a file (functions, classes, imports).
    Uses AST parsing for Python, basic regex for others.

    Args:
        repo_path: Absolute path to the repository root
        file_path: Relative path to the file from repo root

    Returns:
        JSON string with code structure analysis
    """
    try:
        full_path = os.path.normpath(os.path.join(repo_path, file_path))

        if not full_path.startswith(os.path.normpath(repo_path)):
            return "Error: Access denied"

        if not os.path.exists(full_path):
            return "Error: File not found"

        ext = Path(file_path).suffix.lower()

        # Python AST analysis
        if ext == '.py':
            try:
                import ast
                with open(full_path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())

                functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                imports = [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]

                result = {
                    "language": "Python",
                    "functions": functions[:20],
                    "classes": classes[:20],
                    "imports": imports[:20],
                    "total_functions": len(functions),
                    "total_classes": len(classes)
                }
                return json.dumps(result, indent=2)
            except Exception as e:
                return f"Error parsing Python file: {str(e)}"

        # For other languages, provide basic info
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')

        result = {
            "language": LANGUAGE_MAP.get(ext, "Unknown"),
            "lines_of_code": len(lines),
            "non_empty_lines": len([l for l in lines if l.strip()]),
            "note": "Detailed analysis only available for Python files"
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error analyzing code structure: {e}")
        return f"Error analyzing code structure: {str(e)}"


# ============================================================================
# SPECIALIZED TOOLS FOR PLANNER AGENT
# ============================================================================

@tool
def find_ui_files_tool(repo_path: str) -> str:
    """
    Check if the project has a UI/frontend component.
    Looks for frontend directories and files (React, Vue, Angular, HTML, etc.).

    Args:
        repo_path: Absolute path to the repository root

    Returns:
        JSON string with UI detection results
    """
    try:
        ui_indicators = {
            "directories": [],
            "files": [],
            "frameworks": []
        }

        # Check for common frontend directories
        ui_dirs = ['frontend', 'ui', 'client', 'web', 'app', 'src/components', 'public']
        for dir_name in ui_dirs:
            dir_path = os.path.join(repo_path, dir_name)
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                ui_indicators["directories"].append(dir_name)

        # Check for frontend files
        ui_files = ['index.html', 'App.jsx', 'App.tsx', 'App.vue', 'index.jsx', 'index.tsx']
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                if file in ui_files:
                    rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                    ui_indicators["files"].append(rel_path)

        # Check package.json for frontend frameworks
        pkg_file = os.path.join(repo_path, "package.json")
        if os.path.exists(pkg_file):
            with open(pkg_file, 'r') as f:
                pkg_data = json.load(f)
                deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}

                if "react" in deps:
                    ui_indicators["frameworks"].append("React")
                if "vue" in deps:
                    ui_indicators["frameworks"].append("Vue.js")
                if "@angular/core" in deps:
                    ui_indicators["frameworks"].append("Angular")
                if "next" in deps:
                    ui_indicators["frameworks"].append("Next.js")
                if "svelte" in deps:
                    ui_indicators["frameworks"].append("Svelte")

        has_ui = bool(ui_indicators["directories"] or ui_indicators["files"] or ui_indicators["frameworks"])

        result = {
            "has_ui": has_ui,
            "indicators": ui_indicators
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error finding UI files: {e}")
        return f"Error finding UI files: {str(e)}"


@tool
def find_docker_files_tool(repo_path: str) -> str:
    """
    Check for Docker/container deployment files.

    Args:
        repo_path: Absolute path to the repository root

    Returns:
        JSON string with Docker file detection results
    """
    try:
        docker_files = []

        # Check for Docker files
        docker_indicators = [
            'Dockerfile',
            'docker-compose.yml',
            'docker-compose.yaml',
            '.dockerignore',
            'Dockerfile.prod',
            'Dockerfile.dev'
        ]

        for file_name in docker_indicators:
            file_path = os.path.join(repo_path, file_name)
            if os.path.exists(file_path):
                docker_files.append(file_name)

        result = {
            "has_docker": bool(docker_files),
            "docker_files": docker_files
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error finding Docker files: {e}")
        return f"Error finding Docker files: {str(e)}"


@tool
def find_config_files_tool(repo_path: str) -> str:
    """
    Find configuration files (.env, config files, etc.).
    Recursively scans subdirectories.

    Args:
        repo_path: Absolute path to the repository root

    Returns:
        JSON string with configuration file detection results
    """
    try:
        config_files = []

        # Config file patterns to search for
        config_indicators = [
            '.env.example',
            '.env.sample',
            '.env.template',
            'config.json',
            'config.yaml',
            'config.yml',
            'settings.py',
            'config.py',
            'appsettings.json'
        ]

        # Recursively walk directory tree
        for root, dirs, files in os.walk(repo_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]

            for file in files:
                if file in config_indicators:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, repo_path)
                    config_files.append(rel_path)

        result = {
            "has_config": bool(config_files),
            "config_files": config_files,
            "count": len(config_files)
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error finding config files: {e}")
        return f"Error finding config files: {str(e)}"


@tool
def find_dependency_files_tool(repo_path: str) -> str:
    """
    Find dependency/package files in the repository.
    Recursively scans subdirectories for requirements.txt, package.json, go.mod, Cargo.toml, pom.xml, etc.

    Args:
        repo_path: Absolute path to the repository root

    Returns:
        JSON string with dependency file locations
    """
    try:
        dependency_files = []

        # Common dependency file patterns
        dep_patterns = [
            'requirements.txt',
            'package.json',
            'go.mod',
            'Cargo.toml',
            'pom.xml',
            'build.gradle',
            'Gemfile',
            'composer.json',
            'Pipfile',
            'poetry.lock',
            'yarn.lock',
            'package-lock.json'
        ]

        # Recursively walk directory tree
        for root, dirs, files in os.walk(repo_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith('.')]

            for file in files:
                if file in dep_patterns:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, repo_path)
                    dependency_files.append(rel_path)

        result = {
            "dependency_files": dependency_files,
            "count": len(dependency_files)
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error finding dependency files: {e}")
        return f"Error finding dependency files: {str(e)}"


# ============================================================================
# SPECIALIZED TOOLS FOR DIAGRAM GENERATOR AGENT
# ============================================================================

@tool
def find_entry_points_tool(repo_path: str) -> str:
    """
    Find main entry point files (main.py, server.py, index.js, etc.).

    Args:
        repo_path: Absolute path to the repository root

    Returns:
        JSON string with entry point file locations
    """
    try:
        entry_points = []

        # Common entry point patterns
        entry_patterns = [
            'main.py', 'app.py', 'server.py', '__main__.py',
            'index.js', 'index.ts', 'server.js', 'app.js',
            'main.go', 'main.rs', 'Main.java'
        ]

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                if file in entry_patterns:
                    rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                    entry_points.append(rel_path)

        result = {
            "entry_points": entry_points,
            "count": len(entry_points)
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error finding entry points: {e}")
        return f"Error finding entry points: {str(e)}"


@tool
def find_api_routes_tool(repo_path: str, entry_file: str) -> str:
    """
    Analyze an entry file to find API routes/endpoints.
    Looks for common patterns like @app.route, @router.get, etc.

    Args:
        repo_path: Absolute path to the repository root
        entry_file: Relative path to entry file from repo root

    Returns:
        JSON string with discovered API routes
    """
    try:
        full_path = os.path.normpath(os.path.join(repo_path, entry_file))

        if not full_path.startswith(os.path.normpath(repo_path)):
            return "Error: Access denied"

        if not os.path.exists(full_path):
            return "Error: File not found"

        routes = []

        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')

        # Pattern matching for routes
        route_patterns = [
            r'@app\.route\(["\'](.+?)["\']\)',  # Flask
            r'@router\.(get|post|put|delete)\(["\'](.+?)["\']\)',  # FastAPI
            r'app\.(get|post|put|delete)\(["\'](.+?)["\']\)',  # Express
            r'@(Get|Post|Put|Delete)Mapping\(["\'](.+?)["\']\)'  # Spring
        ]

        for line in lines:
            for pattern in route_patterns:
                matches = re.findall(pattern, line)
                if matches:
                    routes.extend([str(m) if isinstance(m, str) else m[-1] for m in matches])

        result = {
            "file": entry_file,
            "routes": routes[:50],  # Limit to 50 routes
            "route_count": len(routes)
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error finding API routes: {e}")
        return f"Error finding API routes: {str(e)}"



# ============================================================================
# VALIDATION TOOLS FOR SELF-CRITIQUE LOOPS
# ============================================================================

@tool
def validate_readme_structure_tool(readme_content: str) -> str:
    """
    Validate README structure and completeness.
    Checks for expected sections, proper markdown formatting, code blocks.

    Args:
        readme_content: README markdown content to validate

    Returns:
        JSON string with validation results
    """
    try:
        issues = []
        sections_found = []

        # Extract sections (markdown headers)
        import re
        header_pattern = r'^##\s+(.+)$'
        sections = re.findall(header_pattern, readme_content, re.MULTILINE)
        sections_found = sections

        # Expected sections (at least some of these should be present)
        expected_sections = ["Overview", "Features", "Installation", "Usage", "Configuration", "API"]
        found_expected = [s for s in expected_sections if any(exp.lower() in s.lower() for exp in sections)]

        if len(found_expected) < 3:
            issues.append({
                "severity": "warning",
                "message": f"Only {len(found_expected)} standard sections found. Consider adding more."
            })

        # Check for code blocks
        code_blocks = readme_content.count("```")
        if code_blocks == 0:
            issues.append({
                "severity": "info",
                "message": "No code examples found. Consider adding usage examples."
            })
        elif code_blocks % 2 != 0:
            issues.append({
                "severity": "error",
                "message": "Unbalanced code blocks (missing closing ```)"
            })

        # Check for mermaid diagrams
        has_mermaid = "```mermaid" in readme_content
        if not has_mermaid:
            issues.append({
                "severity": "info",
                "message": "No Mermaid diagrams found. Visual diagrams enhance documentation."
            })

        # Check minimum length
        if len(readme_content) < 500:
            issues.append({
                "severity": "warning",
                "message": "README is very short. Consider adding more detail."
            })

        result = {
            "sections_found": sections_found,
            "section_count": len(sections_found),
            "code_blocks": code_blocks // 2 if code_blocks % 2 == 0 else 0,
            "has_mermaid": has_mermaid,
            "content_length": len(readme_content),
            "issues": issues
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error validating README structure: {e}")
        return json.dumps({
            "error": str(e),
            "issues": [{"severity": "error", "message": f"Validation failed: {str(e)}"}]
        })


@tool
def validate_mermaid_syntax_tool(mermaid_code: str) -> str:
    """
    Validate Mermaid diagram syntax with STRICT Mermaid 8.14.0 render-safe checks.
    Returns JSON string with validation results.

    FIXED VERSION: Enforces render-safe patterns that prevent "Syntax error in graph"

    Checks:
    - Node IDs must be alphanumeric + underscore only
    - Node labels must be quoted: ID["Label"]
    - Edge labels must not contain: / ( ) : ` "
    - Basic structure (brackets, arrows, diagram type)

    Args:
        mermaid_code: Mermaid diagram code to validate

    Returns:
        JSON: {"valid": bool, "errors": [...], "warnings": [...]}
    """
    try:
        errors = []
        warnings = []

        # Basic checks
        if not mermaid_code or not mermaid_code.strip():
            errors.append("Empty diagram code")
            return json.dumps({"valid": False, "errors": errors, "warnings": warnings})

        code = mermaid_code.strip()

        # Check for diagram type
        diagram_types = [
            "graph", "flowchart", "sequenceDiagram", "classDiagram",
            "stateDiagram", "erDiagram", "journey", "gantt", "pie"
        ]
        has_type = any(code.startswith(dt) for dt in diagram_types)
        if not has_type:
            errors.append(f"Must start with diagram type: {diagram_types[:4]}...")

        # Check for common syntax errors
        open_brackets = code.count("[")
        close_brackets = code.count("]")
        if open_brackets != close_brackets:
            errors.append(f"Unbalanced square brackets: {open_brackets} open vs {close_brackets} close")

        open_parens = code.count("(")
        close_parens = code.count(")")
        if open_parens != close_parens:
            errors.append(f"Unbalanced parentheses: {open_parens} open vs {close_parens} close")

        open_braces = code.count("{")
        close_braces = code.count("}")
        if open_braces != close_braces:
            errors.append(f"Unbalanced curly braces: {open_braces} open vs {close_braces} close")

        # Check for arrow syntax (graph/flowchart)
        if code.startswith(("graph", "flowchart")):
            # Must have at least one arrow
            has_arrow = ("-->" in code or "---" in code or "==>" in code or
                        "-.->" in code or "-..->" in code)
            if not has_arrow:
                warnings.append("Graph/flowchart diagrams typically need arrows (-->, --->, etc.)")

            # Check for node definitions
            lines = code.split("\n")
            node_lines = [l for l in lines if "-->" in l or "---" in l]
            if len(node_lines) == 0:
                errors.append("No connections found - graph needs edges like: A --> B")

            # ===================================================================
            # MERMAID 8.14.0 RENDER-SAFE VALIDATION (NEW)
            # ===================================================================

            # Check 1: Node IDs must be alphanumeric + underscore only
            # Pattern: extract node IDs from lines like "NodeID[...]" or "NodeID --> OtherNode"
            node_id_pattern = r'\b([A-Za-z][A-Za-z0-9_]*)\s*(?:\[|-->|---|\||$)'
            node_ids = []
            for line in lines[1:]:  # Skip first line (graph TD/LR)
                if not line.strip() or line.strip().startswith('#'):
                    continue
                matches = re.findall(node_id_pattern, line)
                node_ids.extend(matches)

            # Check for invalid node IDs (contain special chars besides underscore)
            invalid_node_pattern = r'\b([A-Za-z0-9_]*[^A-Za-z0-9_\s\[\](){}|>-]+[A-Za-z0-9_]*)\s*(?:\[|-->)'
            for line in lines[1:]:
                if not line.strip():
                    continue
                invalid_matches = re.findall(invalid_node_pattern, line)
                for invalid_id in invalid_matches:
                    if invalid_id and not invalid_id.isspace():
                        errors.append(
                            f"Invalid node ID '{invalid_id}' - must be alphanumeric + underscore only. "
                            f"Use: {re.sub(r'[^A-Za-z0-9_]', '', invalid_id)}"
                        )

            # Check 2: Node labels must be quoted if they contain special characters
            # Pattern: NodeID[unquoted text with spaces or special chars]
            unquoted_label_pattern = r'([A-Za-z][A-Za-z0-9_]*)\[([^\]"]+[^"\]])\]'
            for line in lines[1:]:
                if not line.strip():
                    continue
                matches = re.findall(unquoted_label_pattern, line)
                for node_id, label in matches:
                    # Check if label has spaces or special chars and is not quoted
                    if ' ' in label or '(' in label or ')' in label or '/' in label:
                        if not (label.strip().startswith('"') and label.strip().endswith('"')):
                            errors.append(
                                f"Unquoted label in node '{node_id}[{label}]' - must use quotes: {node_id}[\"{label}\"]"
                            )

            # Check 3: Edge labels must not contain unsafe characters
            # Pattern: |label text|
            edge_label_pattern = r'\|([^|]+)\|'
            unsafe_edge_chars = ['/', '(', ')', ':', '`', '"']
            for line in lines[1:]:
                if not line.strip():
                    continue
                edge_matches = re.findall(edge_label_pattern, line)
                for edge_label in edge_matches:
                    for unsafe_char in unsafe_edge_chars:
                        if unsafe_char in edge_label:
                            safe_label = edge_label
                            for char in unsafe_edge_chars:
                                safe_label = safe_label.replace(char, '')
                            safe_label = safe_label.strip()
                            errors.append(
                                f"Unsafe edge label '|{edge_label}|' contains '{unsafe_char}'. "
                                f"Use simple label: |{safe_label}| or create a separate node for complex paths."
                            )
                            break

        # Check sequenceDiagram syntax
        if code.startswith("sequenceDiagram"):
            if "->" not in code and "->>" not in code:
                errors.append("sequenceDiagram needs arrows like: Alice->>Bob: Hello")

        # Warning for common mistakes
        if "graph TD" in code and "TB" not in code:
            pass  # TD (top-down) is valid
        elif "graph TB" in code:
            pass  # TB (top-bottom) is valid
        elif "graph LR" in code:
            pass  # LR (left-right) is valid
        elif "graph RL" in code:
            pass  # RL (right-left) is valid
        elif "graph" in code and not any(d in code for d in ["TD", "TB", "LR", "RL", "BT"]):
            warnings.append("graph should specify direction: graph TD, graph LR, etc.")

        valid = len(errors) == 0

        result = {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "diagram_type": next((dt for dt in diagram_types if code.startswith(dt)), "unknown")
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error validating Mermaid syntax: {e}")
        return json.dumps({
            "valid": False,
            "errors": [f"Validation error: {str(e)}"],
            "warnings": []
        })


# ============================================================================
# TOOL BINDING HELPERS - Bind repo_path to simplify LLM tool usage
# ============================================================================

def make_bound_tools_for_code_explorer(repo_path: str) -> List:
    """
    Create tools for Code Explorer with repo_path pre-bound.
    This simplifies the tool signatures the LLM sees.

    Args:
        repo_path: Absolute path to repository root

    Returns:
        List of tool instances with bound repo_path
    """
    # Create wrapper functions with repo_path bound
    @tool
    def list_directory(relative_path: str = ".") -> str:
        """List contents of a directory. Args: relative_path (str, default '.'): Path from repo root"""
        return list_directory_tool.func(repo_path=repo_path, relative_path=relative_path)

    @tool
    def read_file(
        file_path: str,
        max_lines: int = None,
        strategy: Literal["full", "smart", "pattern_window"] = "pattern_window"
    ) -> str:
        """Read a file. Args: file_path (str), max_lines (int, optional), strategy (full|smart|pattern_window, default: pattern_window)"""
        return read_file_tool.func(
            repo_path=repo_path,
            file_path=file_path,
            max_lines=max_lines,
            strategy=strategy
        )

    @tool
    def detect_languages() -> str:
        """Detect programming languages in the repository. No arguments needed."""
        return detect_languages_tool.func(repo_path=repo_path)

    @tool
    def extract_dependencies() -> str:
        """Extract dependencies from package files (requirements.txt, package.json, etc.). No arguments needed."""
        return extract_dependencies_tool.func(repo_path=repo_path)

    @tool
    def analyze_code_structure(file_path: str) -> str:
        """Analyze code structure (functions, classes, imports). Args: file_path (str): Relative path from repo root"""
        return analyze_code_structure_tool.func(repo_path=repo_path, file_path=file_path)

    return [list_directory, read_file, detect_languages, extract_dependencies, analyze_code_structure]


def make_bound_tools_for_planner(repo_path: str) -> List:
    """
    Create tools for Planner with repo_path pre-bound.

    Args:
        repo_path: Absolute path to repository root

    Returns:
        List of tool instances with bound repo_path
    """
    # Create wrapper functions with repo_path bound
    @tool
    def list_directory(relative_path: str = ".") -> str:
        """List contents of a directory. Args: relative_path (str, default '.')"""
        return list_directory_tool.func(repo_path=repo_path, relative_path=relative_path)

    @tool
    def read_file(
        file_path: str,
        max_lines: int = None,
        strategy: Literal["full", "smart", "pattern_window"] = "pattern_window"
    ) -> str:
        """Read a file. Args: file_path (str), max_lines (int, optional), strategy (full|smart|pattern_window, default: pattern_window)"""
        return read_file_tool.func(
            repo_path=repo_path,
            file_path=file_path,
            max_lines=max_lines,
            strategy=strategy
        )

    @tool
    def detect_languages() -> str:
        """Detect programming languages. No arguments."""
        return detect_languages_tool.func(repo_path=repo_path)

    @tool
    def extract_dependencies() -> str:
        """Extract dependencies from package files. No arguments."""
        return extract_dependencies_tool.func(repo_path=repo_path)

    @tool
    def analyze_code_structure(file_path: str) -> str:
        """Analyze code structure. Args: file_path (str)"""
        return analyze_code_structure_tool.func(repo_path=repo_path, file_path=file_path)

    @tool
    def find_ui_files() -> str:
        """Check if project has UI/frontend components. No arguments."""
        return find_ui_files_tool.func(repo_path=repo_path)

    @tool
    def find_docker_files() -> str:
        """Check for Docker deployment files. No arguments."""
        return find_docker_files_tool.func(repo_path=repo_path)

    @tool
    def find_config_files() -> str:
        """Find configuration files (.env, config files). No arguments."""
        return find_config_files_tool.func(repo_path=repo_path)

    return [list_directory, read_file, detect_languages, extract_dependencies, analyze_code_structure,
            find_ui_files, find_docker_files, find_config_files]


def make_bound_tools_for_writer(repo_path: str) -> List:
    """
    Create tools for Writer with repo_path pre-bound.

    Args:
        repo_path: Absolute path to repository root

    Returns:
        List of StructuredTool instances with bound repo_path
    """
    # Same as code explorer
    return make_bound_tools_for_code_explorer(repo_path)


def make_bound_tools_for_diagram_generator(repo_path: str) -> List:
    """
    Create tools for Diagram Generator with repo_path pre-bound.

    FIXED: Adds validate_mermaid_syntax wrapper (without _tool suffix) to match prompt.

    Args:
        repo_path: Absolute path to repository root

    Returns:
        List of tool instances with bound repo_path
    """
    # Create wrapper functions with repo_path bound
    @tool
    def list_directory(relative_path: str = ".") -> str:
        """List contents of a directory. Args: relative_path (str, default '.')"""
        return list_directory_tool.func(repo_path=repo_path, relative_path=relative_path)

    @tool
    def read_file(
        file_path: str,
        max_lines: int = None,
        strategy: Literal["full", "smart", "pattern_window"] = "pattern_window"
    ) -> str:
        """Read a file. Args: file_path (str), max_lines (int, optional), strategy (full|smart|pattern_window, default: pattern_window)"""
        return read_file_tool.func(
            repo_path=repo_path,
            file_path=file_path,
            max_lines=max_lines,
            strategy=strategy
        )

    @tool
    def detect_languages() -> str:
        """Detect programming languages. No arguments."""
        return detect_languages_tool.func(repo_path=repo_path)

    @tool
    def find_entry_points() -> str:
        """Find main entry point files (main.py, server.py, index.js, etc.). No arguments."""
        return find_entry_points_tool.func(repo_path=repo_path)

    @tool
    def find_api_routes(entry_file: str) -> str:
        """Find API routes in an entry file. Args: entry_file (str): Relative path to entry file"""
        return find_api_routes_tool.func(repo_path=repo_path, entry_file=entry_file)

    @tool
    def find_docker_files() -> str:
        """Check for Docker files. No arguments."""
        return find_docker_files_tool.func(repo_path=repo_path)

    # FIXED: Add wrapper for validate_mermaid_syntax (without _tool suffix)
    # This matches the tool name used in the diagram generator prompt
    @tool
    def validate_mermaid_syntax(mermaid_code: str) -> str:
        """
        Validate Mermaid diagram syntax with strict Mermaid 8.14.0 render-safe checks.

        CRITICAL: Use this to validate EVERY diagram before finalizing output.

        Args:
            mermaid_code (str): The complete Mermaid diagram code to validate

        Returns:
            JSON with {"valid": bool, "errors": [...], "warnings": [...]}
        """
        return validate_mermaid_syntax_tool.func(mermaid_code=mermaid_code)

    return [list_directory, read_file, detect_languages, find_entry_points, find_api_routes,
            find_docker_files, validate_mermaid_syntax]
