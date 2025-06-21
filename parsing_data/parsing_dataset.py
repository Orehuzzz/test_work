from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import pandas as pd
import os

# Указываем путь к tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\\Program Files\\Tesseract-OCR/rus.traineddata"

# Функция предобработки изображения
def preprocess_image(path):
    """Открытие и предобработка изображения"""
    img = Image.open(path).convert("L")  # grayscale
    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(2)
    img = img.point(lambda p: 255 if p > 180 else 0)  # бинаризация
    return img

# Функция извлечения таблицы из изображения
def extract_table(image):
    """Извлечение текста и построение таблицы"""
    df = pytesseract.image_to_data(image, lang="eng+rus", output_type=pytesseract.Output.DATAFRAME)
    df = df[df.text.notnull() & (df.conf != "-1")]
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"] != ""]

    # Кластеризация по Y (строки)
    row_threshold = 10
    df = df.sort_values("top")
    row_positions = []
    for y in df["top"]:
        if not row_positions or abs(y - row_positions[-1]) > row_threshold:
            row_positions.append(y)
    df["row_id"] = df["top"].apply(lambda y: min(row_positions, key=lambda ry: abs(ry - y)))

    # Кластеризация по X (колонки)
    col_threshold = 30
    df = df.sort_values("left")
    col_positions = []
    for x in df["left"]:
        if not col_positions or abs(x - col_positions[-1]) > col_threshold:
            col_positions.append(x)
    df["col_id"] = df["left"].apply(lambda x: min(col_positions, key=lambda cx: abs(cx - x)))

    # Построение таблицы
    grid = []
    for row in sorted(df["row_id"].unique()):
        row_data = df[df["row_id"] == row]
        row_cells = [""] * len(col_positions)
        for _, cell in row_data.iterrows():
            col_index = col_positions.index(cell["col_id"])
            row_cells[col_index] = cell["text"]
        grid.append(row_cells)

    return pd.DataFrame(grid)

# Пути к изображениям
path_1 = r"C:\Users\Vitaliy\PycharmProjects\test_work\png\grid.png"
path_2 = r"C:\Users\Vitaliy\PycharmProjects\test_work\png\grid_2.png"

# Обработка изображений
image1 = preprocess_image(path_1)
image2 = preprocess_image(path_2)

# Извлечение таблиц
table_1 = extract_table(image1)
table_2 = extract_table(image2)

# Объединение таблиц + очистка от дубликатов
#с 13-18 дубликаты - удаляем
combined_table = pd.concat([table_1, table_2], ignore_index=True)
combined_table = combined_table.drop(index=range(13, 19)).reset_index(drop=True)
combined_table[0] = combined_table[0].replace('1051', '105,1')
combined_table[1] = combined_table[1].replace('1159', '115,9')
combined_table[1] = combined_table[1].replace('1112', '111,2')
combined_table[2] = combined_table[2].replace('1131', '113,1')
combined_table[2] = combined_table[2].replace('12,7', '112,7')
combined_table[2] = combined_table[2].replace('1169', '116,9')
combined_table[2] = combined_table[2].replace('12,5', '112,5')

print(combined_table)
#Перекидываем в csv
combined_table.to_csv(r"C:\Users\Vitaliy\PycharmProjects\test_work\csv_result\data.csv", index=False, header=False, encoding="utf-8-sig")
print('Данные перенесены в csv')

