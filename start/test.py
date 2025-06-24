import requests
import random
import os
import time
import re
from io import BytesIO
from pathlib import Path
from typing import Union, List
from PIL import Image, ImageEnhance, ImageFilter
import pandas as pd
import pytesseract
import urllib3

# --------------------------- CONFIG --------------------------- #

TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
RUS_DATA_PATH = r"C:\Program Files\Tesseract-OCR\tessdata"

JSESSIONID = "6B61688F4D80FF486584EFCB303A43AD"
REFERER = "https://bi.gks.ru/biportal/contourbi.jsp?project=%2FDashboard%2Ftrade&report=_1102_%D0%98%D0%BD%D0%B4_%D1%84%D0%B8%D0%B7_%D0%BE%D0%B1%D1%8C%D0%B5%D0%BC%D0%B0_-_%D0%92%D0%B8%D1%82%D0%B0&toolbar=off&slice=slice1&view=view1"

IMAGE_TASKS = [
    {"url": "https://bi.gks.ru/biportal/tmp/grid34aadbb3-9bf8-4e2a-b806-04461983398f/vaxis.png", "type": "regions", "save_as": "vaxis_1.png"},
    {"url": "https://bi.gks.ru/biportal/tmp/gridf7cbfca4-0d35-4afb-8c6a-30e608961b8c/vaxis.png", "type": "regions", "save_as": "vaxis_2.png"},
    {"url": "https://bi.gks.ru/biportal/tmp/grid5a48ab6d-b73c-4946-8d50-f350d86f8341/vaxis.png", "type": "regions", "save_as": "vaxis_3.png"},
    {"url": "https://bi.gks.ru/biportal/tmp/grideb7d961b-5a1f-4551-9d05-e3187f8894cc/vaxis.png", "type": "regions", "save_as": "vaxis_4.png"},
    {"url": "https://bi.gks.ru/biportal/tmp/grid34aadbb3-9bf8-4e2a-b806-04461983398f/grid.png",  "type": "grid",    "save_as": "grid_1.png"},
    {"url": "https://bi.gks.ru/biportal/tmp/gridf7cbfca4-0d35-4afb-8c6a-30e608961b8c/grid.png",  "type": "grid",    "save_as": "grid_2.png"},
    {"url": "https://bi.gks.ru/biportal/tmp/grid5a48ab6d-b73c-4946-8d50-f350d86f8341/grid.png",  "type": "grid",    "save_as": "grid_3.png"},
    {"url": "https://bi.gks.ru/biportal/tmp/grideb7d961b-5a1f-4551-9d05-e3187f8894cc/grid.png",  "type": "grid",    "save_as": "grid_4.png"},
]

PNG_DIR = Path("png")
CSV_DIR = Path("csv_result")
FINAL_OUTPUT = CSV_DIR / "final_result.csv"

# --------------------------- SETUP --------------------------- #

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
os.environ["TESSDATA_PREFIX"] = RUS_DATA_PATH
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
PNG_DIR.mkdir(exist_ok=True)
CSV_DIR.mkdir(exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/14.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 Chrome/92.0.4515.159 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 Version/15.0 Mobile Safari/604.1"
]

# --------------------------- FUNCTIONS --------------------------- #

def download_image(url: str, save_path: str, jsessionid: str, referer: str, max_retries: int = 5) -> bool:
    session = requests.Session()
    session.cookies.update({"JSESSIONID": jsessionid})
    for attempt in range(1, max_retries + 1):
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Referer": referer
        }
        try:
            response = session.get(url, headers=headers, verify=False, timeout=10)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                print(f" Скачано: {save_path}")
                return True
            else:
                print(f"[{attempt}] Статус: {response.status_code}")
        except requests.RequestException as e:
            print(f"[{attempt}]  Ошибка сети: {e}")
        time.sleep(3)
    print(f" Не удалось скачать {url}")
    return False

def preprocess_image(image: Image.Image) -> Image.Image:
    image = image.convert("L")
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    image = image.filter(ImageFilter.SHARPEN)
    image = ImageEnhance.Contrast(image).enhance(2.5)
    image = image.point(lambda p: 255 if p > 180 else 0)
    return image

def extract_text_lines(image_input: Union[str, BytesIO]) -> List[str]:
    image = Image.open(image_input)
    image = preprocess_image(image)
    config = "--psm 6"
    text = pytesseract.image_to_string(image, lang="eng+rus", config=config)
    return [line.strip() for line in text.splitlines() if line.strip()]

def clean_region(line: str) -> Union[str, None]:
    match = re.search(r"[А-ЯЁ][А-Яа-яЁё\s\-]+", line)
    if match:
        region = re.sub(r"[^А-Яа-яЁё\s\-]", " ", match.group(0)).strip()
        return region
    return None

def parse_regions(lines: List[str]) -> List[str]:
    cleaned = [clean_region(line) for line in lines]
    return [r for r in cleaned if r and r not in {"Н", "Е", "Ё", "Российская"}]

def parse_grid_lines(lines: List[str]) -> List[float]:
    numbers = []
    for line in lines:
        match = re.search(r"\d{2,3}(?:[.,]\d{1,2})?", line.replace(",", "."))
        if match:
            try:
                num = float(match.group(0))
                numbers.append(num)
            except ValueError:
                continue
    return numbers

# --------------------------- MAIN --------------------------- #

def main():
    all_region_lines = []
    all_grid_values = []

    for task in IMAGE_TASKS:
        save_path = PNG_DIR / task["save_as"]
        downloaded = download_image(
            url=task["url"],
            save_path=str(save_path),
            jsessionid=JSESSIONID,
            referer=REFERER
        )
        if not downloaded:
            continue

        lines = extract_text_lines(str(save_path))

        if task["type"] == "regions":
            all_region_lines.extend(lines)
        elif task["type"] == "grid":
            values = parse_grid_lines(lines)
            all_grid_values.append(values)

    region_list = parse_regions(all_region_lines)
    region_list = list(dict.fromkeys(region_list))  

    df = pd.DataFrame({'Region': region_list})

    for i, values in enumerate(all_grid_values, 1):
        padded_values = values + [None] * (len(region_list) - len(values))
        df[f"Value_{i}"] = padded_values[:len(region_list)]

    print("\n Финальная таблица:")
    print(df)

    df.to_csv(FINAL_OUTPUT, index=False, encoding="utf-8-sig")
    print(f"\n CSV сохранён: {FINAL_OUTPUT}")

if __name__ == "__main__":
    main()
