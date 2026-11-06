import re
from typing import List, Dict, Any

def normalize_title(title: str) -> str:
    """Normalize title for conservative matching: lowercase, remove non-alphanumeric chars."""
    if not title:
        return ""
    # Lowercase and remove punctuation/extra whitespace
    cleaned = re.sub(r'[^\w\s]', '', title.lower())
    return re.sub(r'\s+', ' ', cleaned).strip()

def deduplicate_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates a list of normalized publication records across multiple sources.
    Priority matching:
    1. DOI
    2. PMID
    3. arXiv ID
    4. OpenAlex ID
    5. Conservative normalized title matching
    
    Preserves and aggregates all source references and identifiers.
    """
    if not papers:
        return []

    merged_map = {} # map key -> unified paper record
    
    # Index maps for fast lookups
    doi_index = {}
    pmid_index = {}
    arxiv_index = {}
    openalex_index = {}
    title_index = {}

    for paper in papers:
        # Extract identifiers
        doi = paper.get("doi")
        pmid = paper.get("pmid")
        arxiv_id = paper.get("arxiv_id")
        openalex_id = paper.get("openalex_id")
        raw_title = paper.get("title", "")
        norm_title = normalize_title(raw_title)

        # Check existing match
        target_key = None

        if doi and doi in doi_index:
            target_key = doi_index[doi]
        elif pmid and pmid in pmid_index:
            target_key = pmid_index[pmid]
        elif arxiv_id and arxiv_id in arxiv_index:
            target_key = arxiv_index[arxiv_id]
        elif openalex_id and openalex_id in openalex_index:
            target_key = openalex_index[openalex_id]
        elif norm_title and len(norm_title) > 10 and norm_title in title_index:
            target_key = title_index[norm_title]

        if target_key is not None:
            # Merge into existing record
            existing = merged_map[target_key]
            
            # Update missing identifiers
            if not existing.get("doi") and doi:
                existing["doi"] = doi
            if not existing.get("pmid") and pmid:
                existing["pmid"] = pmid
            if not existing.get("arxiv_id") and arxiv_id:
                existing["arxiv_id"] = arxiv_id
            if not existing.get("openalex_id") and openalex_id:
                existing["openalex_id"] = openalex_id
            
            # Merge authors
            existing_authors = set(existing.get("authors", []))
            for author in paper.get("authors", []):
                if author not in existing_authors:
                    existing["authors"].append(author)

            # Merge disciplines
            existing_disc = set(existing.get("disciplines", []))
            for disc in paper.get("disciplines", []):
                if disc not in existing_disc:
                    existing["disciplines"].append(disc)

            # Track sources
            sources_list = existing.setdefault("sources_list", [])
            source_entry = {"source": paper.get("source"), "source_id": paper.get("source_id")}
            if source_entry not in sources_list:
                sources_list.append(source_entry)

            # Keep longest abstract if current is short
            if len(paper.get("abstract", "")) > len(existing.get("abstract", "")):
                existing["abstract"] = paper.get("abstract")

        else:
            # Create new unique record
            paper_id = paper["paper_id"]
            paper["sources_list"] = [{"source": paper.get("source"), "source_id": paper.get("source_id")}]
            merged_map[paper_id] = paper
            target_key = paper_id

            # Index identifiers
            if doi:
                doi_index[doi] = target_key
            if pmid:
                pmid_index[pmid] = target_key
            if arxiv_id:
                arxiv_index[arxiv_id] = target_key
            if openalex_id:
                openalex_index[openalex_id] = target_key
            if norm_title and len(norm_title) > 10:
                title_index[norm_title] = target_key

    unique_papers = list(merged_map.values())
    print(f"Deduplication: Reduced {len(papers)} records to {len(unique_papers)} unique publications.")
    return unique_papers
