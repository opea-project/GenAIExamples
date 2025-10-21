#!/usr/bin/env python3
"""
Cogniware Core - Built-in LLM Definitions
Available LLMs in Cogniware's Inference Engine
"""

# Built-in LLMs available in Cogniware's inference engine
COGNIWARE_LLMS = [
    {
        "model_id": "cogniware-chat-7b",
        "model_name": "Cogniware Chat 7B",
        "model_type": "interface",
        "description": "General purpose conversational AI model optimized for natural dialogue",
        "parameters": "7B",
        "size_gb": 3.5,
        "capabilities": ["chat", "text-generation", "question-answering"],
        "status": "ready",
        "source": "cogniware",
        "version": "1.0.0",
        "max_context_length": 4096,
        "supported_tasks": [
            "Conversational AI",
            "General Q&A",
            "Creative writing",
            "Code explanation",
            "Text summarization"
        ],
        "use_cases": [
            "Customer support chatbots",
            "Virtual assistants",
            "Interactive dialogues",
            "Help desk automation"
        ]
    },
    {
        "model_id": "cogniware-chat-13b",
        "model_name": "Cogniware Chat 13B",
        "model_type": "interface",
        "description": "Advanced conversational model with enhanced reasoning capabilities",
        "parameters": "13B",
        "size_gb": 6.5,
        "capabilities": ["chat", "text-generation", "question-answering", "reasoning"],
        "status": "ready",
        "source": "cogniware",
        "version": "1.0.0",
        "max_context_length": 8192,
        "supported_tasks": [
            "Complex conversations",
            "Multi-turn dialogues",
            "Reasoning tasks",
            "Problem solving",
            "Educational tutoring"
        ],
        "use_cases": [
            "Enterprise chatbots",
            "Technical support",
            "Educational platforms",
            "Complex query handling"
        ]
    },
    {
        "model_id": "cogniware-code-7b",
        "model_name": "Cogniware Code 7B",
        "model_type": "interface",
        "description": "Specialized model for code generation and programming assistance",
        "parameters": "7B",
        "size_gb": 3.8,
        "capabilities": ["code-generation", "code-completion", "code-explanation"],
        "status": "ready",
        "source": "cogniware",
        "version": "1.0.0",
        "max_context_length": 16384,
        "supported_languages": [
            "Python", "JavaScript", "TypeScript", "Java", "C++", "C#",
            "Go", "Rust", "Ruby", "PHP", "SQL", "Shell"
        ],
        "supported_tasks": [
            "Code generation",
            "Code completion",
            "Bug fixing",
            "Code review",
            "Documentation generation"
        ],
        "use_cases": [
            "IDE integration",
            "Code review automation",
            "Developer productivity",
            "Programming education"
        ]
    },
    {
        "model_id": "cogniware-code-13b",
        "model_name": "Cogniware Code 13B",
        "model_type": "interface",
        "description": "Advanced code model with multi-language support and complex problem solving",
        "parameters": "13B",
        "size_gb": 7.0,
        "capabilities": ["code-generation", "code-completion", "code-explanation", "debugging"],
        "status": "ready",
        "source": "cogniware",
        "version": "1.0.0",
        "max_context_length": 16384,
        "supported_languages": [
            "Python", "JavaScript", "TypeScript", "Java", "C++", "C#",
            "Go", "Rust", "Ruby", "PHP", "SQL", "Shell", "Kotlin", "Swift"
        ],
        "supported_tasks": [
            "Complex code generation",
            "Architecture design",
            "Algorithm implementation",
            "Performance optimization",
            "Security analysis"
        ],
        "use_cases": [
            "Enterprise development",
            "Complex system design",
            "Code refactoring",
            "Technical interviews"
        ]
    },
    {
        "model_id": "cogniware-knowledge-7b",
        "model_name": "Cogniware Knowledge 7B",
        "model_type": "knowledge",
        "description": "Optimized for information retrieval and knowledge-based Q&A",
        "parameters": "7B",
        "size_gb": 3.2,
        "capabilities": ["question-answering", "information-retrieval", "summarization"],
        "status": "ready",
        "source": "cogniware",
        "version": "1.0.0",
        "max_context_length": 8192,
        "supported_tasks": [
            "Document Q&A",
            "Knowledge retrieval",
            "Fact extraction",
            "Research assistance",
            "Information synthesis"
        ],
        "use_cases": [
            "Knowledge bases",
            "Document search",
            "Research tools",
            "FAQ systems"
        ]
    },
    {
        "model_id": "cogniware-knowledge-13b",
        "model_name": "Cogniware Knowledge 13B",
        "model_type": "knowledge",
        "description": "Advanced knowledge model with RAG optimization and multi-document reasoning",
        "parameters": "13B",
        "size_gb": 6.2,
        "capabilities": ["question-answering", "information-retrieval", "summarization", "rag"],
        "status": "ready",
        "source": "cogniware",
        "version": "1.0.0",
        "max_context_length": 16384,
        "supported_tasks": [
            "Advanced RAG",
            "Multi-document analysis",
            "Complex queries",
            "Cross-reference lookup",
            "Contextual search"
        ],
        "use_cases": [
            "Enterprise knowledge management",
            "Legal document analysis",
            "Scientific research",
            "Compliance documentation"
        ]
    },
    {
        "model_id": "cogniware-embed-base",
        "model_name": "Cogniware Embeddings Base",
        "model_type": "embedding",
        "description": "High-quality text embeddings for semantic search and similarity",
        "parameters": "110M",
        "size_gb": 0.4,
        "capabilities": ["embedding", "semantic-search", "similarity"],
        "status": "ready",
        "source": "cogniware",
        "version": "1.0.0",
        "max_context_length": 512,
        "embedding_dimensions": 768,
        "supported_tasks": [
            "Semantic search",
            "Document similarity",
            "Clustering",
            "Recommendation systems",
            "Duplicate detection"
        ],
        "use_cases": [
            "Search engines",
            "Content recommendations",
            "Document clustering",
            "Plagiarism detection"
        ]
    },
    {
        "model_id": "cogniware-embed-large",
        "model_name": "Cogniware Embeddings Large",
        "model_type": "embedding",
        "description": "Large embedding model with enhanced semantic understanding",
        "parameters": "335M",
        "size_gb": 1.2,
        "capabilities": ["embedding", "semantic-search", "similarity", "cross-lingual"],
        "status": "ready",
        "source": "cogniware",
        "version": "1.0.0",
        "max_context_length": 512,
        "embedding_dimensions": 1024,
        "supported_tasks": [
            "Advanced semantic search",
            "Multi-lingual similarity",
            "Fine-grained clustering",
            "Complex recommendations",
            "Cross-language search"
        ],
        "use_cases": [
            "Multi-lingual search",
            "Enterprise knowledge graphs",
            "Advanced recommendation systems",
            "Cross-lingual information retrieval"
        ]
    },
    {
        "model_id": "cogniware-sql-7b",
        "model_name": "Cogniware SQL 7B",
        "model_type": "interface",
        "description": "Specialized model for SQL generation and database operations",
        "parameters": "7B",
        "size_gb": 3.5,
        "capabilities": ["sql-generation", "query-optimization", "schema-design"],
        "status": "ready",
        "source": "cogniware",
        "version": "1.0.0",
        "max_context_length": 4096,
        "supported_databases": [
            "PostgreSQL", "MySQL", "SQLite", "SQL Server",
            "Oracle", "MongoDB", "Redis"
        ],
        "supported_tasks": [
            "Natural language to SQL",
            "Query optimization",
            "Schema design",
            "Database migration",
            "Query explanation"
        ],
        "use_cases": [
            "Business intelligence",
            "Database Q&A",
            "Report generation",
            "Data analysis"
        ]
    },
    {
        "model_id": "cogniware-summarize-7b",
        "model_name": "Cogniware Summarization 7B",
        "model_type": "interface",
        "description": "Optimized for document summarization and content condensation",
        "parameters": "7B",
        "size_gb": 3.4,
        "capabilities": ["summarization", "text-condensation", "key-points-extraction"],
        "status": "ready",
        "source": "cogniware",
        "version": "1.0.0",
        "max_context_length": 16384,
        "supported_tasks": [
            "Document summarization",
            "Meeting notes",
            "Article condensation",
            "Key points extraction",
            "Executive summaries"
        ],
        "use_cases": [
            "Document management",
            "Meeting automation",
            "News aggregation",
            "Research paper summaries"
        ]
    },
    {
        "model_id": "cogniware-translate-7b",
        "model_name": "Cogniware Translation 7B",
        "model_type": "interface",
        "description": "Multi-lingual translation model with 100+ language pairs",
        "parameters": "7B",
        "size_gb": 4.5,
        "capabilities": ["translation", "language-detection", "multilingual"],
        "status": "ready",
        "source": "cogniware",
        "version": "1.0.0",
        "max_context_length": 2048,
        "supported_languages": [
            "English", "Spanish", "French", "German", "Chinese", "Japanese",
            "Korean", "Arabic", "Portuguese", "Russian", "Italian", "Dutch",
            "Polish", "Turkish", "Vietnamese", "Thai", "Hindi", "Indonesian"
        ],
        "supported_tasks": [
            "Text translation",
            "Document translation",
            "Real-time translation",
            "Language detection",
            "Multilingual chat"
        ],
        "use_cases": [
            "International business",
            "Content localization",
            "Customer support",
            "Document translation"
        ]
    },
    {
        "model_id": "cogniware-sentiment-base",
        "model_name": "Cogniware Sentiment Analysis",
        "model_type": "specialized",
        "description": "Sentiment analysis and emotion detection model",
        "parameters": "125M",
        "size_gb": 0.5,
        "capabilities": ["sentiment-analysis", "emotion-detection", "classification"],
        "status": "ready",
        "source": "cogniware",
        "version": "1.0.0",
        "max_context_length": 512,
        "supported_tasks": [
            "Sentiment classification",
            "Emotion detection",
            "Opinion mining",
            "Review analysis",
            "Social media monitoring"
        ],
        "sentiment_classes": ["positive", "negative", "neutral"],
        "emotion_classes": ["joy", "sadness", "anger", "fear", "surprise", "disgust"],
        "use_cases": [
            "Customer feedback analysis",
            "Social media monitoring",
            "Brand reputation",
            "Product reviews"
        ]
    }
]

