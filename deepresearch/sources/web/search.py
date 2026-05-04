"""
Web Searcher - Searches the web using DuckDuckGo.
"""

import logging
from typing import Any

from deepresearch.agents.planner.planner import Source

logger = logging.getLogger(__name__)


class WebSearcher:
    """
    Web search using DuckDuckGo.
    
    Features:
    - Text search
    - News search
    - Result ranking
    - Snippet extraction
    """
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
    
    async def search(self, query: str, max_results: int = 5) -> list[Source]:
        """
        Search the web for a query.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of Source objects
        """
        try:
            # Try using ddgs CLI first
            import subprocess
            result = subprocess.run(
                ["ddgs", "text", "-q", query, "-m", str(max_results), "-o", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                import json
                results = json.loads(result.stdout)
                
                sources = []
                for r in results:
                    sources.append(Source(
                        url=r.get("href", ""),
                        title=r.get("title", ""),
                        snippet=r.get("body", "")[:300],
                        source_type="web",
                        confidence=0.6
                    ))
                
                return sources
            else:
                # Fallback to Python library
                return await self._search_with_library(query, max_results)
                
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []
    
    async def _search_with_library(self, query: str, max_results: int) -> list[Source]:
        """Search using DuckDuckGo Python library."""
        try:
            from ddgs import DDGS
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                
                sources = []
                for r in results:
                    sources.append(Source(
                        url=r.get("href", ""),
                        title=r.get("title", ""),
                        snippet=r.get("body", "")[:300],
                        source_type="web",
                        confidence=0.6
                    ))
                
                return sources
        except Exception as e:
            logger.error(f"Library search failed: {e}")
            return []
    
    async def search_news(self, query: str, max_results: int = 5) -> list[Source]:
        """Search for news articles."""
        try:
            import subprocess
            result = subprocess.run(
                ["ddgs", "news", "-q", query, "-m", str(max_results), "-o", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                import json
                results = json.loads(result.stdout)
                
                sources = []
                for r in results:
                    sources.append(Source(
                        url=r.get("url", ""),
                        title=r.get("title", ""),
                        snippet=r.get("body", "")[:300],
                        source_type="news",
                        confidence=0.7
                    ))
                
                return sources
            else:
                return []
        except Exception as e:
            logger.error(f"News search failed: {e}")
            return []
