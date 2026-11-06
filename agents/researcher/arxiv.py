import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from agents.researcher.base import BaseCollector
from agents.resilience import robust_request

class ArxivCollector(BaseCollector):
    """
    Collector for arXiv API (Atom XML) using resilient HTTP requests.
    Covers: Artificial Intelligence, Computer Science, Physics, Mathematics, Quantitative Biology.
    """

    @property
    def source_name(self) -> str:
        return "arxiv"

    def search(self, topic: str, max_results: int = 5) -> List[Dict[str, Any]]:
        if not topic.strip():
            raise ValueError("Research topic cannot be empty.")
        if max_results < 1:
            raise ValueError("max_results must be positive.")

        base_url = "http://export.arxiv.org/api/query"
        headers = {"User-Agent": "SAKHR-Discovery-Agent/1.0"}

        print(f"\nSearching arXiv for: {topic}")

        params = {
            "search_query": f"all:{topic}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }

        try:
            response = robust_request("GET", base_url, params=params, headers=headers, timeout=30, source_name="arxiv")
            if not response or response.status_code != 200:
                print("arXiv search failed or returned non-200 status.")
                return []
        except Exception as e:
            print(f"arXiv search error: {e}")
            return []

        try:
            root = ET.fromstring(response.content)
        except Exception as e:
            print(f"arXiv XML parsing error: {e}")
            return []

        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

        entries = root.findall("atom:entry", ns)
        if not entries:
            print("No arXiv publications found.")
            return []

        print(f"Found {len(entries)} arXiv publications.")
        papers = []

        for entry in entries:
            id_url = entry.findtext("atom:id", default="", namespaces=ns)
            arxiv_id = id_url.split("/abs/")[-1] if "/abs/" in id_url else id_url

            title = entry.findtext("atom:title", default="No title", namespaces=ns).strip().replace("\n", " ")
            abstract = entry.findtext("atom:summary", default="No abstract available.", namespaces=ns).strip().replace("\n", " ")
            published = entry.findtext("atom:published", default=None, namespaces=ns)

            authors = []
            for author_elem in entry.findall("atom:author", namespaces=ns):
                name = author_elem.findtext("atom:name", default="", namespaces=ns)
                if name:
                    authors.append(name.strip())

            doi_elem = entry.find("arxiv:doi", namespaces=ns)
            doi = doi_elem.text.strip() if doi_elem is not None and doi_elem.text else None

            url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else id_url

            normalized = self.normalize_record(
                source_id=arxiv_id,
                title=title,
                abstract=abstract,
                authors=authors,
                doi=doi,
                arxiv_id=arxiv_id,
                published_date=published[:10] if published else None,
                url=url,
                disciplines=["Artificial Intelligence", "Computer Science", "Physics", "Mathematics", "Quantitative Biology"],
                is_preprint=True
            )
            papers.append(normalized)

        print(f"Successfully retrieved and normalized {len(papers)} arXiv records.")
        return papers
