# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
OPEA Inventory Management System - Complete Backend API
Full integration with all OPEA GenAIComps microservices
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from app.services.csv_processor import csv_processor
from app.services.dbqna_service import dbqna_service
from app.services.doc_summarization import doc_summarization

# Import all OPEA services
from app.services.embedding_service import embedding_service
from app.services.file_upload_service import file_upload_service
from app.services.graph_generator import graph_generator
from app.services.interactive_agent import interactive_agent
from app.services.knowledge_manager import knowledge_manager
from app.services.llm_service import llm_service
from app.services.retrieval_service import retrieval_service
from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OPEA IMS API - Full Integration",
    description="Complete AI-powered Inventory Management System using OPEA microservices",
    version="2.0.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================
# REQUEST/RESPONSE MODELS
# ====================


class UserLogin(BaseModel):
    email: str
    password: str


class User(BaseModel):
    email: str
    role: str
    name: str


class InventoryQuery(BaseModel):
    query: str
    warehouse: Optional[str] = None
    use_rag: bool = True
    use_dbqna: bool = True


class ChatMessage(BaseModel):
    message: str
    session_id: str
    user_role: str = "Inventory Manager"


class KnowledgeAdd(BaseModel):
    text: str
    source: str
    metadata: Optional[Dict[str, Any]] = None


class DocumentSummarize(BaseModel):
    text: str
    summary_type: str = "concise"
    max_length: int = 200


class AgentCreate(BaseModel):
    description: str
    components: List[str]


class SQLQuery(BaseModel):
    natural_language: str


# Mock user database
USERS = {
    "consumer@company.com": {
        "password": "password123",
        "role": "Consumer",
        "name": "Consumer User",
    },
    "inventory@company.com": {
        "password": "password123",
        "role": "Inventory Manager",
        "name": "Inventory Manager",
    },
    "admin@company.com": {
        "password": "password123",
        "role": "Super Admin",
        "name": "System Administrator",
    },
}

# ====================
# HEALTH & STATUS
# ====================


@app.get("/")
async def root():
    return {
        "service": "OPEA Inventory Management System - Full Integration",
        "version": "2.0.0",
        "status": "active",
        "opea_integration": "enabled",
        "capabilities": [
            "Embeddings",
            "Retrieval",
            "LLM",
            "DBQnA",
            "DocSummarization",
            "Interactive Agent",
            "Graph Generation",
            "Continuous Learning",
        ],
    }


@app.get("/api/health")
async def health_check():
    """Comprehensive health check including all OPEA services."""

    embedding_health = await embedding_service.health_check()
    retrieval_health = await retrieval_service.health_check()
    llm_health = await llm_service.health_check()
    db_health = await dbqna_service.health_check()

    return {
        "status": ("healthy" if all([embedding_health, llm_health, db_health]) else "degraded"),
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "up",
            "embedding_service": "up" if embedding_health else "down",
            "retrieval_service": retrieval_health,
            "llm_service": "up" if llm_health else "down",
            "database": "up" if db_health else "down",
        },
    }


# ====================
# AUTHENTICATION
# ====================


@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    user_data = USERS.get(credentials.email)

    if not user_data or user_data["password"] != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "success": True,
        "user": {
            "email": credentials.email,
            "role": user_data["role"],
            "name": user_data["name"],
        },
        "token": "opea_token_" + credentials.email,
    }


@app.post("/api/auth/logout")
async def logout():
    return {"success": True, "message": "Logged out successfully"}


# ====================
# INTERACTIVE AGENT & CHAT
# ====================


@app.post("/api/chat")
async def chat(msg: ChatMessage):
    """Interactive chat with AI agent Uses RAG + DBQnA for intelligent responses."""
    response = await interactive_agent.chat(
        message=msg.message,
        session_id=msg.session_id,
        user_role=msg.user_role,
        use_rag=True,
        use_dbqna=True,
    )

    return response


@app.get("/api/chat/sessions")
async def get_active_sessions():
    """Get list of active chat sessions."""
    sessions = interactive_agent.get_active_sessions()
    return {"sessions": sessions, "count": len(sessions)}


