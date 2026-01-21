"""
Git Service - Handles repository cloning and cleanup
"""

import os
import shutil
import logging
import re
import requests
from typing import Tuple, Dict, Optional, Callable
from git import Repo, GitCommandError, RemoteProgress
from config import settings
import uuid

logger = logging.getLogger(__name__)


def parse_github_url(url: str) -> Dict[str, Optional[str]]:
    """
    Parse GitHub URL to extract components

    Supports:
    - Base repo: https://github.com/owner/repo
    - Base repo with .git: https://github.com/owner/repo.git
    - Tree URL: https://github.com/owner/repo/tree/branch
    - Subfolder URL: https://github.com/owner/repo/tree/branch/path/to/folder

    Args:
        url: GitHub URL

    Returns:
        Dict with keys: owner, repo, branch, subfolder, clone_url, is_subfolder

    Raises:
        ValueError: If URL is invalid
    """
    # Remove trailing slashes
    url = url.rstrip('/')

    # Pattern: https://github.com/owner/repo[.git][/tree/branch[/path]]
    pattern = r'^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/tree/([^/]+)(?:/(.*))?)?$'

    match = re.match(pattern, url)

    if not match:
        raise ValueError(
            f"Invalid GitHub URL format. Expected: https://github.com/owner/repo[/tree/branch[/path]]\n"
            f"Got: {url}"
        )

    owner, repo, branch, subfolder = match.groups()

    # Clean repo name (remove .git if present)
    repo = repo.replace('.git', '')

    result = {
        "owner": owner,
        "repo": repo,
        "branch": branch or "main",  # Default to main if not specified
        "subfolder": subfolder if subfolder else None,
        "clone_url": f"https://github.com/{owner}/{repo}.git",
        "is_subfolder": bool(subfolder),
        "display_name": subfolder.split('/')[-1] if subfolder else repo
    }

    logger.info(f"Parsed URL: {url} -> {result}")

    return result


class CloneProgress(RemoteProgress):
    """Progress reporter for git clone operations"""

    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.callback = callback
        self._last_message = ""

    def update(self, op_code, cur_count, max_count=None, message=''):
        """Called by GitPython during clone operation"""
        if self.callback:
            # Parse operation
            if op_code & self.COUNTING:
                msg = f"📊 Counting objects: {cur_count}"
            elif op_code & self.COMPRESSING:
                msg = f"🗜️ Compressing objects: {cur_count}/{max_count}" if max_count else f"🗜️ Compressing objects: {cur_count}"
            elif op_code & self.RECEIVING:
                percentage = int((cur_count / max_count * 100)) if max_count else 0
                msg = f"⬇️ Receiving objects: {cur_count}/{max_count} ({percentage}%)"
            elif op_code & self.RESOLVING:
                percentage = int((cur_count / max_count * 100)) if max_count else 0
                msg = f"🔧 Resolving deltas: {cur_count}/{max_count} ({percentage}%)"
            else:
                msg = f"⏳ Cloning: {cur_count}"

            # Only report if message changed (avoid spam)
            if msg != self._last_message:
                self._last_message = msg
                self.callback(msg)


