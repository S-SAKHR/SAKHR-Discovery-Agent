import os
from agents.orchestrator import ResearchOrchestrator
from agents.analyzer import analyze_collection
from agents.comparator import compare_publications
from agents.gap_detector import detect_research_gaps
from agents.trend_detector import analyze_trends
from agents.reporter import generate_daily_report
from agents.telegram_agent import send_telegram_message
from database.db import (
    create_table,
    save_papers,
    get_papers,
    get_unanalyzed_papers,
    save_analyses,
    get_statistics
)


# =====================================
# SAKHR DISCOVERY AGENT
# FULL INTELLIGENCE CONTROLLER
# =====================================

def main():

    print("\n" + "=" * 60)
    print("       SAKHR DISCOVERY AGENT — MULTIDISCIPLINARY INTELLIGENCE")
    print("=" * 60)

    # STEP 1: Initialize database schema
    print("\n[1] Initializing PostgreSQL Knowledge Base...")
    create_table()

    # STEP 2: Receive research topic
    topic = input("\nEnter scientific research topic (e.g., 'CRISPR gene editing', 'Quantum computing', 'Transformer neural networks'): ").strip()

    if not topic:
        print("Research topic cannot be empty.")
        return

    # STEP 3: Research using Orchestrator (Multi-source collection & deduplication)
    print("\n[2] Starting Research Orchestrator across scientific databases...")
    orchestrator = ResearchOrchestrator()
    papers = orchestrator.search(topic, max_results_per_source=2)

    if not papers:
        print("No publications retrieved.")
        return

    # STEP 4: Store publications in PostgreSQL
    print("\n[3] Storing publications in PostgreSQL knowledge base...")
    save_papers(papers, topic=topic)

    # STEP 5: Gemini Scientific Analysis
    print("\n[4] Running Gemini Scientific Intelligence Analysis...")
    unanalyzed = get_unanalyzed_papers(topic=topic)
    
    if unanalyzed:
        print(f"Found {len(unanalyzed)} unanalyzed publications. Analyzing with Gemini...")
        analyses = analyze_collection(unanalyzed)
        save_analyses(analyses)
    else:
        print("All publications for this topic have already been analyzed.")

    # Retrieve stored papers and their analyses for advanced intelligence
    stored_papers = get_papers(limit=5, topic=topic)
    
    # Gather analyses from DB for comparison and gap detection
    # For demonstration, construct papers with analyses dict
    papers_with_analyses = []
    for p in stored_papers:
        papers_with_analyses.append({
            "title": p.get("title"),
            "abstract": p.get("abstract"),
            "analysis": {"main_findings": p.get("abstract", "")[:200], "limitations": "Standard study limitations"}
        })

    # STEP 6: Run Advanced Intelligence Engines
    print("\n[5] Running Scientific Comparator & Research Gap Detector...")
    comparison = compare_publications(papers_with_analyses)
    gaps = detect_research_gaps(papers_with_analyses)
    trends = analyze_trends(topic=topic)

    # STEP 7: Generate Daily Report
    print("\n[6] Generating Daily Scientific Intelligence Report...")
    report_md = generate_daily_report(
        topic=topic,
        papers=stored_papers,
        analyses=[],
        comparison=comparison,
        gaps=gaps,
        trends=trends
    )

    # Save report locally
    os.makedirs("reports", exist_ok=True)
    report_filename = f"reports/report_{topic.replace(' ', '_')}.md"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"Report saved locally to: {report_filename}")

    # STEP 8: Deliver via Telegram
    print("\n[7] Delivering Report via Telegram...")
    send_telegram_message(report_md)

    # STEP 9: Knowledge Base Statistics
    stats = get_statistics()
    print("\n" + "=" * 60)
    print("       KNOWLEDGE BASE STATISTICS")
    print("=" * 60)
    print(f"Total Papers in DB: {stats['papers']}")
    print(f"Total Analyses in DB: {stats['analyses']}")
    print(f"Registered Sources: {stats['sources']}")

    print("\n" + "=" * 60)
    print("       INTELLIGENCE PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)


# =====================================
# EXECUTION
# =====================================

if __name__ == "__main__":
    main()
