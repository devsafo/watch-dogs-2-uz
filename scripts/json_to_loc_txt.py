"""
json_to_loc_txt.py
Ushbu skript tarjima qilingan JSON fayllarni yana o'yin qabul qiladigan
UTF-16 formatidagi .loc.txt faylga aylantiradi.

Foydalanish:
  python scripts/json_to_loc_txt.py
  (yoki alohida fayl ko'rsatilsa: python scripts/json_to_loc_txt.py --input watch_dogs_2_uzbek_translated.json)
"""

import os
import sys
import json
import argparse

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def convert(input_path, output_path, fallback_ru=True):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Dictionary or list
    lines_dict = {}
    if isinstance(data, dict):
        for k, v in data.items():
            lines_dict[int(k)] = str(v)
    elif isinstance(data, list):
        for item in data:
            id_num = item["id"]
            # If uzbek translation exists, use it; otherwise fallback to russian
            text_uz = item.get("uz", "").strip()
            text_ru = item.get("ru", "")
            if text_uz:
                lines_dict[id_num] = text_uz
            elif fallback_ru:
                lines_dict[id_num] = text_ru

    # Write output in UTF-16 with CRLF
    sorted_ids = sorted(lines_dict.keys())
    with open(output_path, 'w', encoding='utf-16', newline='\r\n') as f:
        for id_num in sorted_ids:
            val = lines_dict[id_num]
            f.write(f"{id_num}={val}\n")

    print(f"Muvaffaqiyatli saqlandi: {output_path} ({len(sorted_ids)} ta qator)")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert translated JSON to Watch Dogs 2 .loc.txt format")
    parser.add_argument('--input', default=os.path.join(BASE_DIR, 'watch_dogs_2_uzbek_template.json'), help="Input JSON path")
    parser.add_argument('--output', default=os.path.join(BASE_DIR, 'main_uzbek.loc.txt'), help="Output .loc.txt path")
    args = parser.parse_args()

    convert(args.input, args.output)
