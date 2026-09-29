import os
import re
import json
import asyncio
import logging
import aiohttp
from datetime import datetime
import aiohttp
from database import get_connection, set_setting, get_setting

logger = logging.getLogger("translator")

# Configuration
DEFAULT_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
DEFAULT_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
SERVICE_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://watch-dogs-2-uz-translator.onrender.com").rstrip("/")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "dedsec2026")

# Keys can be specified as DEEPSEEK_API_KEYS="key1,key2,key3,key4,key5"
# or individual DEEPSEEK_API_KEY_1..5 or single DEEPSEEK_API_KEY
def get_worker_api_key(worker_id: int) -> str:
    # 1. Check DEEPSEEK_API_KEY_{worker_id}
    key = os.environ.get(f"DEEPSEEK_API_KEY_{worker_id}")
    if key:
        return key.strip()
    
    # 2. Check comma-separated DEEPSEEK_API_KEYS
    keys_str = os.environ.get("DEEPSEEK_API_KEYS", "")
    if keys_str:
        keys_list = [k.strip() for k in keys_str.split(",") if k.strip()]
        if keys_list:
            return keys_list[(worker_id - 1) % len(keys_list)]
            
    # 3. Check single DEEPSEEK_API_KEY
    single_key = os.environ.get("DEEPSEEK_API_KEY", "")
    return single_key.strip()

SYSTEM_PROMPT = """Sen "Watch Dogs 2" kompyuter o'yini bo'yicha professional lokalizator va tajribali o'zbek tili tarjimonsan.
Vazifang: Berilgan ruscha o'yin matnlarini o'zbek tiliga (Lotin alifbosi: o', g', sh, ch, tutuq belgisi ') tarjima qilish.

QAT'IY QOIDALAR:
1. Uslub: San-Fransisko xakerlari va DedSec guruhining jonli, zamonaviy, norasmiy va dinamik yoshlar nutqi.
2. Maxsus teglarni ASLO o'zgartirma va tushirib qoldirma:
   - [LF] (yangi qator), [CR]
   - {0}, {1}, %s, %d, %i (o'zgaruvchilar)
   - <font ...>, </font>, [KEY_...], [BUTTON_...]
   Bular o'zbekcha tarjimada aynan o'z o'rnida qolishi shart!
3. O'yin terminlari va ismlari:
   - Marcus Holloway -> Markus
   - Wrench -> Rench
   - Sitara -> Sitara
   - Horatio -> Goratsiy
   - Josh -> Josh
   - DedSec -> DedSec (o'zgartirilmasin)
   - ctOS -> ctOS (o'zgartirilmasin)
   - Blume -> Blume / Blyum
   - Nudle -> Nudle
   - Hack / Hacking -> Vzlom / Xakerlik / Buzib kirish
4. Javob formati: FAQAT quyidagi JSON formatida javob qaytar, hech qanday ortiqcha so'z va markdownsiz:
{"translations": [{"id": 12345, "uz": "Tarjima matni"}, ...]}"""

