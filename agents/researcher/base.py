from abc import ABC, abstractmethod
from typing import List, Dict, Any
import uuid
from datetime import datetime, timezone

class BaseCollector(ABC):
    """
    Abstract base class for all scientific literature collectors.
    Ensures a consistent search interface and unified normalized output schema.
    """
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the unique name of the source (e.g. 'pubmed', 'arxiv', 'openalex')."""
        pass

    @abstractmethod
    def search(self, topic: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the scientific database for the given topic.
        Returns a list of normalized publication records.
        """
        pass

    def normalize_record(
        self,
        source_id: str,
        title: str,
        abstract: str,
        authors: List[str] = None,
        doi: str = None,
        pmid: str = None,
        arxiv_id: str = None,
        openalex_id: str = None,
        published_date: str = None,
        url: str = None,
        disciplines: List[str] = None,
        is_preprint: bool = False
    ) -> Dict[str, Any]:
        """
        Helper method to construct a strictly normalized publication record.
        """
        return {
            "paper_id": str(uuid.uuid4()),
            "source": self.source_name,
            "source_id": str(source_id) if source_id else None,
            "pmid": str(pmid) if pmid else None,
            "doi": doi.strip() if doi else None,
            "arxiv_id": arxiv_id.strip() if arxiv_id else None,
            "openalex_id": openalex_id.strip() if openalex_id else None,
            "title": title.strip() if title else "No title",
            "abstract": abstract.strip() if abstract else "No abstract available.",
            "authors": authors if authors else [],
            "published_date": published_date,
            "url": url,
            "disciplines": disciplines if disciplines else [],
            "is_preprint": is_preprint,
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
