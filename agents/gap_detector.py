import json
from typing import List, Dict, Any
from agents.llm_manager import llm_manager

GAP_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "research_gaps": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "hypothesis_title": {"type": "STRING"},
                    "research_question": {"type": "STRING"},
                    "existing_evidence": {"type": "STRING"},
                    "missing_evidence": {"type": "STRING"},
                    "why_it_matters": {"type": "STRING"},
                    "possible_methodology": {"type": "STRING"},
                    "confidence_level": {"type": "STRING"}
                },
                "required": [
                    "hypothesis_title",
                    "research_question",
                    "existing_evidence",
                    "missing_evidence",
                    "why_it_matters",
                    "possible_methodology",
                    "confidence_level"
                ]
            }
        }
    },
    "required": ["research_gaps"]
}

def detect_research_gaps(papers_with_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Examines accumulated literature and analyses to propose high-value research gaps and hypotheses.
    """
    if not papers_with_analyses:
        return {"research_gaps": []}

    context_blocks = []
    for idx, item in enumerate(papers_with_analyses, start=1):
        title = item.get("title", "No title")
        analysis = item.get("analysis", {})
        
        block = f"""
        [STUDY {idx}]
        TITLE: {title}
        FINDINGS: {analysis.get('main_findings', 'N/A')}
        LIMITATIONS: {analysis.get('limitations', 'N/A')}
        UNCERTAINTIES: {analysis.get('uncertainties', 'N/A')}
        """
        context_blocks.append(block)

    literature_text = "\n".join(context_blocks)

    prompt = f"""
    You are an expert Scientific Research Strategist and Gap Detector.
    Analyze the following scientific literature base and identify unexplored research gaps and novel hypotheses.

    {literature_text}

    Propose 2-3 high-value research gaps.
    RULES:
    - Classify every proposed gap as a hypothesis, NOT a confirmed scientific discovery.
    - Explicitly detail what evidence exists and what is missing.
    - Avoid treating an absence of retrieved papers as proof that no research exists.
    """

    result = llm_manager.generate_analysis(prompt, schema=GAP_SCHEMA)
    if "error" in result:
        return {"research_gaps": [], "error": result["error"]}
    return json.loads(result["content"])
