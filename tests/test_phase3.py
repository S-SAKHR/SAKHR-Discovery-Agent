import unittest
from unittest.mock import patch
from agents.comparator import compare_publications
from agents.gap_detector import detect_research_gaps
from agents.trend_detector import analyze_trends

class TestPhase3Intelligence(unittest.TestCase):

    @patch("agents.comparator.generate_content")
    def test_compare_publications(self, mock_gen):
        mock_gen.return_value = '{"synthesis_summary": "Summary", "agreements": ["Agree 1"], "contradictions": ["Contra 1"], "methodological_differences": "Diff", "evidence_quality": "High", "unresolved_questions": ["Q1"]}'
        
        papers = [
            {"title": "Paper 1", "abstract": "Abstract 1", "analysis": {"main_findings": "Finding 1"}},
            {"title": "Paper 2", "abstract": "Abstract 2", "analysis": {"main_findings": "Finding 2"}}
        ]
        result = compare_publications(papers)
        self.assertIn("synthesis_summary", result)
        self.assertEqual(result["evidence_quality"], "High")

    @patch("agents.gap_detector.generate_content")
    def test_detect_research_gaps(self, mock_gen):
        mock_gen.return_value = '{"research_gaps": [{"hypothesis_title": "Hyp 1", "research_question": "Q?", "existing_evidence": "Ev", "missing_evidence": "Miss", "why_it_matters": "Matters", "possible_methodology": "Method", "confidence_level": "Medium"}]}'
        
        papers = [
            {"title": "Paper 1", "analysis": {"main_findings": "Finding 1"}}
        ]
        result = detect_research_gaps(papers)
        self.assertIn("research_gaps", result)
        self.assertEqual(len(result["research_gaps"]), 1)

if __name__ == "__main__":
    unittest.main()
