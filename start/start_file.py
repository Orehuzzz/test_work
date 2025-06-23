import requests
import pytesseract
from PIL import Image
import pandas as pd
from sqlalchemy import create_engine
from params.parametrs import username, password, localhost

# === Получение изображения ===
def pull_data_from_api() -> str:
    """Скачивает изображение из API и сохраняет локально"""
    url = "https://bi.gks.ru/biportal/tmp/grid7a3d968b-6e2c-4c5b-8ceb-f64813cac883/grid.png" #Подставьте свой
    response = requests.get(url)
    if response.status_code == 200:
        path = "downloaded_image.jpg"
        with open(path, 'wb') as f:
            f.write(response.content)
        return path
    else:
        raise Exception("Не удалось получить изображение из API")

# === Парсинг текста из изображения ===
def parse_data_from_image(image_path: str) -> pd.DataFrame:
    """Извлекает текст из изображения и преобразует в DataFrame"""
    image = Image.open(image_path)
    raw_text = pytesseract.image_to_string(image, lang='rus')

    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    data = []

    for line in lines:
        parts = [part.strip() for part in line.split(',')]
        if len(parts) == 4:
            data.append(parts)

    df = pd.DataFrame(data, columns=["region", "value1", "value2", "value3"])

    def clean(x):
        try:
            return float(str(x).replace(',', '.'))
        except:
            return None

    for col in ["value1", "value2", "value3"]:
        df[col] = df[col].apply(clean)

    df = df.dropna()
    df = df.rename(columns={
        "value1": "index_prev_month",
        "value2": "index_same_month_last_year",
        "value3": "index_period_last_year"
    })
    return df

# === 3. Загрузка в БД ===
def load_data_to_db(df: pd.DataFrame):
    """Загружает DataFrame в PostgreSQL"""
    engine = create_engine(
        f"postgresql+psycopg2://{username}:{password}@{localhost}:5432/main_database"
    )
    df.to_sql(
        name='regions_data_table',
        con=engine,
        schema='pictures_data',
        if_exists='append',
        index=False,
        method='multi'
    )
    print("Данные успешно загружены в БД")


def main():
    image_path = pull_data_from_api()
    df = parse_data_from_image(image_path)
    load_data_to_db(df)

if __name__ == "__main__":
    main()