def get_llms_by_type(model_type: str):
    """Get LLMs filtered by type"""
    return [llm for llm in COGNIWARE_LLMS if llm['model_type'] == model_type]

def get_llm_by_id(model_id: str):
    """Get specific LLM by ID"""
    for llm in COGNIWARE_LLMS:
        if llm['model_id'] == model_id:
            return llm
    return None

def get_interface_llms():
    """Get all interface LLMs (for chat and interaction)"""
    return get_llms_by_type('interface')

def get_knowledge_llms():
    """Get all knowledge LLMs (for Q&A and RAG)"""
    return get_llms_by_type('knowledge')

def get_embedding_llms():
    """Get all embedding models"""
    return get_llms_by_type('embedding')

def get_specialized_llms():
    """Get all specialized models"""
    return get_llms_by_type('specialized')

def get_all_llms():
    """Get all available LLMs"""
    return COGNIWARE_LLMS

def get_llms_summary():
    """Get summary of available LLMs"""
    return {
        "total": len(COGNIWARE_LLMS),
        "interface": len(get_interface_llms()),
        "knowledge": len(get_knowledge_llms()),
        "embedding": len(get_embedding_llms()),
        "specialized": len(get_specialized_llms()),
        "total_size_gb": sum(llm['size_gb'] for llm in COGNIWARE_LLMS),
        "total_parameters": sum(
            float(llm['parameters'].replace('B', '').replace('M', 'e-3'))
            for llm in COGNIWARE_LLMS if llm['parameters'].endswith(('B', 'M'))
        )
    }

