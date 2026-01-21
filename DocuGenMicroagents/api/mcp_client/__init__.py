"""
MCP Client Module
Provides connections to MCP servers (Model Context Protocol)
"""

from .github_mcp_client import GitHubMCPClient, get_github_mcp_client

__all__ = ['GitHubMCPClient', 'get_github_mcp_client']
