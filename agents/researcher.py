import requests
import xml.etree.ElementTree as ET


# =====================================
# PUBMED CONFIGURATION
# =====================================

BASE_URL = (
    "https://eutils.ncbi.nlm.nih.gov/"
    "entrez/eutils/"
)

HEADERS = {
    "User-Agent": "SAKHR-Discovery-Agent/1.0"
}


# =====================================
# SEARCH PUBMED
# =====================================

def search_pubmed(topic, max_results=5):

    if not topic.strip():
        raise ValueError("Research topic cannot be empty.")

    if max_results < 1:
        raise ValueError("max_results must be positive.")

    print(f"\nSearching PubMed for: {topic}")

    search_url = BASE_URL + "esearch.fcgi"

    params = {

        "db": "pubmed",

        "term": topic,

        "retmax": max_results,

        "sort": "relevance",

        "retmode": "json"

    }

    response = requests.get(

        search_url,

        params=params,

        headers=HEADERS,

        timeout=30

    )

    response.raise_for_status()

    data = response.json()

    pmids = data["esearchresult"]["idlist"]

    if not pmids:

        print("No publications found.")

        return []

    print(f"Found {len(pmids)} publications.")

    # Retrieve publication details

    papers = fetch_papers(pmids, topic)

    return papers


# =====================================
# FETCH PUBLICATION DETAILS
# =====================================

def fetch_papers(pmids, topic):

    print("Retrieving publication details...")

    fetch_url = BASE_URL + "efetch.fcgi"

    params = {

        "db": "pubmed",

        "id": ",".join(pmids),

        "retmode": "xml"

    }

    response = requests.get(

        fetch_url,

        params=params,

        headers=HEADERS,

        timeout=30

    )

    response.raise_for_status()

    root = ET.fromstring(response.content)

    papers = []

    # Extract each scientific publication

    for article in root.findall(".//PubmedArticle"):

        pmid = article.findtext(
            ".//PMID",
            default="Unknown"
        )

        # Extract title

        title_element = article.find(
            ".//ArticleTitle"
        )

        title = (

            "".join(title_element.itertext())

            if title_element is not None

            else "No title"

        )

        # Extract abstract

        abstract_elements = article.findall(
            ".//Abstract/AbstractText"
        )

        abstract_parts = []

        for element in abstract_elements:

            text = "".join(element.itertext())

            label = element.get("Label")

            if label:
                text = f"{label}: {text}"

            abstract_parts.append(text)

        abstract = " ".join(abstract_parts)

        # Construct publication record

        paper = {

            "pmid": pmid,

            "title": title,

            "abstract": abstract,

            "topic": topic

        }

        papers.append(paper)

    print(f"Successfully retrieved {len(papers)} records.")

    return papers