class GitService:
    """Service for Git operations"""

    def __init__(self):
        self.temp_dir = settings.TEMP_REPO_DIR
        os.makedirs(self.temp_dir, exist_ok=True)

    def clone_repository(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[str, Dict[str, str]]:
        """
        Clone a Git repository to a temporary directory

        Args:
            repo_url: GitHub repository URL
            branch: Optional branch name to checkout after cloning
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (repo_path, metadata_dict)
        """
        try:
            # Generate unique directory name
            repo_id = str(uuid.uuid4())
            repo_path = os.path.join(self.temp_dir, repo_id)

            logger.info(f"Cloning repository: {repo_url}")

            # Check repository size before cloning
            try:
                # Extract owner and repo name from URL
                # Format: https://github.com/owner/repo or https://github.com/owner/repo.git
                parts = repo_url.rstrip('/').replace('.git', '').split('/')
                if 'github.com' in repo_url and len(parts) >= 2:
                    owner = parts[-2]
                    repo_name = parts[-1]

                    # Query GitHub API for repo info
                    api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
                    headers = {}
                    if settings.GITHUB_TOKEN:
                        headers['Authorization'] = f'token {settings.GITHUB_TOKEN}'

                    response = requests.get(api_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        repo_data = response.json()
                        repo_size_kb = repo_data.get('size', 0)  # GitHub returns size in KB
                        repo_size_bytes = repo_size_kb * 1024

                        max_size_gb = settings.MAX_REPO_SIZE / (1024 ** 3)
                        if repo_size_bytes > settings.MAX_REPO_SIZE:
                            error_msg = f"Repository size ({repo_size_bytes / (1024 ** 3):.2f}GB) exceeds maximum allowed size ({max_size_gb:.0f}GB). Please try a smaller repository."
                            logger.error(error_msg)
                            if progress_callback:
                                progress_callback(f"❌ {error_msg}")
                            raise ValueError(error_msg)
                        else:
                            logger.info(f"Repository size check passed: {repo_size_bytes / (1024 ** 3):.2f}GB")
                            if progress_callback:
                                progress_callback(f"✅ Repository size: {repo_size_bytes / (1024 ** 3):.2f}GB")
            except requests.RequestException as e:
                # Don't fail if we can't check size, just log warning
                logger.warning(f"Could not verify repository size: {e}")
            except ValueError:
                # Re-raise size limit errors
                raise

            if progress_callback:
                progress_callback(f"🚀 Starting clone of {repo_url}")

            # Clone the repository with progress tracking
            progress = CloneProgress(callback=progress_callback)

            # Add GitHub PAT authentication for private repos
            clone_url = repo_url
            if settings.GITHUB_TOKEN and 'github.com' in repo_url:
                # Inject GitHub PAT into URL: https://TOKEN@github.com/owner/repo.git
                clone_url = repo_url.replace('https://github.com/', f'https://{settings.GITHUB_TOKEN}@github.com/')
                logger.info(f"Using authenticated clone for private repository")

            repo = Repo.clone_from(clone_url, repo_path, progress=progress)

            if progress_callback:
                progress_callback(f"✅ Clone completed successfully")

            # Checkout specified branch if provided
            if branch:
                try:
                    current_branch = None
                    try:
                        current_branch = repo.active_branch.name
                    except TypeError:
                        # Detached HEAD state or no branches yet
                        pass

                    # Only checkout if not already on the requested branch
                    if current_branch != branch:
                        # Check if branch exists locally
                        if branch in [ref.name for ref in repo.heads]:
                            repo.git.checkout(branch)
                        else:
                            # Create local branch tracking remote branch
                            repo.git.checkout('-b', branch, f'origin/{branch}')

                        logger.info(f"Checked out branch: {branch}")
                        if progress_callback:
                            progress_callback(f"✅ Checked out branch: {branch}")
                except Exception as e:
                    logger.warning(f"Failed to checkout branch {branch}: {e}")
                    if progress_callback:
                        progress_callback(f"⚠️ Warning: Could not checkout branch {branch}, using default branch")

            # Extract metadata
            metadata = {
                "repo_url": repo_url,
                "repo_name": repo_url.split('/')[-1].replace('.git', ''),
                "default_branch": repo.active_branch.name,
                "repo_path": repo_path
            }

            logger.info(f"Repository cloned successfully to: {repo_path}")

            return repo_path, metadata

        except GitCommandError as e:
            logger.error(f"Git clone failed: {e}")

            # Parse git error and provide user-friendly message
            error_message = str(e)
            user_friendly_message = None

            # Exit code 128: Repository not found or access denied
            if "exit code(128)" in error_message:
                if "not found" in error_message.lower() or "could not read" in error_message.lower():
                    user_friendly_message = "Repository not found. Please check the URL and verify the repository exists."
                elif "authentication" in error_message.lower() or "permission" in error_message.lower():
                    user_friendly_message = "Access denied. This repository may be private or you may not have permission to access it."
                else:
                    user_friendly_message = "Repository not found or access denied. Please verify the URL and your permissions."

            # Exit code 403: Rate limit or access forbidden
            elif "403" in error_message:
                user_friendly_message = "Access forbidden. You may have hit GitHub's rate limit or don't have permission to access this repository."

            # Network errors
            elif "connection" in error_message.lower() or "network" in error_message.lower():
                user_friendly_message = "Network error. Please check your internet connection and try again."

            # Use user-friendly message if detected, otherwise use generic message
            final_message = user_friendly_message or f"Failed to clone repository: {str(e)}"

            if progress_callback:
                progress_callback(f"❌ {final_message}")

            raise ValueError(final_message)

        except Exception as e:
            logger.error(f"Unexpected error cloning repository: {e}")
            error_message = f"Unexpected error while cloning: {str(e)}"

            if progress_callback:
                progress_callback(f"❌ {error_message}")

            raise ValueError(error_message)

    def cleanup_repository(self, repo_path: str) -> bool:
        """
        Clean up cloned repository

        Args:
            repo_path: Path to the repository

        Returns:
            True if successful
        """
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path, ignore_errors=True)
                logger.info(f"Cleaned up repository: {repo_path}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to cleanup repository {repo_path}: {e}")
            return False
