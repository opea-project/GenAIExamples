"""
Smart Project Detector
Analyzes repository structure and identifies individual projects within a monorepo
Includes grouping logic to treat parent folders (with api/ui children) as single projects
"""

import os
import logging
import fnmatch
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Project indicators - files that typically mark a project root
PROJECT_INDICATORS = {
    "python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile", "poetry.lock"],
    "nodejs": ["package.json"],
    "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
    "go": ["go.mod"],
    "rust": ["Cargo.toml"],
    "php": ["composer.json"],
    "ruby": ["Gemfile"],
    "dotnet": ["*.csproj", "*.sln", "*.fsproj", "*.vbproj"],
    "cpp": ["CMakeLists.txt", "Makefile"],
    "r": ["DESCRIPTION", "NAMESPACE"],
}

# Directories to ignore
IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", "venv", "env", ".venv",
    "dist", "build", ".idea", ".vscode", "target", "out",
    ".next", ".nuxt", "coverage", ".pytest_cache"
}

# Common subproject folder names (generic patterns, not hardcoded to specific names)
SUBPROJECT_PATTERNS = ["api", "ui", "frontend", "backend", "web", "server", "client", "app", "service"]


class ProjectDetector:
    """Detects and analyzes projects within a repository"""

    def __init__(self, repo_path: str, max_depth: int = 3, group_subprojects: bool = True):
        """
        Args:
            repo_path: Path to repository root
            max_depth: Maximum depth to scan
            group_subprojects: If True, group api/ui siblings under parent project
        """
        self.repo_path = Path(repo_path)
        self.max_depth = max_depth
        self.group_subprojects = group_subprojects

    def detect_projects(self) -> Dict[str, Any]:
        """
        Scan repository and detect individual projects

        Returns:
            Dict with:
                - is_monorepo: bool
                - project_count: int
                - projects: List[Dict] with project metadata
                - skipped_folders: List[Dict] with skipped folder info and reasons
        """
        projects = []
        skipped_folders = []

        # Check if root itself is a project
        root_project = self._analyze_directory(self.repo_path, depth=0)
        if root_project:
            projects.append(root_project)

        # Scan subdirectories
        self._scan_recursive(self.repo_path, projects, depth=1, skipped=skipped_folders)

        # Apply grouping logic if enabled
        if self.group_subprojects:
            projects = self._group_composite_projects(projects)

        # Filter out nested skipped folders (children of other skipped folders)
        skipped_folders = self._filter_nested_skipped_folders(skipped_folders)

        # Filter out standalone media/asset folders when there's a doc folder
        skipped_folders = self._filter_redundant_asset_folders(skipped_folders)

        # Classify as monorepo or single project
        is_monorepo = len(projects) > 1

        logger.info(f"Detected {len(projects)} project(s) - Monorepo: {is_monorepo}")
        if skipped_folders:
            logger.info(f"Skipped {len(skipped_folders)} folder(s) without project indicators")

        return {
            "is_monorepo": is_monorepo,
            "project_count": len(projects),
            "projects": projects,
            "skipped_folders": skipped_folders
        }

    def _scan_recursive(self, directory: Path, projects: List[Dict], depth: int, skipped: List[Dict] = None):
        """Recursively scan directories for projects"""
        if depth > self.max_depth:
            return

        if skipped is None:
            skipped = []

        try:
            for item in directory.iterdir():
                # Skip ignored directories
                if not item.is_dir() or item.name in IGNORE_DIRS or item.name.startswith('.'):
                    continue

                # Check if this directory is a project
                project_info = self._analyze_directory(item, depth)
                if project_info:
                    projects.append(project_info)
                    # Don't scan deeper if we found a project (avoid nested projects)
                    continue

                # Directory has no project indicators - analyze why and track it
                skip_reason = self._analyze_skipped_folder(item)
                if skip_reason:
                    rel_path = item.relative_to(self.repo_path)
                    skipped.append({
                        "name": item.name,
                        "path": str(rel_path),
                        "reason": skip_reason["reason"],
                        "details": skip_reason["details"],
                        "depth": depth
                    })

                # Continue scanning deeper
                self._scan_recursive(item, projects, depth + 1, skipped)

        except PermissionError:
            logger.warning(f"Permission denied: {directory}")

    def _analyze_skipped_folder(self, directory: Path) -> Dict[str, str]:
        """
        Analyze why a folder was skipped (no project indicators)

        Returns:
            Dict with 'reason' and 'details', or None if folder should be ignored
        """
        try:
            items = list(directory.iterdir())
            files = [f for f in items if f.is_file()]
            subdirs = [d for d in items if d.is_dir() and d.name not in IGNORE_DIRS]

            # Empty folder
            if not files and not subdirs:
                return {
                    "reason": "Empty folder",
                    "details": "Contains no files or subfolders"
                }

            # Analyze file types
            doc_extensions = {'.md', '.txt', '.rst', '.adoc', '.pdf'}
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.bmp'}

            doc_files = [f for f in files if f.suffix.lower() in doc_extensions]
            image_files = [f for f in files if f.suffix.lower() in image_extensions]
            other_files = [f for f in files if f.suffix.lower() not in doc_extensions | image_extensions]

            # Documentation-only folder
            if doc_files and not other_files and not image_files:
                return {
                    "reason": "Documentation only",
                    "details": f"Contains only documentation files ({len(doc_files)} markdown/text files)"
                }

            # Images/media-only folder
            if image_files and not other_files and not doc_files:
                return {
                    "reason": "Media only",
                    "details": f"Contains only image files ({len(image_files)} images)"
                }

            # Mixed docs and images, no code
            if (doc_files or image_files) and not other_files and len(files) < 5:
                return {
                    "reason": "Documentation and media",
                    "details": f"Contains {len(doc_files)} docs, {len(image_files)} images, no code"
                }

            # Has files but no project indicators
            if files and not subdirs:
                return {
                    "reason": "No project indicators",
                    "details": f"Contains {len(files)} files but no package.json, requirements.txt, etc."
                }

            # Has subdirectories - likely being scanned recursively
            # Don't report these as skipped since we'll scan their children
            return None

        except PermissionError:
            return {
                "reason": "Permission denied",
                "details": "Cannot access folder contents"
            }

    def _analyze_directory(self, directory: Path, depth: int) -> Dict[str, Any]:
        """
        Analyze a directory to determine if it's a project

        Returns:
            Project metadata dict if project detected, None otherwise
        """
        try:
            files = [f.name for f in directory.iterdir() if f.is_file()]
        except PermissionError:
            return None

        # Check for project indicators (with glob pattern support)
        detected_types = []
        indicator_files = []

        for proj_type, indicators in PROJECT_INDICATORS.items():
            for indicator in indicators:
                # Support glob patterns like *.csproj
                if '*' in indicator or '?' in indicator:
                    # Use fnmatch for glob patterns
                    matches = [f for f in files if fnmatch.fnmatch(f, indicator)]
                    if matches:
                        detected_types.append(proj_type)
                        indicator_files.extend(matches)
                else:
                    # Exact match
                    if indicator in files:
                        detected_types.append(proj_type)
                        indicator_files.append(indicator)

        # If we found project indicators, it's likely a project
        if detected_types:
            # Calculate relative path from repo root
            rel_path = directory.relative_to(self.repo_path)

            # Estimate project complexity
            file_count = len(files)
            dir_count = len([d for d in directory.iterdir() if d.is_dir() and d.name not in IGNORE_DIRS])

            return {
                "name": directory.name,
                "path": str(rel_path) if str(rel_path) != "." else "/",
                "full_path": str(directory),
                "types": list(set(detected_types)),  # Remove duplicates
                "indicators": indicator_files,
                "depth": depth,
                "file_count": file_count,
                "dir_count": dir_count,
                "is_root": depth == 0,
                "is_composite": False  # Will be updated by grouping logic
            }

        return None

    def _group_composite_projects(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group projects that are subprojects under a common parent.

        Logic: If multiple sibling folders at the same depth are projects,
        and they match common subproject patterns (api, ui, frontend, backend, etc.),
        group them under their parent folder as a single composite project.

        Example:
            rag-chatbot/api    (project)
            rag-chatbot/ui     (project)
            → Groups into: rag-chatbot (composite project)

        Returns:
            New list with grouped projects
        """
        # Build a parent-to-children mapping
        parent_map: Dict[str, List[Dict]] = {}

        for project in projects:
            project_path = Path(project["full_path"])
            parent_path = str(project_path.parent)

            if parent_path not in parent_map:
                parent_map[parent_path] = []
            parent_map[parent_path].append(project)

        # Identify parents with multiple subproject children
        grouped_projects = []
        processed_projects = set()

        for parent_path, children in parent_map.items():
            # Skip root-level projects (no grouping needed)
            if len(children) == 1:
                if children[0]["path"] not in processed_projects:
                    grouped_projects.append(children[0])
                    processed_projects.add(children[0]["path"])
                continue

            # Check if these siblings look like subprojects (api, ui, etc.)
            child_names = [child["name"].lower() for child in children]
            subproject_count = sum(1 for name in child_names if any(pattern in name for pattern in SUBPROJECT_PATTERNS))

            # If 2+ children match subproject patterns, group them under parent
            if len(children) >= 2 and subproject_count >= 2:
                parent_dir = Path(parent_path)
                parent_name = parent_dir.name

                # Skip if parent is the repo root
                if str(parent_dir) == str(self.repo_path):
                    # Don't group root-level subprojects, keep them separate
                    for child in children:
                        if child["path"] not in processed_projects:
                            grouped_projects.append(child)
                            processed_projects.add(child["path"])
                    continue

                # Create composite project for the parent
                composite_project = {
                    "name": parent_name,
                    "path": str(parent_dir.relative_to(self.repo_path)),
                    "full_path": str(parent_dir),
                    "types": list(set([t for child in children for t in child["types"]])),
                    "indicators": [f"{child['name']}/{ind}" for child in children for ind in child["indicators"]],
                    "depth": children[0]["depth"] - 1,  # Parent is one level up
                    "file_count": sum(child["file_count"] for child in children),
                    "dir_count": len(children),
                    "is_root": False,
                    "is_composite": True,
                    "subprojects": [child["name"] for child in children]
                }

                grouped_projects.append(composite_project)

                # Mark children as processed
                for child in children:
                    processed_projects.add(child["path"])

                logger.info(f"Grouped {len(children)} subprojects under '{parent_name}': {', '.join(child_names)}")

            else:
                # Not a composite project pattern, keep children separate
                for child in children:
                    if child["path"] not in processed_projects:
                        grouped_projects.append(child)
                        processed_projects.add(child["path"])

        return grouped_projects

    def _filter_nested_skipped_folders(self, skipped_folders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out skipped folders that are children of other skipped folders.
        Only keep top-level skipped folders to avoid redundant information.

        Example: If 'code-generation' is skipped, don't also show 'code-generation/src' and 'code-generation/img'
        """
        if not skipped_folders:
            return []

        # Sort by depth (shallowest first) and then by path
        sorted_folders = sorted(skipped_folders, key=lambda x: (x['depth'], x['path']))

        filtered = []
        for folder in sorted_folders:
            # Normalize path using Path to handle both / and \ correctly
            folder_path = Path(folder['path'])

            # Check if this folder is a child of any already-added skipped folder
            is_nested = False
            for parent in filtered:
                parent_path = Path(parent['path'])
                # Check if folder_path is a child of parent_path
                try:
                    folder_path.relative_to(parent_path)
                    # If no exception, folder_path is under parent_path
                    is_nested = True
                    break
                except ValueError:
                    # Not a subpath, continue checking
                    pass

            # Only add if it's not nested under another skipped folder
            if not is_nested:
                filtered.append(folder)

        logger.info(f"Filtered nested folders: {len(skipped_folders)} -> {len(filtered)}")
        return filtered

    def _filter_redundant_asset_folders(self, skipped_folders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out standalone asset folders (images, media) when there's a documentation folder.

        Rationale: If a repo has both a 'docs' folder and an 'images' folder at the same level,
        the images likely belong to the docs, so we only need to show the docs folder.
        """
        if not skipped_folders:
            return []

        # Check if there's at least one documentation folder
        has_doc_folder = any(
            folder['reason'] in ['Documentation only', 'Documentation and media']
            for folder in skipped_folders
        )

        # If there's a doc folder, filter out standalone media folders
        if has_doc_folder:
            filtered = [
                folder for folder in skipped_folders
                if folder['reason'] != 'Media only'
            ]
            if len(filtered) < len(skipped_folders):
                logger.info(f"Filtered asset folders: {len(skipped_folders)} -> {len(filtered)} (removed media-only folders)")
            return filtered

        # No doc folder, keep all skipped folders
        return skipped_folders


def detect_projects(repo_path: str) -> Dict[str, Any]:
    """
    Convenience function to detect projects in a repository

    Args:
        repo_path: Path to the cloned repository

    Returns:
        Dict with:
            - is_monorepo: bool
            - project_count: int
            - projects: List[Dict] with project metadata
    """
    detector = ProjectDetector(repo_path, group_subprojects=True)
    return detector.detect_projects()
