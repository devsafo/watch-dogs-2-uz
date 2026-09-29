import os
import json
import logging
import psycopg2
from psycopg2.extras import execute_values

logger = logging.getLogger("db")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_v7Je1qwbIzFm@ep-restless-voice-b4unp9mj-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"
)

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Jadvallarni yaratish va indekslarni sozlash"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY,
                    category VARCHAR(64) NOT NULL,
                    ru TEXT NOT NULL,
                    uz TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    worker_id INTEGER,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_translations_status ON translations(status);
                CREATE INDEX IF NOT EXISTS idx_translations_category ON translations(category);
                
                CREATE TABLE IF NOT EXISTS settings (
                    key VARCHAR(64) PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
            conn.commit()
    logger.info("Database initialized successfully.")

def seed_data_if_empty(json_path):
    """Agar jadval bo'sh bo'lsa, JSON fayldan 48,142 ta qatorni bazaga yuklash"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM translations;")
            count = cur.fetchone()[0]
            if count > 0:
                logger.info(f"Database already has {count} rows. Seeding skipped.")
                return count

    if not os.path.exists(json_path):
        logger.error(f"Seed file not found: {json_path}")
        return 0

    logger.info(f"Loading seed data from {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        items = json.load(f)

    rows = []
    for item in items:
        rows.append((
            item["id"],
            item["category"],
            item["ru"],
            item.get("uz") or None,
            "completed" if item.get("uz") else "pending"
        ))

    with get_connection() as conn:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO translations (id, category, ru, uz, status)
                VALUES %s
                ON CONFLICT (id) DO NOTHING;
                """,
                rows,
                page_size=2000
            )
            conn.commit()
    logger.info(f"Successfully seeded {len(rows)} rows into Neon PostgreSQL!")
    return len(rows)

def get_stats():
    """Umumiy statistika va toifalar bo'yicha ko'rsatkichlar"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'pending') as pending,
                    COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed
                FROM translations;
            """)
            row = cur.fetchone()
            stats = {
                "total": row[0],
                "completed": row[1],
                "pending": row[2],
                "in_progress": row[3],
                "failed": row[4],
                "progress_percent": round((row[1] / row[0] * 100), 2) if row[0] > 0 else 0
            }

            cur.execute("""
                SELECT category, 
                       COUNT(*) as total,
                       COUNT(*) FILTER (WHERE status = 'completed') as completed
                FROM translations
                GROUP BY category
                ORDER BY total DESC;
            """)
            stats["categories"] = [
                {
                    "category": r[0],
                    "total": r[1],
                    "completed": r[2],
                    "percent": round((r[2] / r[1] * 100), 1) if r[1] > 0 else 0
                }
                for r in cur.fetchall()
            ]
            return stats