class TranslationManager:
    def __init__(self):
        self.is_running = False
        self.mode = "test" # "test" or "full"
        self.test_limit = 50
        self.translated_in_session = 0
        self.active_tasks = []
        self.logs = []
        self.batch_size = 20

    def add_log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {msg}"
        self.logs.append(log_entry)
        if len(self.logs) > 200:
            self.logs.pop(0)
        logger.info(msg)

    async def start(self, mode: str = "test", limit: int = 50):
        if self.is_running:
            self.add_log("Workerlar allaqachon ishlamoqda.")
            return

        self.is_running = True
        self.mode = mode
        self.test_limit = limit
        self.translated_in_session = 0
        set_setting("translation_state", "running")
        set_setting("translation_mode", mode)
        self.add_log(f"Tarjima boshlandi. Rejim: {mode.upper()}, Limit: {limit if mode == 'test' else 'Cheksiz'}")

        # Reset any stuck 'in_progress' rows back to 'pending'
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE translations SET status = 'pending' WHERE status = 'in_progress';")
                conn.commit()

        # Launch 5 workers
        self.active_tasks = []
        for worker_id in range(1, 6):
            task = asyncio.create_task(self._worker_loop(worker_id))
            self.active_tasks.append(task)

        # Launch keep-alive pinger task to prevent Render free-tier from idling
        self.active_tasks.append(asyncio.create_task(self._keep_alive_pinger()))

    async def stop(self, is_user_action: bool = True):
        self.is_running = False
        if is_user_action:
            set_setting("translation_state", "stopped")
        for task in self.active_tasks:
            task.cancel()
        self.active_tasks = []
        self.add_log("Barcha workerlar to'xtatildi.")

    async def _keep_alive_pinger(self):
        """Render Free serverini 15 daqiqalik uyquga ketishidan saqlash uchun 7 daqiqada bir self-ping"""
        ping_url = f"{SERVICE_EXTERNAL_URL}/api/stats"
        self.add_log(f"Keep-Alive tizimi faollashtirildi (Ping URL: {ping_url})")
        while self.is_running:
            try:
                await asyncio.sleep(420) # 7 daqiqa
                if not self.is_running:
                    break
                auth = aiohttp.BasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD)
                async with aiohttp.ClientSession(auth=auth) as session:
                    async with session.get(ping_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        logger.info(f"Keep-alive self-ping yuborildi: HTTP {resp.status}")
            except Exception as e:
                logger.warning(f"Keep-alive ping xatosi: {e}")

    async def _worker_loop(self, worker_id: int):
        self.add_log(f"Worker #{worker_id} ishga tushdi.")
        api_key = get_worker_api_key(worker_id)
        
        while self.is_running:
            # Check test mode limit
            if self.mode == "test" and self.translated_in_session >= self.test_limit:
                self.add_log(f"Worker #{worker_id}: Test limiti ({self.test_limit}) bajarildi!")
                self.is_running = False
                set_setting("translation_state", "stopped")
                break

            # Fetch batch of pending rows
            batch = self._fetch_batch(worker_id, self.batch_size)
            if not batch:
                # Check if all strings are completely translated
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COUNT(*) FROM translations WHERE status = 'pending';")
                        pending_count = cur.fetchone()[0]
                if pending_count == 0:
                    self.add_log(f"Worker #{worker_id}: Barcha matnlar 100% tarjima qilib bo'lindi!")
                    self.is_running = False
                    set_setting("translation_state", "finished")
                    break
                self.add_log(f"Worker #{worker_id}: Bajariladigan yangi matnlar kutilmoqda...")
                await asyncio.sleep(5)
                continue

            # Check API Key
            if not api_key:
                self.add_log(f"Worker #{worker_id} XATOLIK: DeepSeek API kaliti topilmadi! Sozlamalar bo'limidan kalitni kiriting.")
                self._revert_batch(batch)
                await asyncio.sleep(10)
                continue

            # Translate batch
            success, results = await self._call_deepseek(worker_id, api_key, batch)
            if success:
                self._save_results(worker_id, results)
                self.translated_in_session += len(results)
                self.add_log(f"Worker #{worker_id}: {len(results)} ta matn tarjima qilindi. Jami joriy sessiyada: {self.translated_in_session}")
            else:
                self.add_log(f"Worker #{worker_id}: Xatolik yuz berdi, 5 soniyadan so'ng qayta uriniladi.")
                await asyncio.sleep(5)

            await asyncio.sleep(0.5)

        self.add_log(f"Worker #{worker_id} faoliyatini yakunladi.")

    def _fetch_batch(self, worker_id: int, size: int):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, ru 
                    FROM translations 
                    WHERE status = 'pending' 
                    ORDER BY id ASC 
                    LIMIT %s 
                    FOR UPDATE SKIP LOCKED;
                """, (size,))
                rows = cur.fetchall()
                if not rows:
                    return []
                ids = [r[0] for r in rows]
                cur.execute("""
                    UPDATE translations 
                    SET status = 'in_progress', worker_id = %s, updated_at = NOW() 
                    WHERE id = ANY(%s);
                """, (worker_id, ids))
                conn.commit()
                return [{"id": r[0], "ru": r[1]} for r in rows]

    def _revert_batch(self, batch):
        ids = [item["id"] for item in batch]
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE translations SET status = 'pending' WHERE id = ANY(%s);", (ids,))
                conn.commit()

    async def _call_deepseek(self, worker_id: int, api_key: str, batch: list):
        url = f"{DEFAULT_BASE_URL}/chat/completions"
        user_content = json.dumps(batch, ensure_ascii=False)
        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Quyidagi matnlarni tarjima qil:\n{user_content}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.3
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        parsed = json.loads(content)
                        translations = parsed.get("translations", [])
                        return True, translations
                    elif resp.status == 429:
                        self.add_log(f"Worker #{worker_id}: Rate limit (429)! 10 soniya kutilmoqda...")
                        await asyncio.sleep(10)
                        return False, []
                    else:
                        err_text = await resp.text()
                        self.add_log(f"Worker #{worker_id} HTTP {resp.status}: {err_text[:200]}")
                        return False, []
        except Exception as e:
            self.add_log(f"Worker #{worker_id} istisno: {str(e)}")
            return False, []

    def _save_results(self, worker_id: int, results: list):
        if not results:
            return
        with get_connection() as conn:
            with conn.cursor() as cur:
                for item in results:
                    item_id = item.get("id")
                    uz_text = item.get("uz", "")
                    if item_id and uz_text:
                        cur.execute("""
                            UPDATE translations 
                            SET uz = %s, status = 'completed', worker_id = %s, updated_at = NOW() 
                            WHERE id = %s;
                        """, (uz_text, worker_id, item_id))
                conn.commit()

manager = TranslationManager()
