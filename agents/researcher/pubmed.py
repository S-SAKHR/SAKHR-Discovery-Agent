import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from agents.researcher.base import BaseCollector
from agents.resilience import robust_request

class PubMedCollector(BaseCollector):
    """
    Collector for NCBI PubMed (NCBI E-utilities) using resilient HTTP requests.
    Covers: Biology, Medicine, Neuroscience, Biomedical Engineering.
    """

    @property
    def source_name(self) -> str:
        return "pubmed"

    def search(self, topic: str, max_results: int = 5) -> List[Dict[str, Any]]:
        if not topic.strip():
            raise ValueError("Research topic cannot be empty.")
        if max_results < 1:
            raise ValueError("max_results must be positive.")

        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        headers = {"User-Agent": "SAKHR-Discovery-Agent/1.0"}

        print(f"\nSearching PubMed for: {topic}")

        # 1. ESearch
        search_url = base_url + "esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": topic,
            "retmax": max_results,
            "sort": "relevance",
            "retmode": "json"
        }

        try:
            response = robust_request("GET", search_url, params=params, headers=headers, timeout=30, source_name="pubmed")
            if not response or response.status_code != 200:
                print("PubMed search failed or returned non-200 status.")
                return []
            data = response.json()
        except Exception as e:
            print(f"PubMed search error: {e}")
            return []

        pmids = data.get("esearchresult", {}).get("idlist", [])
        if not pmids:
            print("No PubMed publications found.")
            return []

        print(f"Found {len(pmids)} PubMed publications.")

        # 2. EFetch
        fetch_url = base_url + "efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }

        try:
            res_fetch = robust_request("GET", fetch_url, params=fetch_params, headers=headers, timeout=30, source_name="pubmed")
            if not res_fetch or res_fetch.status_code != 200:
                print("PubMed fetch failed or returned non-200 status.")
                return []
            root = ET.fromstring(res_fetch.content)
        except Exception as e:
            print(f"PubMed fetch error: {e}")
            return []

        papers = []
        for article in root.findall(".//PubmedArticle"):
            pmid = article.findtext(".//PMID", default="Unknown")

            # Extract title
            title_element = article.find(".//ArticleTitle")
            title = "".join(title_element.itertext()) if title_element is not None else "No title"

            # Extract abstract
            abstract_elements = article.findall(".//Abstract/AbstractText")
            abstract_parts = []
            for element in abstract_elements:
                text = "".join(element.itertext())
                label = element.get("Label")
                if label:
                    text = f"{label}: {text}"
                abstract_parts.append(text)
            abstract = " ".join(abstract_parts) if abstract_parts else "No abstract available."

            # Extract DOI if available
            doi = None
            for aid in article.findall(".//ArticleId"):
                if aid.get("IdType") == "doi":
                    doi = aid.text
                    break

            # Extract authors
            authors = []
            for author in article.findall(".//AuthorList/Author"):
                last_name = author.findtext("LastName")
                fore_name = author.findtext("ForeName")
                if last_name:
                    full_name = f"{fore_name} {last_name}".strip() if fore_name else last_name
                    authors.append(full_name)

            # URL
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid != "Unknown" else None

            normalized = self.normalize_record(
                source_id=pmid,
                title=title,
                abstract=abstract,
                authors=authors,
                doi=doi,
                pmid=pmid if pmid != "Unknown" else None,
                url=url,
                disciplines=["Biology", "Medicine", "Neuroscience", "Biomedical Engineering"],
                is_preprint=False
            )
            papers.append(normalized)

        print(f"Successfully retrieved and normalized {len(papers)} PubMed records.")
        return papers
