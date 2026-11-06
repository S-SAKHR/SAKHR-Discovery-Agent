from typing import List, Dict, Any
from agents.researcher.base import BaseCollector
from agents.resilience import robust_request
import os

class SemanticScholarCollector(BaseCollector):
    """
    Collector for Semantic Scholar REST API using resilient HTTP requests.
    Covers: Computer Science, Biomedicine, Neuroscience, Multidisciplinary Science.
    """

    @property
    def source_name(self) -> str:
        return "semantic_scholar"

    def search(self, topic: str, max_results: int = 5) -> List[Dict[str, Any]]:
        if not topic.strip():
            raise ValueError("Research topic cannot be empty.")
        if max_results < 1:
            raise ValueError("max_results must be positive.")

        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        headers = {
            "User-Agent": "SAKHR-Discovery-Agent/1.0"
        }
        
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        if api_key:
            headers["x-api-key"] = api_key

        print(f"\nSearching Semantic Scholar for: {topic}")

        params = {
            "query": topic,
            "limit": max_results,
            "fields": "paperId,externalIds,title,abstract,authors,publicationDate,url,isOpenAccess,fieldsOfStudy"
        }

        try:
            response = robust_request("GET", url, params=params, headers=headers, timeout=30, source_name="semantic_scholar")
            if not response:
                return []
            if response.status_code == 429:
                print("Semantic Scholar rate limit reached (HTTP 429). Skipping source gracefully.")
                return []
            if response.status_code != 200:
                print(f"Semantic Scholar returned status {response.status_code}")
                return []
            data = response.json()
        except Exception as e:
            print(f"Semantic Scholar search error: {e}")
            return []

        results = data.get("data", [])
        if not results:
            print("No Semantic Scholar publications found.")
            return []

        print(f"Found {len(results)} Semantic Scholar publications.")
        papers = []

        for work in results:
            source_id = work.get("paperId")
            title = work.get("title") or "No title"
            abstract = work.get("abstract") or "No abstract available."

            ext_ids = work.get("externalIds", {})
            doi = ext_ids.get("DOI")
            pmid = ext_ids.get("PubMed")
            arxiv_id = ext_ids.get("ArXiv")

            authors = []
            for author in work.get("authors", []):
                name = author.get("name")
                if name:
                    authors.append(name.strip())

            published_date = work.get("publicationDate")
            url = work.get("url") or (f"https://www.semanticscholar.org/paper/{source_id}" if source_id else None)

            fields = work.get("fieldsOfStudy", [])
            disciplines = [f for f in fields] if fields else ["Computer Science", "Biomedicine"]

            is_oa = work.get("isOpenAccess", False)

            normalized = self.normalize_record(
                source_id=source_id,
                title=title,
                abstract=abstract,
                authors=authors,
                doi=doi,
                pmid=pmid,
                arxiv_id=arxiv_id,
                published_date=published_date,
                url=url,
                disciplines=disciplines,
                is_preprint=is_oa
            )
            papers.append(normalized)

        print(f"Successfully retrieved and normalized {len(papers)} Semantic Scholar records.")
        return papers
