from agents.researcher import search_pubmed


papers = search_pubmed(
    "Alzheimer disease sleep",
    max_results=5
)


for paper in papers:

    print("\n" + "=" * 60)

    print("PMID:", paper["pmid"])

    print("TITLE:", paper["title"])

    print("ABSTRACT:")

    print(paper["abstract"][:500])