# External model sources (for downloading/importing models)
EXTERNAL_MODEL_SOURCES = {
    "ollama": {
        "name": "Ollama",
        "description": "Open-source models from Ollama library",
        "base_url": "https://ollama.ai",
        "models": [
            {"id": "llama2", "name": "Llama 2", "size": "3.8GB"},
            {"id": "llama2:13b", "name": "Llama 2 13B", "size": "7.3GB"},
            {"id": "mistral", "name": "Mistral 7B", "size": "4.1GB"},
            {"id": "mixtral", "name": "Mixtral 8x7B", "size": "26GB"},
            {"id": "codellama", "name": "Code Llama", "size": "3.8GB"},
            {"id": "phi", "name": "Phi-2", "size": "1.7GB"},
        ]
    },
    "huggingface": {
        "name": "HuggingFace",
        "description": "Models from HuggingFace Hub",
        "base_url": "https://huggingface.co",
        "models": [
            {"id": "meta-llama/Llama-2-7b-chat-hf", "name": "Llama 2 Chat 7B", "size": "13GB"},
            {"id": "meta-llama/Llama-2-13b-chat-hf", "name": "Llama 2 Chat 13B", "size": "26GB"},
            {"id": "mistralai/Mistral-7B-Instruct-v0.1", "name": "Mistral 7B Instruct", "size": "14GB"},
            {"id": "microsoft/phi-2", "name": "Phi-2", "size": "5.5GB"},
            {"id": "google/flan-t5-xxl", "name": "FLAN-T5 XXL", "size": "11GB"},
            {"id": "bigcode/starcoder", "name": "StarCoder", "size": "15GB"},
        ]
    }
}

def get_external_sources():
    """Get external model sources for importing"""
    return EXTERNAL_MODEL_SOURCES

if __name__ == "__main__":
    # Print summary
    summary = get_llms_summary()
    print("Cogniware Built-in LLMs Summary:")
    print(f"  Total Models: {summary['total']}")
    print(f"  Interface Models: {summary['interface']}")
    print(f"  Knowledge Models: {summary['knowledge']}")
    print(f"  Embedding Models: {summary['embedding']}")
    print(f"  Specialized Models: {summary['specialized']}")
    print(f"  Total Size: {summary['total_size_gb']:.1f} GB")
    print("\nAvailable Models:")
    for llm in COGNIWARE_LLMS:
        print(f"  - {llm['model_name']} ({llm['parameters']}, {llm['size_gb']}GB) - {llm['model_type']}")

