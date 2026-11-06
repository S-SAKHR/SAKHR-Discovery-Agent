import json
from typing import List, Dict, Any
from agents.llm_manager import llm_manager

COMPARISON_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "synthesis_summary": {
            "type": "STRING"
        },
        "agreements": {
            "type": "ARRAY",
            "items": {
                "type": "STRING"
            }
        },
        "contradictions": {
            "type": "ARRAY",
            "items": {
                "type": "STRING"
            }
        },
        "methodological_differences": {
            "type": "STRING"
        },
        "evidence_quality": {
            "type": "STRING"
        },
        "unresolved_questions": {
            "type": "ARRAY",
            "items": {
                "type": "STRING"
            }
        }
    },
    "required": [
        "synthesis_summary",
        "agreements",
        "contradictions",
        "methodological_differences",
        "evidence_quality",
        "unresolved_questions"
    ]
}

def compare_publications(papers_with_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compares several publications on the same research topic using Gemini.
    Identifies agreement, contradictions, methodological differences, and unresolved questions.
    """
    if not papers_with_analyses:
        return {"error": "No papers provided for comparison."}

    # Format papers for prompt
    context_blocks = []
    for idx, item in enumerate(papers_with_analyses, start=1):
        title = item.get("title", "No title")
        abstract = item.get("abstract", "No abstract")
        analysis = item.get("analysis", {})
        
        block = f"""
        [PUBLICATION {idx}]
        TITLE: {title}
        ABSTRACT: {abstract}
        MAIN FINDINGS: {analysis.get('main_findings', 'Not analyzed')}
        LIMITATIONS: {analysis.get('limitations', 'Not reported')}
        """
        context_blocks.append(block)

    publications_text = "\n".join(context_blocks)

    prompt = f"""
    You are an expert Chief Scientific Research Comparator.
    Analyze and compare the following scientific publications rigorously.

    {publications_text}

    Provide a structured comparison extracting:
    1. Synthesis summary: High-level overview of how these studies relate.
    2. Agreements: Where do findings align?
    3. Contradictions: Where do findings conflict or disagree?
    4. Methodological differences: How do study designs or methods differ?
    5. Evidence quality: Assess the overall strength of evidence across studies.
    6. Unresolved questions: What remains unanswered?

    RULES:
    - Reference publication indices when noting agreements or contradictions.
    - Do not manufacture scientific consensus if none exists.
    - Distinguish genuine contradictions from differences in study design or population.
    """

    result = llm_manager.generate_analysis(prompt, schema=COMPARISON_SCHEMA)
    if "error" in result:
        return {"error": result["error"]}
    return json.loads(result["content"])
