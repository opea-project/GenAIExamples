"""
Multi-Agent Q&A System
Simplified agent implementation without CrewAI dependency
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from services.api_client import get_api_client
from services.rag_service import get_rag_service

logger = logging.getLogger(__name__)

# Activity logs for agent interactions
activity_logs = []


def add_activity_log(message: str, log_type: str = "info"):
    """Add an activity log entry"""
    from datetime import datetime
    activity_logs.append({
        "timestamp": datetime.now().isoformat(),
        "type": log_type,
        "message": message
    })
    # Keep only last 500 logs
    if len(activity_logs) > 500:
        activity_logs.pop(0)

# Default configurations
DEFAULT_ORCHESTRATION_CONFIG = {
    "role": "Orchestration Coordinator",
    "goal": "Analyze user queries and delegate them to the most appropriate specialized agent",
    "backstory": "You are an expert coordinator who understands different types of questions. You excel at categorizing queries and routing them to the right specialist: code questions to developers, document questions to researchers, and general questions to assistants.",
    "max_tokens": 500,
    "temperature": 0.7
}

DEFAULT_CODE_CONFIG = {
    "role": "Senior Software Developer",
    "goal": "Answer coding questions with accurate, practical, and well-explained solutions",
    "backstory": "You are an experienced software engineer with expertise in multiple programming languages. You provide clear, working code examples and best practices.",
    "max_tokens": 500,
    "temperature": 0.5
}

DEFAULT_RAG_CONFIG = {
    "role": "Research Assistant",
    "goal": "Retrieve information from documents and provide accurate answers",
    "backstory": "You are a skilled researcher who excels at finding relevant information from knowledge bases and synthesizing comprehensive answers.",
    "max_tokens": 800,
    "temperature": 0.7
}

DEFAULT_NORMAL_CONFIG = {
    "role": "Helpful Assistant",
    "goal": "Provide clear, accurate, and helpful answers to general questions",
    "backstory": "You are a knowledgeable assistant who loves helping people with their questions. You provide thoughtful and informative responses.",
    "max_tokens": 500,
    "temperature": 0.7
}


def get_orchestration_agent(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get orchestration agent configuration"""
    return config if config else DEFAULT_ORCHESTRATION_CONFIG


