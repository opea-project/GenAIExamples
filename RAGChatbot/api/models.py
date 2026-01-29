"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for querying documents"""
    query: str = Field(..., min_length=1, description="Natural language question")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the main topics covered in the document?"
            }
        }


class UploadResponse(BaseModel):
    """Response model for PDF upload"""
    message: str = Field(..., description="Success message")
    num_chunks: int = Field(..., description="Number of chunks created")
    status: str = Field(..., description="Operation status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Successfully uploaded and processed 'document.pdf'",
                "num_chunks": 45,
                "status": "success"
            }
        }


class QueryResponse(BaseModel):
    """Response model for document queries"""
    answer: str = Field(..., description="Answer to the query")
    query: str = Field(..., description="Original query")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The main topics covered in the document are...",
                "query": "What are the main topics covered in the document?"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Health status")
    vectorstore_available: bool = Field(..., description="Whether vectorstore is loaded")
    openai_key_configured: bool = Field(..., description="Whether inference API token is configured")


class DeleteResponse(BaseModel):
    """Response model for delete operations"""
    message: str = Field(..., description="Result message")
    status: str = Field(..., description="Operation status")

