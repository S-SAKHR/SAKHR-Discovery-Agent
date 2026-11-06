from agents.researcher import search_pubmed

from agents.analyzer import analyze_collection


print("\nSearching scientific literature...")

papers = search_pubmed(
    "Alzheimer disease sleep",
    max_results=2
)

print("\nStarting Gemini analysis...")

analyses = analyze_collection(papers)


for analysis in analyses:

    print("\n" + "=" * 60)

    for key, value in analysis.items():

        print(f"\n{key.upper()}:")

        print(value)
