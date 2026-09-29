"""
download_translations.py
Neon PostgreSQL bazasidagi barcha tarjima qilingan matnlarni tortib olib,
D:\Watch Dogs 2 - UZ papkasiga JSON va .loc.txt formatida saqlaydi.

Foydalanish:
  python scripts/download_translations.py
"""

import os
import sys
import json
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_v7Je1qwbIzFm@ep-restless-voice-b4unp9mj-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"
)

def download():
    print("Neon PostgreSQL bazasiga ulanmoqda...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, category, ru, uz, status 
        FROM translations 
        ORDER BY id ASC;
    """)
    rows = cur.fetchall()
    conn.close()

    total = len(rows)
    completed = sum(1 for r in rows if r[3] and r[3].strip())
    print(f"Jami matnlar: {total} ta, shundan tarjima qilingani: {completed} ta ({round(completed/total*100, 2)}%)")

    # 1. JSON formatida saqlash
    json_list = []
    loc_lines = []
    
    for r in rows:
        _id, _cat, _ru, _uz, _status = r
        val_uz = _uz if (_uz and _uz.strip()) else ""
        json_list.append({
            "id": _id,
            "category": _cat,
            "ru": _ru,
            "uz": val_uz,
            "status": _status
        })

        # O'yinga mos matn (agar o'zbekchasi bo'lsa o'zbekcha, bo'lmasa ruscha fallback)
        game_val = val_uz if val_uz else _ru
        loc_lines.append(f"{_id}={game_val}\r\n")

    json_path = os.path.join(BASE_DIR, "watch_dogs_2_uzbek_translated.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_list, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON fayl saqlandi: {json_path}")

    loc_path = os.path.join(BASE_DIR, "main_uzbek.loc.txt")
    with open(loc_path, 'w', encoding='utf-16') as f:
        f.writelines(loc_lines)
    print(f"✅ O'yin uchun matn fayli saqlandi: {loc_path}")

if __name__ == '__main__':
    download()
