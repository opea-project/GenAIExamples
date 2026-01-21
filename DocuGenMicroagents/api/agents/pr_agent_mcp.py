"""
PR Agent with TRUE MCP Integration
Uses official GitHub MCP server via MCP protocol (not direct API calls)
With full ReAct-style logging (Thought → Action → Observation)
"""

import logging
import re
import json
from typing import Dict, Any
from datetime import datetime

from models import get_log_manager, LogType
from mcp_client import get_github_mcp_client

logger = logging.getLogger(__name__)


async def create_pr_with_mcp(
    repo_full_name: str,
    readme_content: str,
    project_name: str,
    base_branch: str,
    github_token: str,
    job_id: str
) -> Dict[str, Any]:
    """
    Create GitHub PR using TRUE MCP protocol with ReAct logging

    This function:
    1. Connects to GitHub MCP server (Docker)
    2. Discovers available tools via MCP
    3. Calls tools to create branch, commit, and PR
    4. Uses stdio protocol (not direct API)
    5. Logs full ReAct cycle (Thought → Action → Observation)

    Args:
        repo_full_name: Repository "owner/repo"
        readme_content: Generated README content
        project_name: Project name for PR title
        base_branch: Base branch to create PR against (e.g., "main" or "dev")
        github_token: GitHub Personal Access Token
        job_id: Job ID for logging

    Returns:
        Dict with success status, PR URL, and details
    """
    log_manager = get_log_manager()

    try:
        # Log start
        await log_manager.log_async(
            job_id=job_id,
            log_type=LogType.AGENT_START,
            message="PR Agent initialized with MCP protocol",
            agent_name="PR Agent (MCP)"
        )

        # 💭 Thought: Planning to connect
        await log_manager.log_async(
            job_id=job_id,
            log_type=LogType.AGENT_THINKING,
            message=f"💭 Thought: I need to connect to GitHub MCP server for {repo_full_name}",
            agent_name="PR Agent (MCP)"
        )

        # Get MCP client
        mcp_client = get_github_mcp_client(github_token)

        # Connect to GitHub MCP server (Docker container via stdio)
        async with mcp_client.connect() as session:
            # 💭 Thought: Discovering tools
            await log_manager.log_async(
                job_id=job_id,
                log_type=LogType.AGENT_THINKING,
                message="💭 Thought: Connected to MCP server. I need to discover available GitHub tools",
                agent_name="PR Agent (MCP)"
            )

            # List available tools
            tools = await mcp_client.list_available_tools()
            logger.info(f"Available MCP tools: {tools}")

            # 📊 Observation: Tools discovered
            await log_manager.log_async(
                job_id=job_id,
                log_type=LogType.AGENT_OBSERVATION,
                message=f"📊 Observation: Found {len(tools)} GitHub MCP tools including: {', '.join(tools[:5])}...",
                agent_name="PR Agent (MCP)",
                metadata={"tools_count": len(tools), "tools": tools}
            )

            # Generate unique branch name with project name
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            # Create slug from project name (lowercase, replace spaces/special chars with hyphens)
            project_slug = re.sub(r'[^a-z0-9]+', '-', project_name.lower()).strip('-')
            branch_name = f"docs/{project_slug}-readme-{timestamp}"

            # Parse repo owner and name
            owner, repo = repo_full_name.split("/")

            # Extract actual project name from README title (H1 or H2)
            readme_title = project_name  # fallback to provided name
            lines = readme_content.split('\n')
            for line in lines[:15]:  # Check first 15 lines for title
                # Look for H1 (# Title) or H2 (## Title)
                if line.startswith('# ') and not line.startswith('## '):
                    readme_title = line[2:].strip()
                    break
                elif line.startswith('## '):
                    # H2 title found - extract it
                    readme_title = line[3:].strip()
                    break

            # === STEP 1: Create Branch ===

            # 💭 Thought: Need to create branch
            await log_manager.log_async(
                job_id=job_id,
                log_type=LogType.AGENT_THINKING,
                message=f"💭 Thought: I need to create a new branch '{branch_name}' from {base_branch}",
                agent_name="PR Agent (MCP)"
            )

            # 🔧 Action: Create branch
            await log_manager.log_async(
                job_id=job_id,
                log_type=LogType.AGENT_ACTION,
                message=f"🔧 Action: create_branch(owner={owner}, repo={repo}, branch={branch_name}, from_branch={base_branch})",
                agent_name="PR Agent (MCP)",
                metadata={"tool": "create_branch", "params": {"owner": owner, "repo": repo, "branch": branch_name, "from_branch": base_branch}}
            )

            try:
                branch_result = await mcp_client.call_tool(
                    "create_branch",
                    {
                        "owner": owner,
                        "repo": repo,
                        "branch": branch_name,
                        "from_branch": base_branch
                    }
                )
                logger.info(f"Branch creation result: {branch_result}")

                # 📊 Observation: Branch created
                await log_manager.log_async(
                    job_id=job_id,
                    log_type=LogType.AGENT_OBSERVATION,
                    message=f"📊 Observation: Branch '{branch_name}' created successfully from {base_branch}",
                    agent_name="PR Agent (MCP)",
                    metadata={"branch_created": True, "branch_name": branch_name}
                )
            except Exception as e:
                logger.warning(f"Branch creation via MCP failed: {e}")
                # 📊 Observation: Branch might exist
                await log_manager.log_async(
                    job_id=job_id,
                    log_type=LogType.AGENT_OBSERVATION,
                    message=f"📊 Observation: Branch creation failed ({str(e)}). Branch may already exist - continuing anyway",
                    agent_name="PR Agent (MCP)",
                    metadata={"branch_created": False, "error": str(e)}
                )

            # === STEP 2: Commit README.md using push_files (FOOLPROOF - No SHA needed) ===

            # 💭 Thought: Need to commit README
            await log_manager.log_async(
                job_id=job_id,
                log_type=LogType.AGENT_THINKING,
                message=f"💭 Thought: I need to commit README.md to branch '{branch_name}' using push_files (no SHA required)",
                agent_name="PR Agent (MCP)"
            )

            # Use push_files tool (more reliable, no SHA needed)
            push_params = {
                "owner": owner,
                "repo": repo,
                "branch": branch_name,
                "files": [
                    {
                        "path": "README.md",
                        "content": readme_content
                    }
                ],
                "message": f"docs: Updated README for {readme_title}"
            }

            logger.info(f"Using push_files to commit README.md to branch '{branch_name}'")

            # 🔧 Action: Commit file using push_files
            await log_manager.log_async(
                job_id=job_id,
                log_type=LogType.AGENT_ACTION,
                message=f"🔧 Action: push_files(owner={owner}, repo={repo}, branch={branch_name}, files=[README.md])",
                agent_name="PR Agent (MCP)",
                metadata={"tool": "push_files", "params": push_params, "content_length": len(readme_content)}
            )

            commit_success = False
            try:
                commit_result = await mcp_client.call_tool(
                    "push_files",
                    push_params
                )
                logger.info(f"Commit result: {commit_result}")

                # Check if commit was successful
                if commit_result and not (hasattr(commit_result, 'isError') and commit_result.isError):
                    commit_success = True
                    # 📊 Observation: File committed
                    await log_manager.log_async(
                        job_id=job_id,
                        log_type=LogType.AGENT_OBSERVATION,
                        message=f"📊 Observation: README.md committed successfully to branch '{branch_name}'",
                        agent_name="PR Agent (MCP)",
                        metadata={"file_committed": True}
                    )
                else:
                    error_text = str(commit_result.content[0].text if hasattr(commit_result, 'content') else commit_result)
                    logger.error(f"File commit returned error: {error_text}")
                    await log_manager.log_async(
                        job_id=job_id,
                        log_type=LogType.AGENT_OBSERVATION,
                        message=f"📊 Observation: Failed to commit README.md - {error_text[:200]}",
                        agent_name="PR Agent (MCP)",
                        metadata={"file_committed": False, "error": error_text}
                    )
                    raise Exception(f"push_files failed: {error_text}")

            except Exception as e:
                logger.error(f"File commit failed: {e}")
                # 📊 Observation: Commit failed
                await log_manager.log_async(
                    job_id=job_id,
                    log_type=LogType.AGENT_OBSERVATION,
                    message=f"📊 Observation: Failed to commit README.md - {str(e)}",
                    agent_name="PR Agent (MCP)",
                    metadata={"file_committed": False, "error": str(e)}
                )
                raise

            # === STEP 3: Create Pull Request ===

            # 💭 Thought: Ready to create PR
            await log_manager.log_async(
                job_id=job_id,
                log_type=LogType.AGENT_THINKING,
                message=f"💭 Thought: README.md is committed. Now I need to create a pull request from '{branch_name}' to '{base_branch}'",
                agent_name="PR Agent (MCP)"
            )

            pr_body = f"""## Summary
This PR adds comprehensive AI-generated documentation for **{readme_title}**.

## What's Included
- **Project Overview** - High-level description and key features
- **Architecture** - System design with Mermaid diagrams
- **Installation Guide** - Step-by-step setup instructions with actual repository URLs
- **Configuration** - Environment variables and settings documentation
- **Deployment** - Quick start guide with Docker/manual deployment options
- **Troubleshooting** - Common issues and solutions
- **API Documentation** - Endpoints and usage examples (if applicable)

## About This Documentation
This README was automatically generated by **DocuGen Micro-Agents**, an advanced AI system that uses specialized agents to analyze your repository:

---
*Generated by DocuGen Micro-Agents AI-powered documentation with specialized micro-agent system*
- Agents Used: Code Explorer, API Reference, Call Graph Analyzer, Environment Config, Dependency Analyzer, Error Analysis, Planner, Mermaid Generator, QA Validator
- Integration: Model Context Protocol (MCP) for GitHub"""

            # 🔧 Action: Create PR
            await log_manager.log_async(
                job_id=job_id,
                log_type=LogType.AGENT_ACTION,
                message=f"🔧 Action: create_pull_request(owner={owner}, repo={repo}, title='docs: Updated README for {readme_title}', head={branch_name}, base={base_branch})",
                agent_name="PR Agent (MCP)",
                metadata={"tool": "create_pull_request", "params": {"owner": owner, "repo": repo, "head": branch_name, "base": base_branch}}
            )

            pr_url = None
            try:
                pr_result = await mcp_client.call_tool(
                    "create_pull_request",
                    {
                        "owner": owner,
                        "repo": repo,
                        "title": f"docs: Updated README for {readme_title}",
                        "body": pr_body,
                        "head": branch_name,
                        "base": base_branch
                    }
                )

                logger.info(f"PR creation result: {pr_result}")
                logger.info(f"PR result type: {type(pr_result)}")

                # Check if PR creation failed
                if hasattr(pr_result, 'isError') and pr_result.isError:
                    error_text = str(pr_result.content[0].text if hasattr(pr_result, 'content') else pr_result)
                    logger.error(f"PR creation returned error: {error_text}")
                    raise Exception(f"create_pull_request failed: {error_text}")

                # Extract PR URL from result
                if hasattr(pr_result, 'content') and pr_result.content:
                    if isinstance(pr_result.content, list) and len(pr_result.content) > 0:
                        result_text = str(pr_result.content[0].text if hasattr(pr_result.content[0], 'text') else pr_result.content[0])
                        logger.info(f"Extracted result_text: {result_text[:500]}")
                    else:
                        result_text = str(pr_result.content)
                        logger.info(f"Result content (non-list): {result_text[:500]}")

                    # Try multiple methods to extract URL
                    # Method 1: Parse as JSON
                    try:
                        data = json.loads(result_text)
                        pr_url = data.get("html_url")
                        logger.info(f"Extracted PR URL from JSON: {pr_url}")
                    except:
                        logger.info("Could not parse result as JSON, trying regex")
                        # Method 2: Regex search for GitHub PR URL
                        url_match = re.search(r'https://github\.com/[^\s"\'<>]+/pull/\d+', result_text)
                        if url_match:
                            pr_url = url_match.group(0)
                            logger.info(f"Extracted PR URL from regex: {pr_url}")
                        else:
                            # Method 3: Construct URL from owner/repo if PR number is available
                            pr_number_match = re.search(r'"number":\s*(\d+)', result_text)
                            if pr_number_match:
                                pr_number = pr_number_match.group(1)
                                pr_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}"
                                logger.info(f"Constructed PR URL from number: {pr_url}")

                # 📊 Observation: PR created
                await log_manager.log_async(
                    job_id=job_id,
                    log_type=LogType.AGENT_OBSERVATION,
                    message=f"📊 Observation: Pull request created successfully! URL: {pr_url or 'Check GitHub'}",
                    agent_name="PR Agent (MCP)",
                    metadata={"pr_created": True, "pr_url": pr_url}
                )

            except Exception as e:
                logger.error(f"PR creation failed: {e}")
                # 📊 Observation: PR creation failed
                await log_manager.log_async(
                    job_id=job_id,
                    log_type=LogType.AGENT_OBSERVATION,
                    message=f"📊 Observation: Failed to create pull request - {str(e)}",
                    agent_name="PR Agent (MCP)",
                    metadata={"pr_created": False, "error": str(e)}
                )
                raise

            # Log completion
            await log_manager.log_async(
                job_id=job_id,
                log_type=LogType.AGENT_COMPLETE,
                message=f"PR workflow complete! PR created at: {pr_url or 'Check GitHub'}",
                agent_name="PR Agent (MCP)",
                metadata={"pr_url": pr_url, "branch": branch_name}
            )

            return {
                "success": True,
                "pr_url": pr_url,
                "branch_name": branch_name,
                "output": f"Successfully created PR via MCP protocol: {pr_url or 'See GitHub'}"
            }

    except Exception as e:
        logger.error(f"MCP PR creation failed: {e}", exc_info=True)
        await log_manager.log_async(
            job_id=job_id,
            log_type=LogType.ERROR,
            message=f"MCP PR Agent error: {str(e)}",
            agent_name="PR Agent (MCP)"
        )

        return {
            "success": False,
            "pr_url": None,
            "branch_name": None,
            "output": f"Failed to create PR via MCP: {str(e)}"
        }
