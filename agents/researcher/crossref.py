import re
from typing import List, Dict, Any
from agents.researcher.base import BaseCollector
from agents.resilience import robust_request

class CrossrefCollector(BaseCollector):
    """
    Collector for Crossref REST API using resilient HTTP requests.
    Covers: Broad multidisciplinary scholarly publications, journals, and books.
    """

    @property
    def source_name(self) -> str:
        return "crossref"

    def _clean_abstract(self, raw_abstract: str) -> str:
        """Remove JATS XML tags from Crossref abstracts if present."""
        if not raw_abstract:
            return "No abstract available."
        cleaned = re.sub(r'<[^>]+>', '', raw_abstract)
        return cleaned.strip()

    def _extract_date(self, item: Dict[str, Any]) -> str:
        """Extract date string from Crossref date fields."""
        for date_key in ["published-print", "published-online", "issued"]:
            date_obj = item.get(date_key, {})
            parts = date_obj.get("date-parts", [])
            if parts and len(parts) > 0 and len(parts[0]) > 0:
                year = parts[0][0]
                month = parts[0][1] if len(parts[0]) > 1 else 1
                day = parts[0][2] if len(parts[0]) > 2 else 1
                try:
                    return f"{year:04d}-{month:02d}-{day:02d}"
                except Exception:
                    return str(year)
        return None

    def search(self, topic: str, max_results: int = 5) -> List[Dict[str, Any]]:
        if not topic.strip():
            raise ValueError("Research topic cannot be empty.")
        if max_results < 1:
            raise ValueError("max_results must be positive.")

        url = "https://api.crossref.org/works"
        headers = {
            "User-Agent": "SAKHR-Discovery-Agent/1.0 (mailto:sakhr-agent@example.com)"
        }

        print(f"\nSearching Crossref for: {topic}")

        params = {
            "query": topic,
            "rows": max_results
        }

        try:
            response = robust_request("GET", url, params=params, headers=headers, timeout=30, source_name="crossref")
            if not response or response.status_code != 200:
                print("Crossref search failed or returned non-200 status.")
                return []
            data = response.json()
        except Exception as e:
            print(f"Crossref search error: {e}")
            return []

        message = data.get("message", {})
        items = message.get("items", [])
        if not items:
            print("No Crossref publications found.")
            return []

        print(f"Found {len(items)} Crossref publications.")
        papers = []

        for item in items:
            doi = item.get("DOI")
            source_id = doi or item.get("ISSN") or item.get("publisher")

            title_list = item.get("title", [])
            title = title_list[0] if title_list else "No title"

            abstract_raw = item.get("abstract")
            abstract = self._clean_abstract(abstract_raw)

            authors = []
            for auth in item.get("author", []):
                given = auth.get("given", "")
                family = auth.get("family", "")
                if family:
                    full_name = f"{given} {family}".strip() if given else family
                    authors.append(full_name)

            published_date = self._extract_date(item)
            crossref_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else None)

            subjects = item.get("subject", [])
            disciplines = [s for s in subjects] if subjects else ["Multidisciplinary Science"]

            normalized = self.normalize_record(
                source_id=source_id,
                title=title,
                abstract=abstract,
                authors=authors,
                doi=doi,
                published_date=published_date,
                url=crossref_url,
                disciplines=disciplines,
                is_preprint=False
            )
            papers.append(normalized)

        print(f"Successfully retrieved and normalized {len(papers)} Crossref records.")
        return papers
