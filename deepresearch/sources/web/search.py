"""
Web Searcher - Searches the web using DuckDuckGo.
"""

import logging
from typing import Any

from deepresearch.models import Source

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
                ["ddgs", "text", "-q", query, "-m", str(max_results)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse the custom format
                sources = self._parse_ddgs_output(result.stdout, "web")
                return sources[:max_results]
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
                ["ddgs", "news", "-q", query, "-m", str(max_results)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse the custom format
                sources = self._parse_ddgs_output(result.stdout, "news")
                return sources[:max_results]
            else:
                return []
        except Exception as e:
            logger.error(f"News search failed: {e}")
            return []
    
    def _parse_ddgs_output(self, output: str, source_type: str) -> list[Source]:
        """Parse ddgs CLI output format."""
        sources = []
        lines = output.strip().split('\n')
        
        i = 0
        while i < len(lines):
            # Look for numbered entries (1., 2., etc.)
            if lines[i].strip().endswith('.') and lines[i].strip()[:-1].isdigit():
                # Found an entry, parse it
                title = ""
                href = ""
                body = ""
                
                i += 1
                while i < len(lines) and not (lines[i].strip().endswith('.') and lines[i].strip()[:-1].isdigit()):
                    line = lines[i].strip()
                    if line.startswith('title'):
                        title = line[5:].strip()
                    elif line.startswith('href'):
                        href = line[4:].strip()
                    elif line.startswith('body'):
                        body = line[4:].strip()
                    elif title and not line.startswith(('title', 'href', 'body')):
                        # Continuation of body
                        body += " " + line
                    i += 1
                
                if title and href:
                    sources.append(Source(
                        url=href,
                        title=title,
                        snippet=body[:300],
                        source_type=source_type,
                        confidence=0.6 if source_type == "web" else 0.7
                    ))
            else:
                i += 1
        
        return sources
