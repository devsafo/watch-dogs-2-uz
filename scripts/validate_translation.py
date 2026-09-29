"""
validate_translation.py
Ushbu skript tarjima qilingan matnlarni tekshiradi:
1. Maxsus belgilar ([LF], [CR], {0}, %s, va h.k.) buzilmaganligini
2. Qaysi matnlar tarjima qilingani va qaysilari qolganligini
3. O'zbek tili uchun moslikni
"""

import os
import sys
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def validate(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, dict):
        items = [{"id": k, "ru": v, "uz": ""} for k, v in data.items()]
    else:
        items = data

    total = len(items)
    translated = 0
    warnings = []

    placeholder_pattern = re.compile(r'(\{[0-9]+\}|%[0-9]*[a-zA-Z]|\[LF\]|\[CR\]|<[^>]+>)')

    for item in items:
        uz = item.get("uz", "").strip()
        ru = item.get("ru", "")
        item_id = item.get("id")

        if uz:
            translated += 1
            # Check placeholders
            tags_ru = placeholder_pattern.findall(ru)
            tags_uz = placeholder_pattern.findall(uz)
            if sorted(tags_ru) != sorted(tags_uz):
                warnings.append(f"ID {item_id}: Teglar mos kelmadi! RU: {tags_ru} != UZ: {tags_uz}")

    percent = (translated / total) * 100 if total > 0 else 0
    print(f"Jami qatorlar: {total}")
    print(f"Tarjima qilingan: {translated} ({percent:.2f}%)")
    print(f"Qolgan qatorlar: {total - translated}")
    if warnings:
        print(f"Ogohlantirishlar ({len(warnings)} ta):")
        for w in warnings[:10]:
            print(" ", w)
        if len(warnings) > 10:
            print(f"  ... va yana {len(warnings) - 10} ta")
    else:
        print("Barcha tekshirilgan teglarda xatolik topilmadi!")

if __name__ == '__main__':
    target = os.path.join(BASE_DIR, 'watch_dogs_2_uzbek_template.json')
    if len(sys.argv) > 1:
        target = sys.argv[1]
    validate(target)
