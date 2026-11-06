import json
from agents.llm_manager import llm_manager


ANALYSIS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "research_question": {
            "type": "STRING"
        },
        "methodology": {
            "type": "STRING"
        },
        "main_findings": {
            "type": "STRING"
        },
        "limitations": {
            "type": "STRING"
        },
        "evidence": {
            "type": "ARRAY",
            "items": {
                "type": "STRING"
            }
        },
        "uncertainties": {
            "type": "STRING"
        }
    },
    "required": [
        "research_question",
        "methodology",
        "main_findings",
        "limitations",
        "evidence",
        "uncertainties"
    ]
}


def analyze_paper(paper):

    abstract = paper["abstract"]

    if not abstract.strip():
        return {
            "pmid": paper["pmid"],
            "error": "No abstract available"
        }

    prompt = f"""
    You are an expert scientific research analyst.

    Analyze the following scientific publication.

    TITLE:
    {paper['title']}

    ABSTRACT:
    {abstract}

    Extract:

    1. Research question:
       What scientific problem is being investigated?

    2. Methodology:
       Identify the study design, population,
       sample size, methods and measurements
       when explicitly reported.

    3. Main findings:
       What did the researchers discover?

    4. Limitations:
       Identify limitations explicitly reported
       by the authors.

    5. Evidence:
       Extract statements from the abstract
       supporting the findings.

    6. Uncertainties:
       What cannot be concluded from this abstract?

    RULES:

    - Use only the supplied publication information.
    - Never invent missing information.
    - Distinguish association from causation.
    - Distinguish hypotheses from demonstrated findings.
    - Mark missing information as
      "Not reported in abstract."
    """

    result = llm_manager.generate_analysis(
        prompt,
        schema=ANALYSIS_SCHEMA
    )

    if "error" in result:
        return {
            "pmid": paper.get("pmid"),
            "paper_id": paper.get("paper_id"),
            "error": result["error"]
        }

    analysis = json.loads(result["content"])

    analysis["pmid"] = paper.get("pmid")
    analysis["paper_id"] = paper.get("paper_id")
    analysis["title"] = paper.get("title")
    analysis["provider"] = result.get("provider")
    analysis["model"] = result.get("model")

    return analysis


def analyze_collection(papers):

    results = []

    for number, paper in enumerate(papers, start=1):

        print(
            f"\nAnalyzing paper {number}/{len(papers)}"
        )

        analysis = analyze_paper(paper)

        results.append(analysis)

    return results
