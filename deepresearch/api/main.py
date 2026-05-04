"""
FastAPI Server - REST API for DeepResearch Agent.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from deepresearch.core.engine import ResearchEngine

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DeepResearch Agent",
    description="Autonomous multi-source research agent powered by MiMo",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instance
engine: ResearchEngine | None = None


class ResearchRequest(BaseModel):
    """Research request model."""
    topic: str
    depth: str = "medium"  # shallow, medium, deep


class ResearchResponse(BaseModel):
    """Research response model."""
    id: str
    topic: str
    status: str
    report: str | None = None
    confidence_score: float = 0.0
    citations: list[dict[str, Any]] = []
    created_at: str


@app.on_event("startup")
async def startup():
    """Initialize the research engine on startup."""
    global engine
    engine = ResearchEngine({
        "db_path": "data/research.db",
        "llm_endpoint": "https://api.mimo.xiaomi.com/v1/chat/completions",
        "model": "mimo-7b"
    })
    await engine.initialize()
    logger.info("DeepResearch Agent API started")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "DeepResearch Agent",
        "version": "0.1.0",
        "description": "Autonomous multi-source research agent",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest):
    """
    Start a new research task.
    
    This endpoint triggers the autonomous research workflow:
    1. Planning → 2. Research → 3. Analysis → 4. Writing → 5. Critique
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    try:
        task = await engine.research(request.topic)
        
        return ResearchResponse(
            id=task.id,
            topic=task.topic,
            status=task.status,
            report=task.report,
            confidence_score=task.confidence_score,
            citations=task.citations,
            created_at=task.created_at.isoformat()
        )
    except Exception as e:
        logger.error(f"Research failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def get_history(limit: int = 10):
    """Get recent research history."""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    history = await engine.get_history(limit)
    return {"history": history}


@app.get("/stats")
async def get_stats():
    """Get research statistics."""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    history = await engine.get_history(limit=100)
    
    total_research = len(history)
    completed = sum(1 for h in history if h["status"] == "completed")
    avg_confidence = (
        sum(h["confidence_score"] for h in history) / total_research
        if total_research > 0
        else 0
    )
    
    return {
        "total_research": total_research,
        "completed": completed,
        "success_rate": completed / total_research if total_research > 0 else 0,
        "average_confidence": avg_confidence
    }
