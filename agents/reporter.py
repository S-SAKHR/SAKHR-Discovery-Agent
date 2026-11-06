from datetime import datetime, timezone
from typing import Dict, Any, List

def generate_daily_report(
    topic: str,
    papers: List[Dict[str, Any]],
    analyses: List[Dict[str, Any]],
    comparison: Dict[str, Any],
    gaps: Dict[str, Any],
    trends: Dict[str, Any]
) -> str:
    """
    Generates a comprehensive Markdown scientific intelligence report.
    """
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    report_lines = [
        f"# 🔬 SAKHR SCIENTIFIC INTELLIGENCE REPORT",
        f"**Date:** {now_utc}",
        f"**Research Topic:** {topic}",
        f"---",
        f"",
        f"## 📊 1. Knowledge Base & Trend Metrics",
        f"- **Total Publications Monitored:** {trends.get('total_papers', len(papers))}",
        f"- **Source Distribution:** {trends.get('source_distribution', {})}",
        f"- **Preprint Breakdown:** {trends.get('preprint_breakdown', {})}",
        f"",
        f"## 🧠 2. Cross-Publication Synthesis & Comparison",
        f"**Synthesis Summary:** {comparison.get('synthesis_summary', 'No summary available.')}",
        f"",
        f"**Key Agreements:**",
    ]

    for agree in comparison.get("agreements", []):
        report_lines.append(f"- {agree}")

    report_lines.extend([
        f"",
        f"**Contradictions / Disagreements:**",
    ])
    for contra in comparison.get("contradictions", []):
        report_lines.append(f"- {contra}")

    report_lines.extend([
        f"",
        f"**Methodological Differences:** {comparison.get('methodological_differences', 'N/A')}",
        f"**Evidence Quality:** {comparison.get('evidence_quality', 'N/A')}",
        f"",
        f"## 💡 3. Emerging Research Gaps & Hypotheses",
    ])

    for gap in gaps.get("research_gaps", []):
        report_lines.extend([
            f"### 🚀 Hypothesis: {gap.get('hypothesis_title')}",
            f"- **Research Question:** {gap.get('research_question')}",
            f"- **Existing Evidence:** {gap.get('existing_evidence')}",
            f"- **Missing Evidence:** {gap.get('missing_evidence')}",
            f"- **Why It Matters:** {gap.get('why_it_matters')}",
            f"- **Proposed Methodology:** {gap.get('possible_methodology')}",
            f"- **Confidence Level:** {gap.get('confidence_level')}",
            f""
        ])

    report_lines.extend([
        f"## 📚 4. Top Discovered Publications & Sources",
    ])

    for idx, paper in enumerate(papers[:5], start=1):
        title = paper.get("title", "No title")
        url = paper.get("url") or "#"
        sources = [s.get("source") for s in paper.get("sources_list", [{"source": paper.get("source", "db")}])]
        report_lines.append(f"{idx}. [{title}]({url}) *(Sources: {sources})*")

    report_lines.extend([
        f"",
        f"---",
        f"*Generated autonomously by SAKHR Discovery Agent.*"
    ])

    return "\n".join(report_lines)
