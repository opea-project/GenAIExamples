"""
FastAPI Server for DocuGen AI
Provides REST API and SSE streaming for real-time agent visibility
"""

import asyncio
import json
import logging
import sys
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List

# Disable output buffering for real-time log streaming
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from config import settings
from models import (
    GenerateDocsRequest,
    GenerateDocsResponse,
    JobStatusResponse,
    ProjectSelectionRequest,
    ProjectSelectionResponse,
    LogType,
    get_log_manager
)
from workflow import get_workflow
from agents.pr_agent_mcp import create_pr_with_mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Job storage 
job_storage: Dict[str, Dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context for startup/shutdown"""
    logger.info("DocuGen AI starting up...")
    logger.info(f"Authentication mode: {settings.AUTH_MODE}")

    # Check if GitHub token is configured for MCP PR creation
    github_token = settings.GITHUB_TOKEN
    if github_token:
        logger.info("GitHub token configured - MCP PR creation enabled")
    else:
        logger.warning("GITHUB_TOKEN not configured - PR creation will be disabled")

    yield
    logger.info("DocuGen AI shutting down...")


# Initialize FastAPI
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "auth_mode": settings.AUTH_MODE.value
    }


@app.post("/api/generate-docs", response_model=GenerateDocsResponse)
async def generate_documentation(request: GenerateDocsRequest, background_tasks: BackgroundTasks):
    """
    Start documentation generation workflow

    Returns job_id for tracking and SSE streaming
    """
    try:
        job_id = str(uuid.uuid4())

        # Initialize job
        job_storage[job_id] = {
            "repo_url": str(request.repo_url),
            "status": "pending",
            "workflow_paused": False,
            "current_agent": None,
            "final_readme": None,
            "error": None,
            "awaiting_project_selection": False,
            "detected_projects": None
        }

        # Start workflow in background
        background_tasks.add_task(run_workflow, job_id, str(request.repo_url))

        logger.info(f"Documentation generation started: {job_id}")

        return GenerateDocsResponse(
            job_id=job_id,
            status="started",
            message="Documentation generation workflow started. Connect to SSE stream to monitor progress."
        )

    except Exception as e:
        logger.error(f"Failed to start workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def run_workflow(job_id: str, repo_url: str):
    """
    Run the documentation workflow
    Executes with human-in-the-loop interrupts
    """
    try:
        workflow = await get_workflow()

        # Initial state
        initial_state = {
            "job_id": job_id,
            "repo_url": repo_url,
            "repo_path": None,
            "repo_name": None,
            "default_branch": None,
            "is_monorepo": None,
            "detected_projects": None,
            "skipped_folders": None,  # List of skipped folders with reasons
            "selected_projects": None,
            "awaiting_project_selection": None,
            "is_subfolder_target": None,  # NEW: Track if user provided subfolder URL
            "file_structure": None,
            "languages": None,
            "dependencies": None,
            "key_files": None,
            "code_summary": None,
            "project_type": None,
            "documentation_sections": None,
            "section_instructions": None,
            "readme_sections": None,
            "mermaid_diagrams": None,
            "final_readme": None,
            "error": None,
            "retry_count": 0,
            "workflow_status": "pending",
            "current_agent": None
        }

        # Run workflow (will interrupt after each agent)
        config = {"configurable": {"thread_id": job_id}}

        # Execute workflow - it will pause at interrupt points
        async for event in workflow.graph.astream(initial_state, config):
            logger.info(f"Workflow event: {event}")

            # Update job storage with latest state
            for node_name, node_state in event.items():
                if isinstance(node_state, dict):
                    # Always update status from workflow_status
                    workflow_status = node_state.get("workflow_status", "in_progress")
                    job_storage[job_id]["status"] = workflow_status
                    job_storage[job_id]["current_agent"] = node_state.get("current_agent")

                    # Store repo_name for PR creation
                    if node_state.get("repo_name"):
                        job_storage[job_id]["repo_name"] = node_state["repo_name"]

                    # CRITICAL: Update final_readme whenever present
                    if node_state.get("final_readme"):
                        job_storage[job_id]["final_readme"] = node_state["final_readme"]
                        logger.info(f"✅ Updated job_storage[{job_id}]['final_readme'] = {len(node_state['final_readme'])} chars (workflow_status={workflow_status})")

                    if node_state.get("error"):
                        job_storage[job_id]["error"] = node_state["error"]

                    # Handle project selection
                    if node_state.get("awaiting_project_selection"):
                        job_storage[job_id]["awaiting_project_selection"] = True
                        job_storage[job_id]["detected_projects"] = node_state.get("detected_projects")
                        job_storage[job_id]["skipped_folders"] = node_state.get("skipped_folders", [])

                        # DEBUG: Log what we're storing
                        logger.info(f"DEBUG server.py: Storing skipped_folders: {job_storage[job_id]['skipped_folders']}")
                        logger.info(f"DEBUG server.py: Number of skipped folders: {len(job_storage[job_id]['skipped_folders'])}")

                        logger.info(f"Workflow paused for project selection: {job_id}")
                        return  # Stop workflow execution until user selects projects

        logger.info(f"Workflow completed for job: {job_id}")

    except Exception as e:
        logger.error(f"Workflow failed for job {job_id}: {e}", exc_info=True)
        job_storage[job_id]["status"] = "failed"
        job_storage[job_id]["error"] = str(e)


@app.get("/api/status/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    """Get current job status"""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_storage[job_id]

    # DEBUG: Log what we're returning
    skipped = job.get("skipped_folders", [])
    logger.info(f"DEBUG get_job_status: Returning skipped_folders with {len(skipped)} items")
    logger.info(f"DEBUG get_job_status: skipped_folders = {skipped}")

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress_percentage=50,  # Simplified
        current_agent=job.get("current_agent"),
        error_message=job.get("error"),
        readme_preview=job.get("final_readme", "")[:500] if job.get("final_readme") else None,
        awaiting_project_selection=job.get("awaiting_project_selection", False),
        detected_projects=job.get("detected_projects"),
        skipped_folders=job.get("skipped_folders", [])
    )


@app.get("/api/logs/{job_id}")
async def stream_logs(job_id: str):
    """
    Server-Sent Events (SSE) endpoint for streaming agent activity logs

    Client usage:
    ```javascript
    const eventSource = new EventSource(`/api/logs/${jobId}`)
    eventSource.onmessage = (event) => {
        const log = JSON.parse(event.data)
        console.log(log)
    }
    ```
    """
    log_manager = get_log_manager()

    async def event_generator():
        """Generate SSE events from log queue"""
        # Subscribe to logs for this job
        queue = await log_manager.subscribe(job_id)

        try:
            while True:
                # Wait for new log
                try:
                    log = await asyncio.wait_for(queue.get(), timeout=30.0)

                    # Convert log to JSON
                    log_data = {
                        "timestamp": log.timestamp.isoformat(),
                        "log_type": log.log_type.value,
                        "agent_name": log.agent_name,
                        "message": log.message,
                        "metadata": log.metadata
                    }

                    yield {
                        "data": json.dumps(log_data)
                    }

                except asyncio.TimeoutError:
                    # Send keep-alive ping
                    yield {
                        "data": json.dumps({"type": "keepalive"})
                    }

        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for job: {job_id}")
        finally:
            # Unsubscribe
            await log_manager.unsubscribe(job_id, queue)

    return EventSourceResponse(event_generator())


@app.post("/api/approve/{job_id}")
async def approve_agent_output(job_id: str):
    """
    Approve current agent's output and continue workflow
    Used for human-in-the-loop control
    """
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    # Resume workflow by invoking with continue command
    workflow = await get_workflow()
    config = {"configurable": {"thread_id": job_id}}

    try:
        # Continue workflow from last checkpoint
        state = workflow.graph.get_state(config)

        # Resume execution
        async for event in workflow.graph.astream(None, config):
            logger.info(f"Resumed workflow: {event}")

        return {"status": "approved", "message": "Workflow continued"}

    except Exception as e:
        logger.error(f"Failed to continue workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reject/{job_id}")
async def reject_agent_output(job_id: str, feedback: str = ""):
    """
    Reject current agent's output and provide feedback
    Agent will retry with feedback
    """
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    # Update state with feedback and retry
    workflow = await get_workflow()
    config = {"configurable": {"thread_id": job_id}}

    try:
        state = workflow.graph.get_state(config)

        # Update state with feedback
        # (Implementation depends on how you want to handle retries)

        return {"status": "rejected", "message": "Agent will retry with feedback"}

    except Exception as e:
        logger.error(f"Failed to reject and retry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/select-projects/{job_id}", response_model=ProjectSelectionResponse)
async def select_projects(job_id: str, request: ProjectSelectionRequest, background_tasks: BackgroundTasks):
    """
    Submit user's project selection and resume workflow
    """
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_storage[job_id]

    if not job.get("awaiting_project_selection"):
        raise HTTPException(status_code=400, detail="Job is not awaiting project selection")

    # Validate: 1 project can be selected
    if len(request.selected_project_paths) != 1:
        project_word = "project" if len(request.selected_project_paths) == 1 else "projects"
        raise HTTPException(
            status_code=400,
            detail=f" {len(request.selected_project_paths)} {project_word} are selected! Please select one project, as single-project documentation is supported."
        )

    try:
        # Update job storage
        job["awaiting_project_selection"] = False
        job_storage[job_id] = job

        logger.info(f"User selected {len(request.selected_project_paths)} projects for job {job_id}")

        # Resume workflow with selected projects
        background_tasks.add_task(resume_workflow, job_id, request.selected_project_paths)

        return ProjectSelectionResponse(
            status="accepted",
            message=f"Selected {len(request.selected_project_paths)} project(s). Resuming documentation generation..."
        )

    except Exception as e:
        logger.error(f"Failed to process project selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def resume_workflow(job_id: str, selected_projects: List[str]):
    """
    Resume workflow after user selects projects
    """
    try:
        workflow = await get_workflow()
        config = {"configurable": {"thread_id": job_id}}

        # Log selection
        log_manager = get_log_manager()
        await log_manager.log_async(
            job_id=job_id,
            log_type=LogType.WORKFLOW_PROGRESS,
            message=f"✅ User selected {len(selected_projects)} project(s). Continuing workflow..."
        )

        # DEBUG: Log the selected projects
        logger.info(f"DEBUG: Updating state with selected_projects = {selected_projects}")

        # Update the state directly in the graph
        await workflow.graph.aupdate_state(
            config,
            {
                "selected_projects": selected_projects,
                "awaiting_project_selection": False
            }
        )

        # Resume workflow from updated state
        async for event in workflow.graph.astream(None, config):
            logger.info(f"Resumed workflow event: {event}")

            # Update job storage
            for node_name, node_state in event.items():
                if isinstance(node_state, dict):
                    workflow_status = node_state.get("workflow_status", "in_progress")
                    job_storage[job_id]["status"] = workflow_status
                    job_storage[job_id]["current_agent"] = node_state.get("current_agent")

                    # Store repo_name for PR creation
                    if node_state.get("repo_name"):
                        job_storage[job_id]["repo_name"] = node_state["repo_name"]

                    # CRITICAL: Update final_readme whenever present
                    if node_state.get("final_readme"):
                        job_storage[job_id]["final_readme"] = node_state["final_readme"]
                        logger.info(f"✅ [RESUME] Updated job_storage[{job_id}]['final_readme'] = {len(node_state['final_readme'])} chars (workflow_status={workflow_status})")

                    if node_state.get("error"):
                        job_storage[job_id]["error"] = node_state["error"]

        logger.info(f"Workflow resumed and completed for job: {job_id}")
        logger.info(f"✅ Final job_storage[{job_id}] has final_readme: {'final_readme' in job_storage[job_id]}")

    except Exception as e:
        logger.error(f"Failed to resume workflow: {e}", exc_info=True)
        job_storage[job_id]["status"] = "failed"
        job_storage[job_id]["error"] = str(e)


@app.get("/api/download/{job_id}")
def download_readme(job_id: str):
    """Download generated README.md"""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_storage[job_id]

    if not job.get("final_readme"):
        raise HTTPException(status_code=400, detail="README not ready yet")

    from fastapi.responses import Response

    return Response(
        content=job["final_readme"],
        media_type="text/markdown",
        headers={
            "Content-Disposition": "attachment; filename=README.md"
        }
    )


@app.post("/api/create-pr/{job_id}")
async def create_pull_request(job_id: str):
    """
    Create a GitHub Pull Request using TRUE MCP Protocol
    Connects to official GitHub MCP server via stdio
    """
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_storage[job_id]

    if not job.get("final_readme"):
        raise HTTPException(status_code=400, detail="README not ready yet")

    # Check if GitHub token is configured
    github_token = settings.GITHUB_TOKEN
    if not github_token:
        raise HTTPException(
            status_code=503,
            detail="GitHub integration not configured. Please set GITHUB_TOKEN in environment variables."
        )

    try:
        # Extract repo info from URL
        repo_url = job["repo_url"]

        # Parse GitHub repo from URL
        # Expected format: https://github.com/owner/repo or https://github.com/owner/repo/tree/branch/...
        if "github.com" not in repo_url:
            raise HTTPException(status_code=400, detail="Only GitHub repositories are supported for PR creation")

        # Parse the full GitHub URL to extract owner, repo, and branch
        from services.git_service import parse_github_url
        parsed_url = parse_github_url(repo_url)

        repo_full_name = f"{parsed_url['owner']}/{parsed_url['repo']}"
        base_branch = parsed_url['branch']  # Extract branch from URL (e.g., "dev")

        # Extract project name from workflow state (already set correctly)
        # Use the actual repo_name from job storage which comes from workflow
        project_name = job.get("repo_name", parsed_url['display_name'])

        # Call MCP-based PR creation
        result = await create_pr_with_mcp(
            repo_full_name=repo_full_name,
            readme_content=job["final_readme"],
            project_name=project_name,
            base_branch=base_branch,
            github_token=github_token,
            job_id=job_id
        )

        if result["success"]:
            return {
                "status": "success",
                "message": "Pull request created successfully via MCP",
                "pr_url": result["pr_url"],
                "branch_name": result["branch_name"]
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to create PR via MCP: {result['output']}",
                "details": result["output"]
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create PR via MCP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create PR via MCP: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.API_PORT,
        log_level="info"
    )
