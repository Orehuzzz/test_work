from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import pandas as pd
import os
import re

# Настройка Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\\Program Files\\Tesseract-OCR/rus.traineddata"

# Пути к изображениям с регионами (городами)
path_regions_1 = r'C:\Users\Vitaliy\PycharmProjects\test_work\png\vaxis_1.png'
path_regions_2 = r'C:\Users\Vitaliy\PycharmProjects\test_work\png\vaxis_2.png'

# Пути к изображениям с таблицами чисел
path_table_1 = r"C:\Users\Vitaliy\PycharmProjects\test_work\png\grid.png"
path_table_2 = r"C:\Users\Vitaliy\PycharmProjects\test_work\png\grid_2.png"

# Функция предобработки
def preprocess_image(path):
    img = Image.open(path).convert("L")
    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(2.5)
    img = img.point(lambda p: 255 if p > 180 else 0)
    return img

# Извлечение строк (городов)
def extract_lines_from_image(path):
    image = preprocess_image(path)
    config = "--psm 6"
    text = pytesseract.image_to_string(image, lang="eng+rus+osd", config=config)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines

# Очистка названий регионов (городов)
def clean_region(text):
    match = re.search(r"[А-ЯЁ][а-яё\s\-]+", text)
    if match:
        region = match.group(0).strip()
        region = re.sub(r"[^А-Яа-яЁё\s\-]", " ", region)
        return region
    return None

# Извлекаем регионы из двух изображений
lines_1 = extract_lines_from_image(path_regions_1)
lines_2 = extract_lines_from_image(path_regions_2)
all_lines = lines_1 + lines_2

df_regions = pd.DataFrame(all_lines, columns=["Label"])
df_regions["Region"] = df_regions["Label"].apply(clean_region)

df_regions = df_regions[(df_regions["Region"].notna()) &
                        (df_regions["Region"].str.len() > 1) &
                        (~df_regions["Region"].isin(["Н", "Е", "Ё", "Российская"]))]

df_regions.loc[df_regions["Region"] == "Город", "Region"] = "Город Москва"
df_regions.loc[df_regions["Region"] == "Центральный федеральный", "Region"] = "Центральный федеральный округ"

df_regions = df_regions.drop_duplicates(subset=["Region"]).reset_index(drop=True)

# Функция извлечения таблицы чисел из изображения
def extract_table(image):
    df = pytesseract.image_to_data(image, lang="eng", output_type=pytesseract.Output.DATAFRAME)
    df = df[df.text.notnull() & (df.conf != "-1")]
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"] != ""]

    row_threshold = 10
    df = df.sort_values("top")
    row_positions = []
    for y in df["top"]:
        if not row_positions or abs(y - row_positions[-1]) > row_threshold:
            row_positions.append(y)
    df["row_id"] = df["top"].apply(lambda y: min(row_positions, key=lambda ry: abs(ry - y)))

    col_threshold = 30
    df = df.sort_values("left")
    col_positions = []
    for x in df["left"]:
        if not col_positions or abs(x - col_positions[-1]) > col_threshold:
            col_positions.append(x)
    df["col_id"] = df["left"].apply(lambda x: min(col_positions, key=lambda cx: abs(cx - x)))

    grid = []
    for row in sorted(df["row_id"].unique()):
        row_data = df[df["row_id"] == row]
        row_cells = [""] * len(col_positions)
        for _, cell in row_data.iterrows():
            col_index = col_positions.index(cell["col_id"])
            row_cells[col_index] = cell["text"]
        grid.append(row_cells)

    return pd.DataFrame(grid)

# Обрабатываем таблицы с числами
image_table_1 = preprocess_image(path_table_1)
image_table_2 = preprocess_image(path_table_2)
table_1 = extract_table(image_table_1)
table_2 = extract_table(image_table_2)

combined_table = pd.concat([table_1, table_2], ignore_index=True)

# Удаляем дубликаты строк с 13 по 18
combined_table = combined_table.drop(index=range(13, 19), errors='ignore').reset_index(drop=True)

# Исправляем ошибки OCR в числах
combined_table = combined_table.replace({
    '1159': '115,9',
    '1131': '113,1',
    '12,7': '112,7',
    '1169': '116,9',
    '12,5': '112,5'
})

# Проверяем совпадение числа регионов и строк таблицы
if len(df_regions) == len(combined_table):
    combined_table.insert(0, "Region", df_regions["Region"])
else:
    print(f"Ошибка: кол-во регионов ({len(df_regions)}) и строк таблицы ({len(combined_table)}) не совпадает!")

# Итоговый вывод
print(combined_table)