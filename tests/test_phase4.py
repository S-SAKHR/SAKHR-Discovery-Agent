import unittest
from unittest.mock import patch
from agents.reporter import generate_daily_report
from agents.telegram_agent import send_telegram_message

class TestPhase4Reporting(unittest.TestCase):

    def test_generate_daily_report(self):
        topic = "Quantum computing"
        papers = [{"title": "Quantum Paper", "url": "https://doi.org/10.1000/xyz", "sources_list": [{"source": "arxiv"}]}]
        comparison = {"synthesis_summary": "Good summary", "agreements": ["Agree"], "contradictions": ["Contra"], "methodological_differences": "Diff", "evidence_quality": "High", "unresolved_questions": ["Q1"]}
        gaps = {"research_gaps": [{"hypothesis_title": "Hyp", "research_question": "Q?", "existing_evidence": "Ev", "missing_evidence": "Miss", "why_it_matters": "Matters", "possible_methodology": "Method", "confidence_level": "Medium"}]}
        trends = {"total_papers": 10, "source_distribution": {"arxiv": 5}, "preprint_breakdown": {"True": 5}}

        report = generate_daily_report(topic, papers, [], comparison, gaps, trends)
        self.assertIn("Quantum computing", report)
        self.assertIn("SAKHR SCIENTIFIC INTELLIGENCE REPORT", report)
        self.assertIn("Good summary", report)

    @patch("agents.telegram_agent.requests.post")
    def test_send_telegram_message_missing_creds(self, mock_post):
        res = send_telegram_message("Test", chat_id="", token="")
        self.assertFalse(res)
        mock_post.assert_not_called()

    @patch("agents.telegram_agent.requests.post")
    def test_send_telegram_message_success(self, mock_post):
        mock_post.return_value.status_code = 200
        res = send_telegram_message("Test message", chat_id="12345", token="fake_token")
        self.assertTrue(res)
        mock_post.assert_called_once()

if __name__ == "__main__":
    unittest.main()
