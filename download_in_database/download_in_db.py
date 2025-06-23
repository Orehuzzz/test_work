import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, MetaData, Table
from params.parametrs import username, password, localhost

# Преобразовываем значения
def clean_float(x):
    try:
        x_str = str(x).replace(',', '.').strip()
        return float(x_str) if x_str else None
    except:
        return None

# Подключение к БД
engine = create_engine(
    f"postgresql+psycopg2://{username}:{password}@{localhost}:5432/main_database",
    connect_args={"connect_timeout": 10},
    pool_pre_ping=True
)

metadata = MetaData()

# Задаём таблицу
region_table = Table(
    'regions_data_table', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('region', String(100)),
    Column('index_prev_month', Float),
    Column('index_same_month_last_year', Float),
    Column('index_period_last_year', Float),
    schema='pictures_data'
)

# Создаем таблицу, если не существует
metadata.create_all(engine)

# Чтение CSV
df = pd.read_csv(
    r"C:\Users\Vitaliy\PycharmProjects\test_work\csv_result\result.csv",
    header=None,
    names=["region", "value1", "value2", "value3"],
    dtype=str,
    encoding='utf-8',
    on_bad_lines='skip'
)

# Преобразуем значения в числовой формат
for col in ["value1", "value2", "value3"]:
    df[col] = df[col].apply(clean_float)


# Переименовываем колонки
df = df.rename(columns={
    "value1": "index_prev_month",
    "value2": "index_same_month_last_year",
    "value3": "index_period_last_year"
})

# Удаляем строки с пустыми значениями
df = df.dropna(subset=["index_prev_month", "index_same_month_last_year", "index_period_last_year"])

print(f"Будет вставлено строк: {len(df)}")
print(df.head())

try:
    with engine.begin() as connection:
        # Можно очистить таблицу перед вставкой, если нужно:
        # connection.execute(region_table.delete())

        df.to_sql(
            name='regions_data_table',
            con=connection,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=1000,
            schema='pictures_data'
        )
    print("Данные успешно вставлены")
except Exception as e:
    print(f"Ошибка при вставке данных: {e}")
