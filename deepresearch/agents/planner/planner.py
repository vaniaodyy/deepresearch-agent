"""
Planner Agent - Creates research strategy and breaks down topics into sub-queries.
"""

import json
import logging
from typing import Any

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ResearchPlan(BaseModel):
    """Research plan structure."""
    topic: str
    sub_queries: list[str]
    sources_to_check: list[str]
    estimated_time: str
    research_depth: str


class PlannerAgent:
    """
    Autonomous planning agent that decides research strategy.
    
    Features:
    - Breaks down complex topics into sub-queries
    - Identifies best sources for each sub-query
    - Self-corrects if initial approach fails
    - Adapts strategy based on available data
    """
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.llm_endpoint = config.get("llm_endpoint", "https://api.mimo.xiaomi.com/v1/chat/completions")
        self.llm_key = config.get("llm_key", "")
        self.model = config.get("model", "mimo-7b")
    
    async def create_plan(self, topic: str) -> dict[str, Any]:
        """
        Create an autonomous research plan for a given topic.
        
        Args:
            topic: The research topic or question
            
        Returns:
            Research plan with sub-queries and source recommendations
        """
        logger.info(f"Creating research plan for: {topic}")
        
        # Generate research plan using LLM
        prompt = f"""You are a research strategist. Create a comprehensive research plan for:

TOPIC: {topic}

Generate a JSON response with:
1. sub_queries: 5-10 specific search queries to investigate this topic
2. sources_to_check: Best sources for this topic (web, arxiv, reddit, github, news)
3. research_depth: "shallow", "medium", or "deep"
4. estimated_time: Estimated research time

Consider:
- Multiple perspectives on the topic
- Recent data and trends
- Academic and industry sources
- Cross-referencing needs

Return ONLY valid JSON."""

        try:
            response = await self._call_llm(prompt)
            plan = json.loads(response)
            
            # Validate and enhance plan
            plan = self._validate_plan(plan, topic)
            
            logger.info(f"Plan created: {len(plan['sub_queries'])} sub-queries")
            return plan
            
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            # Fallback to basic plan
            return self._fallback_plan(topic)
    
    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.llm_endpoint,
                headers={
                    "Authorization": f"Bearer {self.llm_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a research planning assistant. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                raise Exception(f"LLM API error: {response.status_code}")
    
    def _validate_plan(self, plan: dict[str, Any], topic: str) -> dict[str, Any]:
        """Validate and enhance the research plan."""
        # Ensure required fields exist
        plan.setdefault("topic", topic)
        plan.setdefault("sub_queries", [topic])
        plan.setdefault("sources_to_check", ["web", "arxiv"])
        plan.setdefault("research_depth", "medium")
        plan.setdefault("estimated_time", "15 minutes")
        
        # Ensure we have at least 3 sub-queries
        if len(plan["sub_queries"]) < 3:
            plan["sub_queries"] = [
                topic,
                f"{topic} overview",
                f"{topic} recent developments",
                f"{topic} analysis",
                f"{topic} future trends"
            ]
        
        return plan
    
    def _fallback_plan(self, topic: str) -> dict[str, Any]:
        """Create a basic fallback plan."""
        return {
            "topic": topic,
            "sub_queries": [
                topic,
                f"{topic} overview",
                f"{topic} recent news",
                f"{topic} analysis",
                f"{topic} expert opinions"
            ],
            "sources_to_check": ["web", "news", "reddit"],
            "research_depth": "medium",
            "estimated_time": "10 minutes"
        }