def get_code_agent(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get code agent configuration"""
    return config if config else DEFAULT_CODE_CONFIG


def get_rag_agent(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get RAG agent configuration"""
    return config if config else DEFAULT_RAG_CONFIG


def get_normal_agent(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get normal agent configuration"""
    return config if config else DEFAULT_NORMAL_CONFIG


def determine_agent_type(query: str, verbose: bool = True) -> tuple[str, str]:
    """
    Determine which agent should handle the query
    
    Args:
        query: User query
        verbose: Whether to log the decision
        
    Returns:
        Tuple of (agent_type, reasoning)
    """
    query_lower = query.lower()
    
    # Check for code-related keywords
    code_keywords = ['code', 'programming', 'function', 'variable', 'debug', 'error', 
                     'python', 'javascript', 'java', 'c++', 'git', 'repo', 'repository',
                     'algorithm', 'data structure', 'api', 'syntax', 'compile', 'test']
    if any(keyword in query_lower for keyword in code_keywords):
        matched_keywords = [kw for kw in code_keywords if kw in query_lower]
        reasoning = f"Code keywords detected: {', '.join(matched_keywords[:3])}"
        if verbose:
            logger.info(f"🔍 ORCHESTRATION: {reasoning} → Routing to Code Agent")
            add_activity_log(f"🔍 {reasoning} → Routing to Code Agent", "info")
        return 'code', reasoning
    
    # Check for document/retrieval-related keywords
    rag_keywords = ['document', 'file', 'pdf', 'retrieve', 'search', 'find in',
                   'according to', 'read', 'extract', 'index']
    if any(keyword in query_lower for keyword in rag_keywords):
        matched_keywords = [kw for kw in rag_keywords if kw in query_lower]
        reasoning = f"RAG keywords detected: {', '.join(matched_keywords[:3])}"
        if verbose:
            logger.info(f"🔍 ORCHESTRATION: {reasoning} → Routing to RAG Agent")
            add_activity_log(f"🔍 {reasoning} → Routing to RAG Agent", "info")
        return 'rag', reasoning
    
    # Default to normal agent
    reasoning = "No specialized keywords found, using general agent"
    if verbose:
        logger.info(f"🔍 ORCHESTRATION: {reasoning} → Routing to General Agent")
        add_activity_log(f"🔍 {reasoning} → Routing to General Agent", "info")
    return 'normal', reasoning


def process_query(query: str, agent_config: Optional[Dict[str, Any]] = None, verbose: bool = True) -> tuple[str, str]:
    """
    Process a query using the appropriate agent with full logging
    
    Args:
        query: User query
        agent_config: Optional agent configuration
        verbose: Whether to log agent interactions
        
    Returns:
        Tuple of (response, agent_name)
    """
    # Step 1: Orchestration - Determine which agent to use
    if verbose:
        logger.info("=" * 80)
        logger.info("🎯 ORCHESTRATION: Analyzing user query")
        logger.info(f"📝 Query: {query}")
        logger.info("=" * 80)
        add_activity_log("🎯 ORCHESTRATION: Analyzing user query", "info")
        add_activity_log(f"📝 Query: {query}", "info")
    
    agent_type, reasoning = determine_agent_type(query, verbose=verbose)
    
    try:
        # Get agent configurations if provided
        code_config = None
        rag_config = None
        normal_config = None
        
        if agent_config:
            code_config = agent_config.get("code")
            rag_config = agent_config.get("rag")
            normal_config = agent_config.get("normal")
        
        # Get the appropriate agent config
        if agent_type == 'code':
            agent_config_data = get_code_agent(code_config)
            agent_name = 'code_agent'
        elif agent_type == 'rag':
            agent_config_data = get_rag_agent(rag_config)
            agent_name = 'rag_agent'
        else:
            agent_config_data = get_normal_agent(normal_config)
            agent_name = 'normal_agent'
        
        # Step 2: Agent configuration
        if verbose:
            logger.info("")
            logger.info(f"🤖 AGENT SELECTED: {agent_name}")
            logger.info(f"   Role: {agent_config_data.get('role', 'Assistant')}")
            logger.info(f"   Goal: {agent_config_data.get('goal', 'Help the user')}")
            logger.info("")
            add_activity_log(f"🤖 AGENT SELECTED: {agent_name}", "info")
            add_activity_log(f"   Role: {agent_config_data.get('role', 'Assistant')}", "info")
        
        # Build the prompt with agent context
        role = agent_config_data.get("role", "Assistant")
        goal = agent_config_data.get("goal", "Help the user")
        backstory = agent_config_data.get("backstory", "You are a helpful assistant")
        
        # Step 3: Agent processing
        if verbose:
            logger.info("💭 AGENT THINKING: Processing query with agent-specific context...")
            add_activity_log("💭 AGENT THINKING: Processing query with agent-specific context...", "info")
        
        api_client = get_api_client()
        
        # Handle RAG agent differently - search documents first
        if agent_type == 'rag':
            try:
                rag_service = get_rag_service()
                if verbose:
                    add_activity_log("🔍 RAG: Searching document index...", "info")
                
                # Search for relevant documents
                results = rag_service.search(query, k=3)
                
                if results:
                    # Build context from retrieved documents
                    context_parts = []
                    for i, result in enumerate(results, 1):
                        doc_text = result['document']['text']
                        similarity = result['similarity']
                        context_parts.append(f"Document {i} (similarity: {similarity:.2f}):\n{doc_text}")
                    
                    context = "\n\n".join(context_parts)
                    
                    if verbose:
                        add_activity_log(f"📄 RAG: Found {len(results)} relevant documents", "info")
                        logger.info(f"RAG retrieval: Found {len(results)} relevant documents")
                    
                    system_prompt = f"""You are a {role}.

Your goal: {goal}

{backstory}

Use the following retrieved documents to answer the question. If the documents don't contain relevant information, say so.

Retrieved Documents:
{context}

Now answer the following question based on the documents above:"""
                else:
                    if verbose:
                        add_activity_log("⚠️ RAG: No documents found in index", "warning")
                    
                    system_prompt = f"""You are a {role}.

Your goal: {goal}

{backstory}

Note: No documents are currently indexed. You cannot answer questions about documents until documents are uploaded.

Now answer the following question:"""
            except Exception as e:
                logger.error(f"Error in RAG retrieval: {str(e)}")
                if verbose:
                    add_activity_log(f"❌ RAG Error: {str(e)}", "error")
                
                # Fall back to normal prompt
                system_prompt = f"""You are a {role}.

Your goal: {goal}

{backstory}

Now answer the following question:"""
        else:
            # For non-RAG agents, use standard prompt
            system_prompt = f"""You are a {role}.

Your goal: {goal}

{backstory}

Now answer the following question:"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        response = api_client.chat_complete(
            messages=messages,
            max_tokens=agent_config_data.get("max_tokens", 500),
            temperature=agent_config_data.get("temperature", 0.7)
        )
        
        if verbose:
            logger.info(f"✅ AGENT RESPONSE: Generated {len(str(response))} characters")
            logger.info("=" * 80)
            logger.info("")
            add_activity_log(f"✅ AGENT RESPONSE: Generated {len(str(response))} characters", "success")
        
        return str(response), agent_name
        
    except Exception as e:
        error_msg = f"❌ ERROR: {str(e)}"
        logger.error(error_msg, exc_info=True)
        add_activity_log(error_msg, "error")
        raise


def update_agent_configs(configs: Dict[str, Any]) -> None:
    """
    Update all agent configurations (stored as defaults for future queries)
    
    Args:
        configs: Dictionary containing agent configurations
    """
    # In this simplified version, configs are used at query time
    # This function exists for API compatibility
    logger.info("Agent configurations updated")