@app.delete("/api/chat/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a chat session."""
    interactive_agent.clear_session(session_id)
    return {"success": True, "message": f"Session {session_id} cleared"}


# ====================
# INVENTORY QUERIES (DBQnA)
# ====================


@app.post("/api/inventory/query")
async def query_inventory(query: InventoryQuery):
    """Query inventory using natural language Powered by OPEA DBQnA agent."""
    result = await dbqna_service.query_inventory(query.query)
    return result


@app.post("/api/inventory/nl-to-sql")
async def natural_language_to_sql(query: SQLQuery):
    """Convert natural language to SQL query."""
    schema = await dbqna_service.get_schema()
    sql = await llm_service.generate_sql_query(query.natural_language, schema)

    return {
        "natural_language": query.natural_language,
        "sql_query": sql,
        "schema_used": schema,
    }


@app.get("/api/inventory/stock")
async def get_stock():
    """Get stock levels."""
    # This would query actual database
    return {
        "success": True,
        "data": [
            {
                "product": "Intel Xeon 6",
                "sku": "CPU-XN6-2024",
                "stock": 247,
                "status": "In Stock",
                "trend": "+12%",
            },
            {
                "product": "AMD EPYC 9004",
                "sku": "CPU-EP9-2024",
                "stock": 189,
                "status": "In Stock",
                "trend": "+8%",
            },
            {
                "product": "NVIDIA H100",
                "sku": "GPU-H100-2024",
                "stock": 45,
                "status": "Low Stock",
                "trend": "-15%",
            },
            {
                "product": "Samsung DDR5 64GB",
                "sku": "RAM-DD5-64",
                "stock": 523,
                "status": "In Stock",
                "trend": "+23%",
            },
        ],
    }


# ====================
# KNOWLEDGE BASE MANAGEMENT
# ====================


@app.post("/api/knowledge/add")
async def add_knowledge(knowledge: KnowledgeAdd):
    """Add new knowledge to the system Supports continuous learning."""
    result = await knowledge_manager.add_knowledge_from_text(
        text=knowledge.text,
        source=knowledge.source,
        metadata=knowledge.metadata,
        auto_train=True,
    )

    return result


@app.post("/api/knowledge/upload-csv")
async def upload_csv_knowledge(file: UploadFile = File(...)):
    """Upload CSV file to add to knowledge base Automatically processes and embeds data."""
    try:
        # Read file content
        content = await file.read()

        # Process using file upload service
        result = await file_upload_service.upload_and_process(filename=file.filename, content=content)

        return result

    except Exception as e:
        logger.error(f"CSV upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge/upload-file")
async def upload_knowledge_file(file: UploadFile = File(...)):
    """Upload file (CSV, XLSX, PDF, DOCX) to knowledge base Supports multiple file formats with automatic processing
    Optimized for Intel Xeon processors."""
    try:
        # Read file content
        content = await file.read()

        # Process using file upload service
        result = await file_upload_service.upload_and_process(filename=file.filename, content=content)

        return result

    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge/uploaded-files")
async def get_uploaded_files(file_type: Optional[str] = None):
    """Get list of uploaded files."""
    files = file_upload_service.list_uploaded_files(file_type=file_type)
    return {"success": True, "files": files, "count": len(files)}


@app.get("/api/knowledge/stats")
async def get_knowledge_stats():
    """Get knowledge base statistics."""
    stats = await knowledge_manager.get_knowledge_stats()
    return stats


@app.post("/api/knowledge/retrain")
async def retrain_knowledge_base():
    """Retrain entire knowledge base with latest embeddings Useful after adding bulk data."""
    result = await knowledge_manager.retrain_all()
    return result


@app.get("/api/knowledge/search")
async def search_knowledge(q: str, top_k: int = 5):
    """Search knowledge base."""
    results = await knowledge_manager.search_knowledge(query=q, top_k=top_k)
    return {"query": q, "results": results}


# ====================
# DOCUMENT SUMMARIZATION
# ====================


@app.post("/api/documents/summarize")
async def summarize_document(doc: DocumentSummarize):
    """Summarize a document using OPEA DocSummarization."""
    summary = await doc_summarization.summarize_document(
        text=doc.text, summary_type=doc.summary_type, max_length=doc.max_length
    )
    return summary


@app.post("/api/documents/extract-info")
async def extract_information(text: str):
    """Extract structured information from text."""
    result = await llm_service.extract_entities(text)
    return {"extracted_entities": result}


@app.get("/api/documents/summarize-csv/{filename}")
async def summarize_csv_file(filename: str):
    """Summarize a CSV file."""
    csv_path = f"../data/{filename}"
    summary = await doc_summarization.summarize_csv_data(csv_path)
    return summary


# ====================
# GRAPH & VISUALIZATION DATA
# ====================


@app.get("/api/graphs/stock-trend/{sku}")
async def get_stock_trend(sku: str, days: int = 30):
    """Get stock trend data for charts."""
    data = await graph_generator.generate_stock_trend(sku, days)
    return data


@app.get("/api/graphs/category-distribution")
async def get_category_distribution():
    """Get category distribution for pie chart."""
    data = await graph_generator.generate_category_distribution()
    return data


@app.get("/api/graphs/warehouse-comparison")
async def get_warehouse_comparison():
    """Get warehouse comparison data."""
    data = await graph_generator.generate_warehouse_comparison()
    return data


@app.get("/api/graphs/allocation-timeline")
async def get_allocation_timeline(days: int = 14):
    """Get allocation timeline."""
    data = await graph_generator.generate_allocation_timeline(days)
    return data


@app.get("/api/graphs/performance-metrics")
async def get_performance_metrics():
    """Get KPI metrics."""
    data = await graph_generator.generate_performance_metrics()
    return data


@app.get("/api/graphs/forecast/{sku}")
async def get_forecast(sku: str, days: int = 30):
    """Get demand forecast."""
    data = await graph_generator.generate_forecast(sku, days)
    return data


# ====================
# AI AGENT MANAGEMENT
# ====================


@app.post("/api/agents/create")
async def create_agent(agent: AgentCreate):
    """Create new AI agent configuration."""
    return {
        "success": True,
        "agent_id": "agent_" + datetime.now().strftime("%Y%m%d%H%M%S"),
        "description": agent.description,
        "components": agent.components,
        "status": "created",
    }


@app.post("/api/agents/deploy/{agent_id}")
async def deploy_agent(agent_id: str):
    """Deploy an AI agent."""
    return {
        "success": True,
        "agent_id": agent_id,
        "deployment_url": f"https://inventory-agent-{agent_id}.azurewebsites.net",
        "status": "deploying",
    }


# ====================
# DASHBOARD & ANALYTICS
# ====================


@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Comprehensive dashboard statistics."""
    return {
        "success": True,
        "data": {
            "total_items": 2847,
            "warehouses": 3,
            "allocations": 156,
            "inventory_value": 2400000,
            "stock_by_category": [
                {"category": "Processors", "count": 436, "percentage": 78},
                {"category": "GPUs", "count": 45, "percentage": 25},
                {"category": "Memory", "count": 523, "percentage": 92},
                {"category": "Storage", "count": 312, "percentage": 65},
            ],
            "recent_activity": [
                {
                    "type": "stock_update",
                    "product": "Intel Xeon 6",
                    "details": "San Jose • +50 units",
                    "time": "2 mins ago",
                },
                {
                    "type": "allocation",
                    "product": "NVIDIA H100",
                    "details": "Cloud Dynamics • 35 units",
                    "time": "15 mins ago",
                },
                {
                    "type": "alert",
                    "product": "Warehouse",
                    "details": "Portland at 82%",
                    "time": "1 hour ago",
                },
            ],
        },
    }


@app.get("/api/inventory/warehouses")
async def get_warehouses():
    """Get warehouse information."""
    return {
        "success": True,
        "data": [
            {
                "name": "San Jose",
                "capacity": "15,000 sq ft",
                "utilization": "78%",
                "items": 2847,
                "temp": "68°F",
            },
            {
                "name": "Austin",
                "capacity": "12,000 sq ft",
                "utilization": "65%",
                "items": 1923,
                "temp": "70°F",
            },
            {
                "name": "Portland",
                "capacity": "18,000 sq ft",
                "utilization": "82%",
                "items": 3456,
                "temp": "66°F",
            },
        ],
    }


@app.get("/api/inventory/allocations")
async def get_allocations():
    """Get allocation records."""
    return {
        "success": True,
        "data": [
            {
                "id": "AL-2024-001",
                "product": "Intel Xeon 6",
                "customer": "Tech Corp",
                "qty": 50,
                "status": "Pending",
                "date": "2024-10-10",
            },
            {
                "id": "AL-2024-002",
                "product": "NVIDIA H100",
                "customer": "AI Solutions",
                "qty": 20,
                "status": "Confirmed",
                "date": "2024-10-09",
            },
            {
                "id": "AL-2024-003",
                "product": "AMD EPYC 9004",
                "customer": "Cloud Dynamics",
                "qty": 35,
                "status": "Shipped",
                "date": "2024-10-08",
            },
        ],
    }


# ====================
# WEBSOCKET FOR REAL-TIME UPDATES
# ====================


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


@app.websocket("/ws/inventory")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time inventory updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Process websocket messages
            await websocket.send_json({"status": "received", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ====================
# STARTUP & INITIALIZATION
# ====================


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("🚀 Starting OPEA IMS Platform...")

    # Check OPEA services
    logger.info("Checking OPEA microservices...")
    embedding_ok = await embedding_service.health_check()
    llm_ok = await llm_service.health_check()

    logger.info(f"  Embedding Service: {'✅' if embedding_ok else '❌'}")
    logger.info(f"  LLM Service: {'✅' if llm_ok else '❌'}")

    # Load knowledge base stats
    stats = await knowledge_manager.get_knowledge_stats()
    logger.info(f"  Knowledge Base: {stats.get('total_documents', 0)} documents indexed")

    logger.info("✅ OPEA IMS Platform started successfully!")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
