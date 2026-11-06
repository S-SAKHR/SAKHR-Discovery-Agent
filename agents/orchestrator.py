from typing import List, Dict, Any
from agents.researcher.pubmed import PubMedCollector
from agents.researcher.arxiv import ArxivCollector
from agents.researcher.openalex import OpenAlexCollector
from agents.researcher.semantic_scholar import SemanticScholarCollector
from agents.researcher.crossref import CrossrefCollector
from agents.deduplication import deduplicate_papers
from agents.resilience import get_cached_search, set_cached_search

class ResearchOrchestrator:
    """
    Multidisciplinary Research Orchestrator.
    Routes research queries to relevant scientific collectors (PubMed, arXiv, OpenAlex, Semantic Scholar, Crossref),
    executes resilient searches with caching, fallback, source provenance, and deduplication.
    """

    def __init__(self):
        self.pubmed = PubMedCollector()
        self.arxiv = ArxivCollector()
        self.openalex = OpenAlexCollector()
        self.semantic_scholar = SemanticScholarCollector()
        self.crossref = CrossrefCollector()

    def route_query(self, topic: str) -> List[Any]:
        """
        Discipline-aware source routing based on query keywords.
        Always includes broad multidisciplinary collectors (OpenAlex, Semantic Scholar, Crossref),
        and dynamically routes to arXiv or PubMed based on domain keywords.
        """
        topic_lower = topic.lower()
        collectors = [self.openalex, self.semantic_scholar, self.crossref]

        ai_cs_physics_keywords = [
            "ai", "artificial intelligence", "machine learning", "deep learning",
            "transformer", "neural", "quantum", "physics", "black hole", "astronomy",
            "algorithm", "computation", "robotics", "mathematics", "algebra", "topology",
            "computer science", "nlp", "llm"
        ]

        bio_med_keywords = [
            "crispr", "gene", "protein", "cell", "alzheimer", "cancer", "disease",
            "biology", "medicine", "clinical", "neuroscience", "brain", "neuron",
            "biotechnology", "biomedical", "immunology", "therapy", "drug"
        ]

        needs_arxiv = any(kw in topic_lower for kw in ai_cs_physics_keywords)
        needs_pubmed = any(kw in topic_lower for kw in bio_med_keywords)

        if needs_arxiv or (not needs_pubmed and not needs_arxiv):
            collectors.append(self.arxiv)

        if needs_pubmed or (not needs_pubmed and not needs_arxiv):
            collectors.append(self.pubmed)

        return collectors

    def search(self, topic: str, max_results_per_source: int = 3) -> List[Dict[str, Any]]:
        """
        Executes resilient search with caching, provenance tracking, and fallback.
        Returns unified sorted collection, attaching provenance metadata.
        """
        if not topic.strip():
            raise ValueError("Research topic cannot be empty.")

        cache_key = f"{topic.lower().strip()}:{max_results_per_source}"
        cached_result = get_cached_search(cache_key)
        if cached_result is not None:
            print(f"\n[Orchestrator] Cache hit for topic: '{topic}'")
            return cached_result

        collectors = self.route_query(topic)
        print(f"\n[Orchestrator] Topic: '{topic}'")
        print(f"[Orchestrator] Selected collectors: {[c.source_name for c in collectors]}")

        raw_papers = []
        successful_sources = []
        failed_sources = []

        for collector in collectors:
            try:
                papers = collector.search(topic, max_results=max_results_per_source)
                if papers:
                    raw_papers.extend(papers)
                    successful_sources.append(collector.source_name)
                else:
                    failed_sources.append(collector.source_name)
            except Exception as e:
                print(f"[Orchestrator] Collector {collector.source_name} failed: {e}")
                failed_sources.append(collector.source_name)

        incomplete_search = len(failed_sources) > 0 and len(successful_sources) > 0

        if not raw_papers:
            print("[Orchestrator] No publications retrieved from any source.")
            return []

        # Deduplicate across sources
        unique_papers = deduplicate_papers(raw_papers)

        # Rank results by abstract richness
        unique_papers.sort(key=lambda p: len(p.get("abstract", "")), reverse=True)

        # Attach provenance metadata to papers or return via orchestrator context if needed
        for paper in unique_papers:
            paper["provenance"] = {
                "successful_sources": successful_sources,
                "failed_sources": failed_sources,
                "incomplete_search": incomplete_search
            }

        set_cached_search(cache_key, unique_papers)
        return unique_papers
