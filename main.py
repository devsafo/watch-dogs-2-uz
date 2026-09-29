import os
import io
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

from database import init_db, seed_data_if_empty, get_stats, get_connection
from translator import manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database and verifying tables...")
    try:
        init_db()
        seed_path = os.path.join(os.path.dirname(__file__), "watch_dogs_2_uzbek_template.json")
        if os.path.exists(seed_path):
            seed_data_if_empty(seed_path)
    except Exception as e:
        logger.error(f"Error during startup DB setup: {e}")
    yield
    # Shutdown
    await manager.stop()

app = FastAPI(title="Watch Dogs 2 Uzbek Translator", lifespan=lifespan)

os.makedirs("templates", exist_ok=True)
templates = Jinja2Templates(directory="templates")

class StartRequest(BaseModel):
    mode: str = "test" # "test" or "full"
    limit: int = 50

class SettingsRequest(BaseModel):
    deepseek_api_key: Optional[str] = None
    deepseek_api_keys: Optional[str] = None
    deepseek_model: Optional[str] = None
    deepseek_base_url: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/stats")
async def api_stats():
    stats = get_stats()
    stats["is_running"] = manager.is_running
    stats["mode"] = manager.mode
    stats["session_count"] = manager.translated_in_session
    return stats

@app.get("/api/logs")
async def api_logs():
    return {"logs": manager.logs}

@app.get("/api/translations")
async def api_translations(status: Optional[str] = None, limit: int = 50, offset: int = 0):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if status:
                cur.execute("""
                    SELECT id, category, ru, uz, status, worker_id, updated_at 
                    FROM translations 
                    WHERE status = %s 
                    ORDER BY id ASC 
                    LIMIT %s OFFSET %s;
                """, (status, limit, offset))
            else:
                cur.execute("""
                    SELECT id, category, ru, uz, status, worker_id, updated_at 
                    FROM translations 
                    ORDER BY id ASC 
                    LIMIT %s OFFSET %s;
                """, (limit, offset))
            
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "category": r[1],
                    "ru": r[2],
                    "uz": r[3],
                    "status": r[4],
                    "worker_id": r[5],
                    "updated_at": r[6].isoformat() if r[6] else None
                }
                for r in rows
            ]

@app.post("/api/start")
async def api_start(req: StartRequest):
    await manager.start(mode=req.mode, limit=req.limit)
    return {"status": "started", "mode": req.mode, "limit": req.limit}

@app.post("/api/stop")
async def api_stop():
    await manager.stop()
    return {"status": "stopped"}

@app.post("/api/settings")
async def api_settings(req: SettingsRequest):
    if req.deepseek_api_key:
        os.environ["DEEPSEEK_API_KEY"] = req.deepseek_api_key.strip()
    if req.deepseek_api_keys:
        os.environ["DEEPSEEK_API_KEYS"] = req.deepseek_api_keys.strip()
    if req.deepseek_model:
        os.environ["DEEPSEEK_MODEL"] = req.deepseek_model.strip()
    if req.deepseek_base_url:
        os.environ["DEEPSEEK_BASE_URL"] = req.deepseek_base_url.strip()
    return {"status": "saved"}

@app.get("/api/export/json")
async def export_json():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, category, ru, uz FROM translations ORDER BY id ASC;")
            rows = cur.fetchall()
            data = [
                {"id": r[0], "category": r[1], "ru": r[2], "uz": r[3] or ""}
                for r in rows
            ]
    content = json.dumps(data, ensure_ascii=False, indent=2)
    return StreamingResponse(
        io.BytesIO(content.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=watch_dogs_2_uzbek_translated.json"}
    )

@app.get("/api/export/loc")
async def export_loc():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, ru, uz FROM translations ORDER BY id ASC;")
            rows = cur.fetchall()
            lines = []
            for r in rows:
                val = r[2] if (r[2] and r[2].strip()) else r[1]
                lines.append(f"{r[0]}={val}\r\n")
            text = "".join(lines)
    return StreamingResponse(
        io.BytesIO(text.encode('utf-16')),
        media_type="text/plain; charset=utf-16le",
        headers={"Content-Disposition": "attachment; filename=main_uzbek.loc.txt"}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
