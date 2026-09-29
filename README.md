# Watch Dogs 2 — O'zbek Tili Lokalizatsiya Loyihasi

Ushbu jildda `Watch Dogs 2` (Steam versiyasi: `D:\Steam\steamapps\common\Watch_Dogs2`) o'yinining barcha rus tilidagi lokalizatsiya matnlari (subtitrlar, menyu, UI, missiyalar, telefon xabarlari, ko'cha suhbatlari, qurol va jihozlar tavsifi) to'liq ajratib olinib, **JSON** formatida qulay tartibda saqlangan.

---

## 📊 Umumiy Statistika

* **Jami matnlar soni:** `48,142` ta unikal satr
* **Matn manbasi:** O'yinning eng oxirgi yangilanish arxivi (`patch2.dat`, `patch.dat`, `common.dat` ichidagi `languages/main_russian.loc`)
* **Kodlash:** `UTF-8`

---

## 📁 Fayllar va Jildlar Tuzilishi

| Fayl / Jild | Tavsifi |
| :--- | :--- |
| `watch_dogs_2_russian.json` | O'yinning barcha ruscha matnlari oddiy lug'at ko'rinishida (`{"ID": "Matn"}`) |
| `watch_dogs_2_uzbek_template.json` | Tarjima qilish uchun maxsus shablon (`[{"id": 4555, "category": "...", "ru": "...", "uz": ""}]`) |
| `categories/` | Matnlarning turlar bo'yicha ajratilgan alohida JSON fayllari |
| `statistics.json` | Loyiha va toifalar bo'yicha to'liq statistika |
| `scripts/` | Tarjimani tekshirish va o'yin formatiga qaytarish skriptlari |
| `tools/` | Matnlarni chiqarib olish va qayta ishlash uchun sozlangan modding utilitalari |
| `main_russian.loc` / `.txt` | O'yindan olingan xom binar va matnli lokalizatsiya fayllari |

---

## 📂 Toifalar bo'yicha Bo'limlar (`categories/`)

Matnlar tarjimonlar ishlashi uchun 8 ta asosiy guruhga ajratilgan:

1. **`story_and_cutscenes.json`** (`26,944` ta matn)
   * Asosiy syujet missiyalari, ketsahnalar, Mark va DedSec a'zolari o'rtasidagi asosiy dialoglar va subtitrlar.
2. **`phone_and_audio_logs.json`** (`5,606` ta matn)
   * Telefon qo'ng'iroqlari, SMS xabarlar, DedSec chat yozishmalari va shahar bo'ylab topiladigan audioyozuvlar.
3. **`notifications_and_world.json`** (`5,390` ta matn)
   * Xakerlik bo'yicha maslahatlar, ctOS tizim ogohlantirishlari, qobiliyatlar (skills) bo'yicha ko'rsatmalar.
4. **`ambient_dialogues.json`** (`4,619` ta matn)
   * San-Fransisko ko'chalaridagi oddiy shahar aholisining o'zaro suhbatlari va reaksiyalari.
5. **`ui_and_menus.json`** (`3,577` ta matn)
   * Bosh menyu, pauza menyusi, grafika, ovoz va boshqaruv (klaviatura/joystik) sozlamalari, telefon ilovalari interfeysi.
6. **`missions_and_objectives.json`** (`1,425` ta matn)
   * Operatsiyalar va missiyalar nomlari, har bir bosqichdagi aniq vazifalar va maqsadlar.
7. **`items_weapons_vehicles.json`** (`520` ta matn)
   * 3D-printer qurollari, kiyim-kechaklar, avtomobillar, dronlar va jumper (RC Jumper) tavsiflari.
8. **`multiplayer_and_extra.json`** (`61` ta matn)
   * Ko'p o'yinchili rejim (Bounty Hunter, Hacking Invasion, Co-op) matnlari.

---

## 🛠️ Yordamchi Skriptlar (`scripts/`)

### 1. Tarjimani tekshirish:
Tarjima jarayonida maxsus belgilar (`[LF]`, `{0}`, `%s`) tushib qolmaganligini va umumiy progressni ko'rish:
```bash
python scripts/validate_translation.py
```

### 2. JSON dan o'yin formatiga eksport qilish:
Tarjima qilingan JSON faylni o'yin kodi qabul qiladigan `main_uzbek.loc.txt` fayliga o'girish:
```bash
python scripts/json_to_loc_txt.py --input watch_dogs_2_uzbek_template.json --output main_uzbek.loc.txt
```

---

## ⚠️ Muhim Eslatmalar (Tarjimon uchun)

1. **Maxsus teglar:**
   * `[LF]` — yangi qatorga o'tish (Line Feed). Uni o'chirib yubormaslik kerak.
   * `[CR]` — qator qaytishi (Carriage Return).
   * `{0}`, `{1}`, `%s`, `%d` — o'yin dinamik qo'yadigan o'zgaruvchilar (masalan: o'yinchi ismi, pul miqdori, tugma nomi). Ular o'zgartirilmasligi shart.
2. **Belgilar qo'llab-quvvatlanishi:**
   * O'yinning shriftlar daraxtida standart Lotin (`A-Z`, `a-z`, apostrof `'`), Kirill (`А-Я`, `а-я`) va barcha standart tinish belgilari to'liq mavjud. Lotin alifbosidagi O'zbek tili uchun barcha harflar va `o'`, `g'`, `sh`, `ch` to'liq mos keladi.
