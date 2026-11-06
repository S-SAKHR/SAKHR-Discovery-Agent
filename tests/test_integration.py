from agents.orchestrator import ResearchOrchestrator

queries = [
    ("BIOLOGY", "CRISPR gene editing"),
    ("ARTIFICIAL INTELLIGENCE", "Transformer neural networks"),
    ("PHYSICS", "Quantum computing"),
    ("ASTRONOMY", "Black hole observations"),
    ("NEUROSCIENCE", "Brain-computer interfaces")
]

orchestrator = ResearchOrchestrator()

print("=" * 60)
print("       SAKHR DISCOVERY AGENT — PHASE 2 MULTI-SOURCE INTEGRATION TEST")
print("=" * 60)

for domain, query in queries:
    print(f"\n[TEST] Testing Domain: {domain} | Query: '{query}'")
    try:
        papers = orchestrator.search(query, max_results_per_source=2)
        print(f"Retrieved & Deduplicated Unique Publications: {len(papers)}")
        for i, p in enumerate(papers, start=1):
            sources = [s.get("source") for s in p.get("sources_list", [])]
            print(f"  {i}. Sources: {sources} | Title: {p.get('title')[:80]}...")
    except Exception as e:
        print(f"Error searching {query}: {e}")

print("\n" + "=" * 60)
print("       PHASE 2 INTEGRATION TEST COMPLETED")
print("=" * 60)
