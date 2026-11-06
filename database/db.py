import psycopg
from psycopg.types.json import Jsonb
import uuid
from config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    GEMINI_MODEL
)


def get_connection():
    # Prioritize cloud connection string (Neon/Supabase)
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return psycopg.connect(db_url)
    
    # Fallback to individual parameters (Local/Legacy)
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


# =================================
# DATABASE STRUCTURE & MIGRATIONS
# =================================

def create_table():
    """
    Creates the unified multidisciplinary database schema safely,
    preserving existing tables and records and handling legacy constraints.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. Sources table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    name TEXT PRIMARY KEY,
                    description TEXT,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Seed default sources
            for src in ["pubmed", "arxiv", "openalex", "semantic_scholar", "crossref", "europe_pmc", "nasa_ads"]:
                cur.execute("""
                    INSERT INTO sources (name) VALUES (%s)
                    ON CONFLICT (name) DO NOTHING;
                """, (src,))

            # 2. Papers table (Multidisciplinary unified schema)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    paper_id UUID,
                    pmid TEXT,
                    doi TEXT,
                    arxiv_id TEXT,
                    openalex_id TEXT,
                    title TEXT NOT NULL,
                    abstract TEXT,
                    authors JSONB,
                    published_date DATE,
                    url TEXT,
                    topic TEXT,
                    is_preprint BOOLEAN DEFAULT FALSE,
                    fetched_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Add columns if migrating from legacy schema
            cur.execute("""
                ALTER TABLE papers ADD COLUMN IF NOT EXISTS paper_id UUID;
                ALTER TABLE papers ADD COLUMN IF NOT EXISTS doi TEXT;
                ALTER TABLE papers ADD COLUMN IF NOT EXISTS arxiv_id TEXT;
                ALTER TABLE papers ADD COLUMN IF NOT EXISTS openalex_id TEXT;
                ALTER TABLE papers ADD COLUMN IF NOT EXISTS authors JSONB;
                ALTER TABLE papers ADD COLUMN IF NOT EXISTS published_date DATE;
                ALTER TABLE papers ADD COLUMN IF NOT EXISTS url TEXT;
                ALTER TABLE papers ADD COLUMN IF NOT EXISTS is_preprint BOOLEAN DEFAULT FALSE;
            """)

            # Populate paper_id for legacy rows missing it
            cur.execute("""
                UPDATE papers SET paper_id = gen_random_uuid() WHERE paper_id IS NULL;
            """)

            # Ensure paper_id has a UNIQUE or PRIMARY KEY constraint so foreign keys can reference it
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                        WHERE tc.table_name = 'papers' AND kcu.column_name = 'paper_id' AND tc.constraint_type IN ('PRIMARY KEY', 'UNIQUE')
                    ) THEN
                        ALTER TABLE papers ADD CONSTRAINT papers_paper_id_key UNIQUE (paper_id);
                    END IF;
                END $$;
            """)

            # 3. Paper Sources (Tracking multi-source provenance)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS paper_sources (
                    id SERIAL PRIMARY KEY,
                    paper_id UUID REFERENCES papers(paper_id) ON DELETE CASCADE,
                    source_name TEXT REFERENCES sources(name),
                    source_id TEXT,
                    UNIQUE(paper_id, source_name)
                );
            """)

            # 4. Topics and Paper Topics
            cur.execute("""
                CREATE TABLE IF NOT EXISTS topics (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS paper_topics (
                    paper_id UUID REFERENCES papers(paper_id) ON DELETE CASCADE,
                    topic_name TEXT,
                    PRIMARY KEY (paper_id, topic_name)
                );
            """)

            # 5. Analyses table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    paper_id UUID REFERENCES papers(paper_id) ON DELETE CASCADE,
                    pmid TEXT,
                    analysis JSONB NOT NULL,
                    model TEXT,
                    analyzed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (paper_id)
                );
            """)

            # Indexes for performance
            cur.execute("CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_papers_pmid ON papers(pmid);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_papers_arxiv ON papers(arxiv_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_papers_topic ON papers(topic);")

    print("Unified multidisciplinary database schema is ready.")


# =================================
# SAVE PUBLICATIONS (MULTIDISCIPLINARY)
# =================================

