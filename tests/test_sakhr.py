import unittest
from unittest.mock import patch, MagicMock
from agents.researcher.base import BaseCollector
from agents.deduplication import deduplicate_papers, normalize_title
from agents.orchestrator import ResearchOrchestrator

class DummyCollector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "dummy"
    def search(self, topic: str, max_results: int = 5):
        return [self.normalize_record(source_id="123", title="Test Paper", abstract="Test abstract.")]

class TestSakhrFoundation(unittest.TestCase):

    def test_normalize_title(self):
        self.assertEqual(normalize_title("  Artificial Intelligence: A Modern Approach! "), "artificial intelligence a modern approach")
        self.assertEqual(normalize_title(""), "")

    def test_base_collector_normalization(self):
        collector = DummyCollector()
        record = collector.normalize_record(
            source_id="999",
            title="Quantum Computing",
            abstract="Qubits and superposition.",
            doi="10.1000/xyz",
            pmid="12345"
        )
        self.assertEqual(record["source"], "dummy")
        self.assertEqual(record["doi"], "10.1000/xyz")
        self.assertEqual(record["pmid"], "12345")
        self.assertEqual(record["title"], "Quantum Computing")
        self.assertIn("paper_id", record)

    def test_deduplication_exact_doi(self):
        papers = [
            {
                "paper_id": "id-1",
                "source": "pubmed",
                "source_id": "111",
                "doi": "10.1038/s41586-021-00000-x",
                "title": "AlphaFold Discovery",
                "abstract": "Short abstract",
                "authors": ["Author A"]
            },
            {
                "paper_id": "id-2",
                "source": "openalex",
                "source_id": "W123",
                "doi": "10.1038/s41586-021-00000-x",
                "title": "AlphaFold Discovery",
                "abstract": "Much longer and detailed abstract about protein folding and structural biology.",
                "authors": ["Author A", "Author B"]
            }
        ]
        unique = deduplicate_papers(papers)
        self.assertEqual(len(unique), 1)
        self.assertEqual(unique[0]["doi"], "10.1038/s41586-021-00000-x")
        self.assertEqual(len(unique[0]["authors"]), 2)
        self.assertIn("protein folding", unique[0]["abstract"])
        self.assertEqual(len(unique[0]["sources_list"]), 2)

    def test_orchestrator_routing(self):
        orchestrator = ResearchOrchestrator()
        
        # Test AI / Physics query routing
        sources_ai = orchestrator.route_query("Transformer neural networks")
        source_names_ai = [s.source_name for s in sources_ai]
        self.assertIn("openalex", source_names_ai)
        self.assertIn("arxiv", source_names_ai)

        # Test Biology query routing
        sources_bio = orchestrator.route_query("CRISPR gene editing")
        source_names_bio = [s.source_name for s in sources_bio]
        self.assertIn("openalex", source_names_bio)
        self.assertIn("pubmed", source_names_bio)


if __name__ == "__main__":
    unittest.main()
