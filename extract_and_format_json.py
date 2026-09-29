import os
import sys
import json
from collections import Counter, OrderedDict

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"D:\Watch Dogs 2 - UZ"
CATEGORIES_DIR = os.path.join(BASE_DIR, "categories")
os.makedirs(CATEGORIES_DIR, exist_ok=True)

def categorize(id_num, text):
    if 0 <= id_num < 50000:
        return 'ui_and_menus'
    elif 50000 <= id_num < 100000:
        return 'ui_and_menus'
    elif 100000 <= id_num < 150000:
        return 'items_weapons_vehicles'
    elif 150000 <= id_num < 200000:
        return 'ambient_dialogues'
    elif 200000 <= id_num < 250000:
        return 'ui_and_menus'
    elif 250000 <= id_num < 400000:
        return 'phone_and_audio_logs'
    elif 400000 <= id_num < 550000:
        return 'notifications_and_world'
    elif 550000 <= id_num < 600000:
        return 'missions_and_objectives'
    elif 600000 <= id_num < 750000:
        return 'story_and_cutscenes'
    else:
        return 'multiplayer_and_extra'

CATEGORY_NAMES = {
    'story_and_cutscenes': 'Asosiy hikoya va subtitrlar (Story Cutscenes & Subtitles)',
    'phone_and_audio_logs': 'Telefon xabarlari, DedSec chat va audioyozuvlar (Phone & Audio Logs)',
    'notifications_and_world': 'O\'yin bildirishnomalari va xakerlik maslahatlari (Notifications & Hints)',
    'ambient_dialogues': 'Shahar aholisi va ko\'cha suhbatlari (Pedestrian & Ambient Dialogues)',
    'ui_and_menus': 'Menyu, sozlamalar, boshqaruv va interfeys (UI & Menus)',
    'missions_and_objectives': 'Missiya nomlari va topshiriq maqsadlari (Missions & Objectives)',
    'items_weapons_vehicles': 'Qurollar, kiyimlar, transport va jihozlar (Items, Weapons & Vehicles)',
    'multiplayer_and_extra': 'Ko\'p o\'yinchili rejim va qo\'shimchalar (Multiplayer & Extras)'
}

raw_strings = {}

def load_file(path):
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-16') as f:
        for line in f:
            if '=' in line:
                k, v = line.split('=', 1)
                raw_strings[int(k)] = v.rstrip('\r\n')

# 1. Base common
load_file(os.path.join(BASE_DIR, 'main_russian_common.loc.txt'))
# 2. Patch 1
load_file(os.path.join(BASE_DIR, 'main_russian_patch.loc.txt'))
# 3. Patch 2 (latest patch overrides earlier ones)
load_file(os.path.join(BASE_DIR, 'main_russian.loc.txt'))

print(f"Total merged strings: {len(raw_strings)}")

# Sort by ID
sorted_ids = sorted(raw_strings.keys())

# 1. Full key-value dictionary
dict_all = OrderedDict()
for i in sorted_ids:
    dict_all[str(i)] = raw_strings[i]

with open(os.path.join(BASE_DIR, 'watch_dogs_2_russian.json'), 'w', encoding='utf-8') as f:
    json.dump(dict_all, f, ensure_ascii=False, indent=2)
print("Saved watch_dogs_2_russian.json")

# 2. Template for Uzbek translation
template_list = []
categorized_data = {cat: [] for cat in CATEGORY_NAMES.keys()}
category_counts = Counter()

for i in sorted_ids:
    text = raw_strings[i]
    cat = categorize(i, text)
    category_counts[cat] += 1
    
    item = {
        "id": i,
        "category": cat,
        "ru": text,
        "uz": ""
    }
    template_list.append(item)
    categorized_data[cat].append(item)

with open(os.path.join(BASE_DIR, 'watch_dogs_2_uzbek_template.json'), 'w', encoding='utf-8') as f:
    json.dump(template_list, f, ensure_ascii=False, indent=2)
print("Saved watch_dogs_2_uzbek_template.json")

# 3. Categorized JSON files
for cat, items in categorized_data.items():
    cat_filename = f"{cat}.json"
    cat_filepath = os.path.join(CATEGORIES_DIR, cat_filename)
    with open(cat_filepath, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"Saved {cat_filepath} ({len(items)} strings)")

# 4. Statistics
stats = {
    "game": "Watch Dogs 2 (PC / Steam)",
    "source_archive": "patch2.dat / patch.dat / common.dat (languages/main_russian.loc)",
    "total_strings": len(sorted_ids),
    "categories": {
        cat: {
            "name_uz": CATEGORY_NAMES[cat],
            "count": category_counts[cat],
            "file": f"categories/{cat}.json"
        }
        for cat in CATEGORY_NAMES.keys()
    }
}

with open(os.path.join(BASE_DIR, 'statistics.json'), 'w', encoding='utf-8') as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)
print("Saved statistics.json")
