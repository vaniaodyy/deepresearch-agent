"""
Researcher Agent - Executes searches and extracts data from multiple sources.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from deepresearch.sources.web.search import WebSearcher

logger = logging.getLogger(__name__)


class Source(BaseModel):
    """A research source."""
    url: str
    title: str
    snippet: str
    content: str | None = None
    source_type: str  # web, arxiv, reddit, github, news
    confidence: float = 0.0
    retrieved_at: datetime = datetime.now()


class ResearcherAgent:
    """
    Autonomous research agent that executes searches and extracts data.
    
    Features:
    - Multi-source search (web, arxiv, reddit, github, news)
    - Parallel search execution
    - Content extraction and cleaning
    - Source reliability scoring
    """
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.web_searcher = WebSearcher(config)
        self.max_sources_per_query = config.get("max_sources_per_query", 5)
        self.parallel_searches = config.get("parallel_searches", 3)
    
    async def execute_plan(self, plan: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Execute a research plan by running searches across multiple sources.
        
        Args:
            plan: The research plan from PlannerAgent
            
        Returns:
            List of sources found
        """
        sub_queries = plan.get("sub_queries", [])
        sources_to_check = plan.get("sources_to_check", ["web"])
        
        logger.info(f"Executing plan: {len(sub_queries)} queries across {sources_to_check}")
        
        all_sources = []
        
        # Run searches in parallel batches
        for i in range(0, len(sub_queries), self.parallel_searches):
            batch = sub_queries[i:i + self.parallel_searches]
            
            batch_tasks = []
            for query in batch:
                for source_type in sources_to_check:
                    batch_tasks.append(
                        self._search_source(query, source_type)
                    )
            
            # Execute batch in parallel
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Collect valid results
            for result in batch_results:
                if isinstance(result, list):
                    all_sources.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Search failed: {result}")
        
        # Deduplicate and rank sources
        sources = self._deduplicate_sources(all_sources)
        sources = self._rank_sources(sources)
        
        logger.info(f"Found {len(sources)} unique sources")
        
        return [source.model_dump() for source in sources]
    
    async def _search_source(self, query: str, source_type: str) -> list[Source]:
        """Search a specific source type."""
        try:
            if source_type == "web":
                return await self.web_searcher.search(query, max_results=self.max_sources_per_query)
            elif source_type == "arxiv":
                return await self._search_arxiv(query)
            elif source_type == "reddit":
                return await self._search_reddit(query)
            elif source_type == "github":
                return await self._search_github(query)
            elif source_type == "news":
                return await self._search_news(query)
            else:
                logger.warning(f"Unknown source type: {source_type}")
                return []
        except Exception as e:
            logger.error(f"Search failed for {source_type}: {e}")
            return []
    
    async def _search_arxiv(self, query: str) -> list[Source]:
        """Search arXiv for academic papers."""
        try:
            import arxiv
            
            search = arxiv.Search(
                query=query,
                max_results=self.max_sources_per_query,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            sources = []
            for result in search.results():
                sources.append(Source(
                    url=result.pdf_url,
                    title=result.title,
                    snippet=result.summary[:300],
                    content=result.summary,
                    source_type="arxiv",
                    confidence=0.9  # Academic sources are highly reliable
                ))
            
            return sources
        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
            return []
    
    async def _search_reddit(self, query: str) -> list[Source]:
        """Search Reddit for discussions."""
        # Placeholder - implement with PRAW or web scraping
        return []
    
    async def _search_github(self, query: str) -> list[Source]:
        """Search GitHub for repositories and code."""
        # Placeholder - implement with GitHub API
        return []
    
    async def _search_news(self, query: str) -> list[Source]:
        """Search for news articles."""
        # Use web searcher with news-specific query
        return await self.web_searcher.search(
            f"{query} news latest",
            max_results=self.max_sources_per_query
        )
    
    def _deduplicate_sources(self, sources: list[Source]) -> list[Source]:
        """Remove duplicate sources based on URL."""
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            if source.url not in seen_urls:
                seen_urls.add(source.url)
                unique_sources.append(source)
        
        return unique_sources
    
    def _rank_sources(self, sources: list[Source]) -> list[Source]:
        """Rank sources by reliability and relevance."""
        def source_priority(source: Source) -> float:
            # Academic sources are most reliable
            type_scores = {
                "arxiv": 0.9,
                "github": 0.8,
                "news": 0.7,
                "web": 0.6,
                "reddit": 0.5
            }
            return type_scores.get(source.source_type, 0.5) + source.confidence
        
        return sorted(sources, key=source_priority, reverse=True)
