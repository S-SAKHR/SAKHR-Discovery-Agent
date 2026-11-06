from typing import List, Dict, Any
from database.db import get_connection

def analyze_trends(topic: str = None) -> Dict[str, Any]:
    """
    Analyzes accumulated research data in PostgreSQL using reproducible SQL queries
    to calculate publication volume, source distribution, and preprint ratios.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Total papers
            if topic:
                cur.execute("SELECT COUNT(*) FROM papers WHERE topic = %s;", (topic,))
            else:
                cur.execute("SELECT COUNT(*) FROM papers;")
            total_papers = cur.fetchone()[0]

            # Source distribution
            if topic:
                cur.execute("""
                    SELECT ps.source_name, COUNT(*) 
                    FROM paper_sources ps
                    JOIN papers p ON ps.paper_id = p.paper_id
                    WHERE p.topic = %s
                    GROUP BY ps.source_name;
                """, (topic,))
            else:
                cur.execute("""
                    SELECT source_name, COUNT(*) 
                    FROM paper_sources
                    GROUP BY source_name;
                """)
            source_distribution = {row[0]: row[1] for row in cur.fetchall()}

            # Preprint vs Published ratio
            if topic:
                cur.execute("""
                    SELECT is_preprint, COUNT(*) 
                    FROM papers 
                    WHERE topic = %s 
                    GROUP BY is_preprint;
                """, (topic,))
            else:
                cur.execute("""
                    SELECT is_preprint, COUNT(*) 
                    FROM papers 
                    GROUP BY is_preprint;
                """)
            preprint_counts = {str(row[0]): row[1] for row in cur.fetchall()}

    return {
        "topic": topic or "All Topics",
        "total_papers": total_papers,
        "source_distribution": source_distribution,
        "preprint_breakdown": preprint_counts
    }
