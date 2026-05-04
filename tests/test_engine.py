"""
Tests for the Research Engine.
"""

import asyncio
import pytest
from deepresearch.core.engine import ResearchEngine, ResearchTask


@pytest.fixture
def engine():
    """Create a test engine."""
    return ResearchEngine({"db_path": ":memory:"})


def test_research_task_creation():
    """Test creating a research task."""
    task = ResearchTask(
        id="test_001",
        topic="Test topic"
    )
    
    assert task.id == "test_001"
    assert task.topic == "Test topic"
    assert task.status == "pending"
    assert task.confidence_score == 0.0


def test_engine_initialization(engine):
    """Test engine initialization."""
    assert engine is not None
    assert engine.config is not None


@pytest.mark.asyncio
async def test_engine_initialize(engine):
    """Test engine async initialization."""
    await engine.initialize()
    assert engine._initialized is True
    assert "planner" in engine.agents
    assert "researcher" in engine.agents
    assert "analyst" in engine.agents
    assert "writer" in engine.agents
    assert "critic" in engine.agents
