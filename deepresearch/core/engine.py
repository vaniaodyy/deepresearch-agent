"""
Core Research Engine - The autonomous loop that coordinates all agents.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ResearchTask(BaseModel):
    """A research task to be executed."""
    id: str
    topic: str
    created_at: datetime = datetime.now()
    status: str = "pending"
    plan: dict[str, Any] | None = None
    sources: list[dict[str, Any]] = []
    analysis: dict[str, Any] | None = None
    report: str | None = None
    confidence_score: float = 0.0
    citations: list[dict[str, Any]] = []


class ResearchEngine:
    """
    The autonomous research engine.
    
    Coordinates the multi-agent workflow:
    1. Planner → Creates research strategy
    2. Researcher → Executes searches and extracts data
    3. Analyst → Cross-references and analyzes findings
    4. Writer → Generates comprehensive report
    5. Critic → Reviews and suggests improvements
    """
    
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.agents = {}
        self.db_path = Path(self.config.get("db_path", "data/research.db"))
        self._initialized = False
    
    async def initialize(self):
        """Initialize all agents and database."""
        if self._initialized:
            return
        
        # Import agents lazily to avoid circular imports
        from deepresearch.agents.planner.planner import PlannerAgent
        from deepresearch.agents.researcher.researcher import ResearcherAgent
        from deepresearch.agents.analyst.analyst import AnalystAgent
        from deepresearch.agents.writer.writer import WriterAgent
        from deepresearch.agents.critic.critic import CriticAgent
        
        self.agents = {
            "planner": PlannerAgent(self.config),
            "researcher": ResearcherAgent(self.config),
            "analyst": AnalystAgent(self.config),
            "writer": WriterAgent(self.config),
            "critic": CriticAgent(self.config),
        }
        
        # Initialize database
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        logger.info("Research engine initialized")
    
    async def research(self, topic: str) -> ResearchTask:
        """
        Execute a full autonomous research cycle.
        
        Args:
            topic: The research topic or question
            
        Returns:
            ResearchTask with all results
        """
        await self.initialize()
        
        task = ResearchTask(
            id=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            topic=topic,
        )
        
        try:
            # Phase 1: Planning
            logger.info(f"Phase 1: Planning research for '{topic}'")
            task.plan = await self.agents["planner"].create_plan(topic)
            task.status = "planning_complete"
            
            # Phase 2: Research
            logger.info("Phase 2: Executing research")
            task.sources = await self.agents["researcher"].execute_plan(task.plan)
            task.status = "research_complete"
            
            # Phase 3: Analysis
            logger.info("Phase 3: Analyzing findings")
            task.analysis = await self.agents["analyst"].analyze(
                topic=topic,
                plan=task.plan,
                sources=task.sources
            )
            task.status = "analysis_complete"
            
            # Phase 4: Writing
            logger.info("Phase 4: Generating report")
            task.report = await self.agents["writer"].generate_report(
                topic=topic,
                plan=task.plan,
                analysis=task.analysis,
                sources=task.sources
            )
            task.status = "writing_complete"
            
            # Phase 5: Critique
            logger.info("Phase 5: Reviewing report")
            critique = await self.agents["critic"].review(
                report=task.report,
                topic=topic,
                sources=task.sources
            )
            
            # Apply critical feedback if needed
            if critique.get("needs_revision", False):
                logger.info("Revision needed, regenerating report...")
                task.report = await self.agents["writer"].revise_report(
                    original_report=task.report,
                    critique=critique,
                    topic=topic
                )
            
            task.confidence_score = critique.get("confidence_score", 0.0)
            task.citations = task.analysis.get("citations", [])
            task.status = "completed"
            
            # Save to database
            await self._save_task(task)
            
            logger.info(f"Research completed: {task.id} (confidence: {task.confidence_score:.1%})")
            
        except Exception as e:
            task.status = "failed"
            logger.error(f"Research failed: {e}")
            raise
        
        return task
    
    async def _save_task(self, task: ResearchTask):
        """Save research task to database."""
        import aiosqlite
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS research_tasks (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    plan JSON,
                    sources JSON,
                    analysis JSON,
                    report TEXT,
                    confidence_score REAL DEFAULT 0.0,
                    citations JSON
                )
            """)
            
            await db.execute("""
                INSERT OR REPLACE INTO research_tasks 
                (id, topic, created_at, status, plan, sources, analysis, report, confidence_score, citations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.topic,
                task.created_at.isoformat(),
                task.status,
                json.dumps(task.plan),
                json.dumps(task.sources),
                json.dumps(task.analysis),
                task.report,
                task.confidence_score,
                json.dumps(task.citations)
            ))
            
            await db.commit()
    
    async def get_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent research history."""
        import aiosqlite
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM research_tasks ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            rows = await cursor.fetchall()
            
            return [
                {
                    "id": row[0],
                    "topic": row[1],
                    "created_at": row[2],
                    "status": row[3],
                    "confidence_score": row[8],
                }
                for row in rows
            ]
