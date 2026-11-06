from typing import List, Dict, Any
from agents.researcher.base import BaseCollector
from agents.resilience import robust_request

class OpenAlexCollector(BaseCollector):
    """
    Collector for OpenAlex REST API using resilient HTTP requests.
    Covers: Multidisciplinary scientific literature across all domains.
    """

    @property
    def source_name(self) -> str:
        return "openalex"

    def _reconstruct_abstract(self, inverted_index: Dict[str, List[int]]) -> str:
        """
        OpenAlex stores abstracts as inverted indexes {word: [positions]}.
        Reconstructs the original abstract string.
        """
        if not inverted_index or not isinstance(inverted_index, dict):
            return "No abstract available."
        
        max_pos = -1
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
                if pos > max_pos:
                    max_pos = pos

        if max_pos == -1:
            return "No abstract available."

        words = [""] * (max_pos + 1)
        for pos, word in word_positions:
            if 0 <= pos <= max_pos:
                words[pos] = word

        return " ".join([w for w in words if w])

    def search(self, topic: str, max_results: int = 5) -> List[Dict[str, Any]]:
        if not topic.strip():
            raise ValueError("Research topic cannot be empty.")
        if max_results < 1:
            raise ValueError("max_results must be positive.")

        url = "https://api.openalex.org/works"
        headers = {
            "User-Agent": "SAKHR-Discovery-Agent/1.0 (mailto:sakhr-agent@example.com)"
        }

        print(f"\nSearching OpenAlex for: {topic}")

        params = {
            "search": topic,
            "per_page": max_results
        }

        try:
            response = robust_request("GET", url, params=params, headers=headers, timeout=30, source_name="openalex")
            if not response or response.status_code != 200:
                print("OpenAlex search failed or returned non-200 status.")
                return []
            data = response.json()
        except Exception as e:
            print(f"OpenAlex search error: {e}")
            return []

        results = data.get("results", [])
        if not results:
            print("No OpenAlex publications found.")
            return []

        print(f"Found {len(results)} OpenAlex publications.")
        papers = []

        for work in results:
            openalex_url = work.get("id", "")
            openalex_id = openalex_url.split("/")[-1] if openalex_url else None

            title = work.get("title") or work.get("display_name") or "No title"
            
            inv_index = work.get("abstract_inverted_index")
            abstract = self._reconstruct_abstract(inv_index)

            ids = work.get("ids", {})
            doi_raw = work.get("doi") or ids.get("doi")
            doi = doi_raw.replace("https://doi.org/", "").strip() if doi_raw else None

            pmid_raw = ids.get("pmid")
            pmid = str(pmid_raw).replace("https://pubmed.ncbi.nlm.nih.gov/", "").strip() if pmid_raw else None

            arxiv_raw = ids.get("arxiv")
            arxiv_id = str(arxiv_raw).strip() if arxiv_raw else None

            authors = []
            for auth in work.get("authorships", []):
                author_obj = auth.get("author", {})
                name = author_obj.get("display_name")
                if name:
                    authors.append(name.strip())

            published_date = work.get("publication_date")
            primary_loc = work.get("primary_location") or {}
            landing_url = primary_loc.get("landing_page_url") or work.get("doi") or openalex_url

            pub_type = work.get("type", "")
            is_preprint = pub_type.lower() in ["preprint", "repository"]

            disciplines = []
            for concept in work.get("concepts", []):
                c_name = concept.get("display_name")
                if c_name and concept.get("score", 0) > 0.3:
                    disciplines.append(c_name)
            if not disciplines:
                disciplines = ["Multidisciplinary Science"]

            normalized = self.normalize_record(
                source_id=openalex_id,
                title=title,
                abstract=abstract,
                authors=authors,
                doi=doi,
                pmid=pmid,
                arxiv_id=arxiv_id,
                openalex_id=openalex_id,
                published_date=published_date,
                url=landing_url,
                disciplines=disciplines,
                is_preprint=is_preprint
            )
            papers.append(normalized)

        print(f"Successfully retrieved and normalized {len(papers)} OpenAlex records.")
        return papers