def save_papers(papers, topic: str = None):
    if not papers:
        return

    with get_connection() as conn:
        with conn.cursor() as cur:
            for paper in papers:
                paper_id = paper.get("paper_id")
                if not paper_id:
                    paper_id = str(uuid.uuid4())
                else:
                    try:
                        uuid.UUID(str(paper_id))
                    except ValueError:
                        paper_id = str(uuid.uuid4())

                pmid = paper.get("pmid")
                doi = paper.get("doi")
                arxiv_id = paper.get("arxiv_id")
                openalex_id = paper.get("openalex_id")
                title = paper.get("title", "No title")
                abstract = paper.get("abstract", "")
                authors = Jsonb(paper.get("authors", []))
                published_date = paper.get("published_date")
                url = paper.get("url")
                is_preprint = paper.get("is_preprint", False)
                paper_topic = topic or paper.get("topic")

                # Check if paper already exists by doi, pmid, arxiv_id, or openalex_id
                existing_paper_id = None
                if pmid:
                    cur.execute("SELECT paper_id FROM papers WHERE pmid = %s;", (pmid,))
                    row = cur.fetchone()
                    if row: existing_paper_id = row[0]
                if not existing_paper_id and doi:
                    cur.execute("SELECT paper_id FROM papers WHERE doi = %s;", (doi,))
                    row = cur.fetchone()
                    if row: existing_paper_id = row[0]
                if not existing_paper_id and arxiv_id:
                    cur.execute("SELECT paper_id FROM papers WHERE arxiv_id = %s;", (arxiv_id,))
                    row = cur.fetchone()
                    if row: existing_paper_id = row[0]

                if existing_paper_id:
                    actual_paper_id = existing_paper_id
                    cur.execute("""
                        UPDATE papers SET
                            title = %s,
                            abstract = %s,
                            authors = %s,
                            published_date = COALESCE(%s, published_date),
                            url = COALESCE(%s, url),
                            topic = COALESCE(%s, topic),
                            doi = COALESCE(%s, doi),
                            pmid = COALESCE(%s, pmid),
                            arxiv_id = COALESCE(%s, arxiv_id),
                            openalex_id = COALESCE(%s, openalex_id)
                        WHERE paper_id = %s;
                    """, (
                        title, abstract, authors, published_date, url, paper_topic,
                        doi, pmid, arxiv_id, openalex_id, actual_paper_id
                    ))
                else:
                    actual_paper_id = paper_id
                    cur.execute("""
                        INSERT INTO papers
                        (paper_id, pmid, doi, arxiv_id, openalex_id, title, abstract, authors, published_date, url, topic, is_preprint)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """, (
                        actual_paper_id, pmid, doi, arxiv_id, openalex_id, title, abstract,
                        authors, published_date, url, paper_topic, is_preprint
                    ))

                # Save sources (support both single source and sources_list)
                sources_list = paper.get("sources_list")
                if not sources_list:
                    sources_list = [{"source": paper.get("source"), "source_id": paper.get("source_id")}]

                for src_entry in sources_list:
                    s_name = src_entry.get("source")
                    s_id = src_entry.get("source_id")
                    if s_name:
                        cur.execute("""
                            INSERT INTO paper_sources (paper_id, source_name, source_id)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (paper_id, source_name) DO UPDATE SET source_id = EXCLUDED.source_id;
                        """, (actual_paper_id, s_name, s_id))

                # Save topic mapping
                if paper_topic:
                    cur.execute("""
                        INSERT INTO topics (name) VALUES (%s)
                        ON CONFLICT (name) DO NOTHING;
                    """, (paper_topic,))
                    cur.execute("""
                        INSERT INTO paper_topics (paper_id, topic_name)
                        VALUES (%s, %s)
                        ON CONFLICT (paper_id, topic_name) DO NOTHING;
                    """, (actual_paper_id, paper_topic))

    print(f"Saved/updated {len(papers)} publications in PostgreSQL knowledge base.")


# =================================
# GET PUBLICATIONS
# =================================

def get_papers(limit: int = 50, topic: str = None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if topic:
                cur.execute("""
                    SELECT paper_id, pmid, doi, arxiv_id, openalex_id, title, abstract, topic, fetched_at
                    FROM papers
                    WHERE topic = %s
                    ORDER BY fetched_at DESC
                    LIMIT %s;
                """, (topic, limit))
            else:
                cur.execute("""
                    SELECT paper_id, pmid, doi, arxiv_id, openalex_id, title, abstract, topic, fetched_at
                    FROM papers
                    ORDER BY fetched_at DESC
                    LIMIT %s;
                """, (limit,))

            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


# =================================
# FIND UNANALYZED PUBLICATIONS
# =================================

def get_unanalyzed_papers(topic: str = None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if topic:
                cur.execute("""
                    SELECT p.paper_id, p.pmid, p.title, p.abstract, p.topic
                    FROM papers p
                    LEFT JOIN analyses a ON p.paper_id = a.paper_id
                    WHERE a.paper_id IS NULL AND p.topic = %s;
                """, (topic,))
            else:
                cur.execute("""
                    SELECT p.paper_id, p.pmid, p.title, p.abstract, p.topic
                    FROM papers p
                    LEFT JOIN analyses a ON p.paper_id = a.paper_id
                    WHERE a.paper_id IS NULL;
                """)

            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


# =================================
# SAVE AI ANALYSES
# =================================

def save_analyses(analyses):
    if not analyses:
        return

    with get_connection() as conn:
        with conn.cursor() as cur:
            for analysis in analyses:
                if "error" in analysis:
                    continue

                paper_id = analysis.get("paper_id")
                pmid = analysis.get("pmid")

                # If paper_id not provided, look up by pmid or title
                if not paper_id and pmid:
                    cur.execute("SELECT paper_id FROM papers WHERE pmid = %s;", (pmid,))
                    row = cur.fetchone()
                    if row:
                        paper_id = row[0]

                if not paper_id:
                    continue

                cur.execute("""
                    INSERT INTO analyses (paper_id, pmid, analysis, model)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (paper_id) DO UPDATE SET
                        analysis = EXCLUDED.analysis,
                        model = EXCLUDED.model,
                        analyzed_at = CURRENT_TIMESTAMP;
                """, (
                    paper_id,
                    pmid,
                    Jsonb(analysis),
                    GEMINI_MODEL
                ))

    print(f"Saved {len(analyses)} AI analyses in PostgreSQL.")


# =================================
# DATABASE STATISTICS
# =================================

def get_statistics():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM papers;")
            papers = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM analyses;")
            analyses = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM sources;")
            sources = cur.fetchone()[0]

    return {
        "papers": papers,
        "analyses": analyses,
        "sources": sources
    }
