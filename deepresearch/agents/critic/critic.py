"""
Critic Agent - Reviews report quality and suggests improvements.
"""

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class CriticAgent:
    """
    Autonomous critic agent that reviews report quality.
    
    Features:
    - Quality assessment
    - Accuracy verification
    - Completeness check
    - Improvement suggestions
    - Confidence scoring
    """
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.llm_endpoint = config.get("llm_endpoint", "https://api.mimo.xiaomi.com/v1/chat/completions")
        self.llm_key = config.get("llm_key", "")
        self.model = config.get("model", "mimo-7b")
    
    async def review(
        self,
        report: str,
        topic: str,
        sources: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Review a research report and provide feedback.
        
        Args:
            report: The report to review
            topic: The original research topic
            sources: The sources used
            
        Returns:
            Review with feedback, confidence score, and revision needs
        """
        logger.info(f"Reviewing report for: {topic}")
        
        prompt = f"""You are a research quality critic. Review this report:

TOPIC: {topic}

REPORT:
{report}

SOURCES USED: {len(sources)}

Provide a comprehensive review in JSON format:
1. overall_quality: "excellent", "good", "fair", or "poor"
2. confidence_score: 0.0-1.0 based on evidence quality
3. strengths: List of report strengths
4. weaknesses: List of issues found
5. accuracy_issues: Any factual concerns
6. completeness_gaps: Missing information
7. improvement_suggestions: Specific recommendations
8. needs_revision: true if major issues found
9. source_quality: Assessment of source reliability

Return ONLY valid JSON."""

        try:
            response = await self._call_llm(prompt)
            review = json.loads(response)
            
            # Validate review
            review = self._validate_review(review)
            
            logger.info(f"Review complete: {review['overall_quality']} (confidence: {review['confidence_score']:.1%})")
            return review
            
        except Exception as e:
            logger.error(f"Review failed: {e}")
            return self._fallback_review()
    
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
                        {"role": "system", "content": "You are a research quality critic. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,  # Lower temperature for more consistent reviews
                    "max_tokens": 1500
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                raise Exception(f"LLM API error: {response.status_code}")
    
    def _validate_review(self, review: dict[str, Any]) -> dict[str, Any]:
        """Validate and enhance review."""
        review.setdefault("overall_quality", "fair")
        review.setdefault("confidence_score", 0.5)
        review.setdefault("strengths", [])
        review.setdefault("weaknesses", [])
        review.setdefault("accuracy_issues", [])
        review.setdefault("completeness_gaps", [])
        review.setdefault("improvement_suggestions", [])
        review.setdefault("needs_revision", False)
        review.setdefault("source_quality", "unknown")
        
        # Ensure confidence score is within bounds
        review["confidence_score"] = max(0.0, min(1.0, review["confidence_score"]))
        
        # Determine if revision is needed based on quality
        if review["overall_quality"] in ["poor", "fair"]:
            review["needs_revision"] = True
        
        # Check for major issues
        if len(review["accuracy_issues"]) > 2 or len(review["weaknesses"]) > 3:
            review["needs_revision"] = True
        
        return review
    
    def _fallback_review(self) -> dict[str, Any]:
        """Create a basic fallback review."""
        return {
            "overall_quality": "fair",
            "confidence_score": 0.5,
            "strengths": ["Report structure is clear"],
            "weaknesses": ["Could not complete full review"],
            "accuracy_issues": [],
            "completeness_gaps": ["Full review unavailable"],
            "improvement_suggestions": ["Verify facts with additional sources"],
            "needs_revision": False,
            "source_quality": "unknown"
        }
