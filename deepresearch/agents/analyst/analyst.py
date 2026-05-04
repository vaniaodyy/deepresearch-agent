"""
Analyst Agent - Cross-references and analyzes findings from multiple sources.
"""

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class AnalystAgent:
    """
    Autonomous analysis agent that processes research findings.
    
    Features:
    - Cross-references multiple sources
    - Identifies patterns and contradictions
    - Calculates confidence scores
    - Extracts key insights and data points
    """
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.llm_endpoint = config.get("llm_endpoint", "https://api.mimo.xiaomi.com/v1/chat/completions")
        self.llm_key = config.get("llm_key", "")
        self.model = config.get("model", "mimo-7b")
    
    async def analyze(
        self,
        topic: str,
        plan: dict[str, Any],
        sources: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Analyze research findings and extract insights.
        
        Args:
            topic: The original research topic
            plan: The research plan
            sources: List of sources found
            
        Returns:
            Analysis with insights, patterns, and confidence scores
        """
        logger.info(f"Analyzing {len(sources)} sources for: {topic}")
        
        # Prepare source summaries for LLM
        source_summaries = self._prepare_source_summaries(sources)
        
        prompt = f"""You are a research analyst. Analyze the following sources about:

TOPIC: {topic}

SOURCES:
{source_summaries}

Provide a comprehensive analysis in JSON format:
1. key_findings: List of main discoveries (with source citations)
2. patterns: Identified patterns across sources
3. contradictions: Any conflicting information
4. confidence_score: Overall confidence (0.0-1.0)
5. citations: List of sources used (url, title, relevance)
6. data_points: Specific numbers, statistics, facts mentioned
7. expert_opinions: Notable expert views found
8. gaps: Information gaps that couldn't be filled

Return ONLY valid JSON."""

        try:
            response = await self._call_llm(prompt)
            analysis = json.loads(response)
            
            # Validate analysis
            analysis = self._validate_analysis(analysis, sources)
            
            logger.info(f"Analysis complete: {analysis['confidence_score']:.1%} confidence")
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._fallback_analysis(topic, sources)
    
    def _prepare_source_summaries(self, sources: list[dict[str, Any]]) -> str:
        """Prepare source summaries for LLM analysis."""
        summaries = []
        
        for i, source in enumerate(sources[:10], 1):  # Limit to top 10 sources
            summary = f"""
Source {i}:
- Title: {source.get('title', 'Unknown')}
- Type: {source.get('source_type', 'web')}
- URL: {source.get('url', 'N/A')}
- Snippet: {source.get('snippet', 'N/A')[:300]}
"""
            summaries.append(summary)
        
        return "\n".join(summaries)
    
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
                        {"role": "system", "content": "You are a research analyst. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 2000
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                raise Exception(f"LLM API error: {response.status_code}")
    
    def _validate_analysis(self, analysis: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
        """Validate and enhance analysis."""
        analysis.setdefault("key_findings", [])
        analysis.setdefault("patterns", [])
        analysis.setdefault("contradictions", [])
        analysis.setdefault("confidence_score", 0.5)
        analysis.setdefault("citations", [])
        analysis.setdefault("data_points", [])
        analysis.setdefault("expert_opinions", [])
        analysis.setdefault("gaps", [])
        
        # Ensure confidence score is within bounds
        analysis["confidence_score"] = max(0.0, min(1.0, analysis["confidence_score"]))
        
        # Add source citations if missing
        if not analysis["citations"]:
            analysis["citations"] = [
                {
                    "url": s.get("url", ""),
                    "title": s.get("title", ""),
                    "relevance": 0.7
                }
                for s in sources[:5]
            ]
        
        return analysis
    
    def _fallback_analysis(self, topic: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
        """Create a basic fallback analysis."""
        return {
            "key_findings": [
                f"Found {len(sources)} sources about {topic}",
                "Detailed analysis unavailable due to processing error"
            ],
            "patterns": [],
            "contradictions": [],
            "confidence_score": 0.3,
            "citations": [
                {
                    "url": s.get("url", ""),
                    "title": s.get("title", ""),
                    "relevance": 0.5
                }
                for s in sources[:3]
            ],
            "data_points": [],
            "expert_opinions": [],
            "gaps": ["Full analysis could not be completed"]
        }
