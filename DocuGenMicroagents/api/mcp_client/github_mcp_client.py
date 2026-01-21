"""
GitHub MCP Client - Connects to official GitHub MCP server
Uses MCP protocol (stdio) to communicate with Docker container
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class GitHubMCPClient:
    """Client for GitHub MCP Server"""

    def __init__(self, github_token: str):
        """
        Initialize GitHub MCP client

        Args:
            github_token: GitHub Personal Access Token
        """
        self.github_token = github_token
        self.session: Optional[ClientSession] = None
        self._client_context = None

    @asynccontextmanager
    async def connect(self):
        """
        Connect to GitHub MCP server running in Docker

        Yields:
            ClientSession for making tool calls
        """
        # Define server parameters - run GitHub MCP server via Docker
        server_params = StdioServerParameters(
            command="docker",
            args=[
                "run",
                "-i",
                "--rm",
                "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={self.github_token}",
                "ghcr.io/github/github-mcp-server:latest"
            ],
            env=None
        )

        logger.info("Starting GitHub MCP server via Docker...")

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session

                # Initialize session
                await session.initialize()

                # List available tools
                tools = await session.list_tools()
                logger.info(f"Connected to GitHub MCP server. Available tools: {[t.name for t in tools.tools]}")

                yield session

        logger.info("Disconnected from GitHub MCP server")
        self.session = None

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the GitHub MCP server

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server. Use 'async with client.connect():'")

        logger.debug(f"Calling MCP tool: {tool_name} with args: {arguments}")

        result = await self.session.call_tool(tool_name, arguments=arguments)

        logger.debug(f"MCP tool {tool_name} result: {result}")

        return result

    async def list_available_tools(self) -> List[str]:
        """
        Get list of available tools from GitHub MCP server

        Returns:
            List of tool names
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        tools = await self.session.list_tools()
        return [tool.name for tool in tools.tools]


# Singleton instance
_github_mcp_client: Optional[GitHubMCPClient] = None


def get_github_mcp_client(github_token: Optional[str] = None) -> GitHubMCPClient:
    """
    Get or create GitHub MCP client instance

    Args:
        github_token: GitHub PAT (uses env var if not provided)

    Returns:
        GitHubMCPClient instance
    """
    global _github_mcp_client

    if _github_mcp_client is None:
        token = github_token or os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN env var or pass token parameter.")

        _github_mcp_client = GitHubMCPClient(token)
        logger.info("GitHub MCP client created")

    return _github_mcp_client
