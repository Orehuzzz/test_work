from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import pandas as pd
import os
import re

# Укажите пути к изображениям
path_1 = r'C:\Users\Vitaliy\PycharmProjects\test_work\png\vaxis_1.png'
path_2 = r'C:\Users\Vitaliy\PycharmProjects\test_work\png\vaxis_2.png'


# Укажите путь к  Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\\Program Files\\Tesseract-OCR/rus.traineddata"


# Предобрабатываем изображения
def preprocess_image(path):
    image = Image.open(path).convert("L")
    image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
    image = image.filter(ImageFilter.SHARPEN)
    image = ImageEnhance.Contrast(image).enhance(2.5)
    image = image.point(lambda p: 255 if p > 180 else 0)
    return image


# Извлекаем текст
def extract_lines_from_image(path):
    image = preprocess_image(path)
    config = "--psm 6"
    text = pytesseract.image_to_string(image, lang="eng+rus+osd", config=config)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines


# Очищаем строки и извлекаем названия региона
def clean_region(text):
    match = re.search(r"[А-ЯЁ][а-яё\s\-]+", text)
    if match:
        region = match.group(0).strip()
        region = re.sub(r"[^А-Яа-яЁё\s\-]", " ", region)
        return region
    return None

# Получаем строки с двух изображений
lines_1 = extract_lines_from_image(path_1)
lines_2 = extract_lines_from_image(path_2)

# Объединяем все строки в одну таблицу
all_lines = lines_1 + lines_2
df = pd.DataFrame(all_lines, columns=["Label"])

# Очищаем данные + удаляем дубликаты
df["Region"] = df["Label"].apply(clean_region)

df = df[(df["Region"].notna()) &
        (df["Region"] != "Н") &
        (df["Region"] != "Е") &
        (df["Region"] != "Ё") &
        (df["Region"] != "Российская")]

df.loc[df["Region"] == "Город", "Region"] = "Город Москва"
df.loc[df["Region"] == "Центральный федеральный", "Region"] = "Центральный федеральный округ"

df = df.drop_duplicates(subset=["Region"])
df = df.reset_index(drop=True)

# Проверяем результат
#print(df['Region'])


df['Region'].to_csv(r"C:\Users\Vitaliy\PycharmProjects\test_work\csv_result\city.csv", index=False, header=False, encoding="utf-8-sig")
print('данные перенесены в csv')