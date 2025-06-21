import pandas as pd

regions_df = pd.read_csv('city.csv')
data_df = pd.read_csv('data.csv')

combined_df = pd.concat([regions_df, data_df], axis=1)

combined_df.to_csv('result.csv', index=False, encoding='utf-8-sig')
print("Объединённый файл сохранён как 'result.csv'")