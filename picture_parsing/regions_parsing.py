import requests
import urllib3
import random
import os
import time

# Отключаем SSL предупреждения
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#Подставляем URL на свой файл в network-е
url = 'https://bi.gks.ru/biportal/tmp/grid34bbafb1-1c5f-4843-92f4-a12dfa760d5d/vaxis.png'

#Можете подставить дополнительных user-agent-ов
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/14.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 Chrome/92.0.4515.159 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 Version/15.0 Mobile Safari/604.1"
]

#Подставляем необходимый referer
referer = "https://bi.gks.ru/biportal/contourbi.jsp?project=%2FDashboard%2Ftrade&report=_1102_%D0%98%D0%BD%D0%B4_%D1%84%D0%B8%D0%B7_%D0%BE%D0%B1%D1%8C%D0%B5%D0%BC%D0%B0_-_%D0%92%D0%B8%D1%82%D0%B0&toolbar=off&slice=slice1&view=view1"

#JSESSIONID тоже смотрим в network-е
session = requests.Session()
session.cookies.update({
    "JSESSIONID": "87090E2AE54D382CEB6FE724F8B61F1F",
    # добавь другие куки, если нужно
})

# Указываем кол-во попыток
max_retries = 10
for attempt in range(1, max_retries + 1):
    user_agent = random.choice(user_agents)
    headers = {
        "User-Agent": user_agent,
        "Referer": referer
    }
#try/else блок для загрузки + проверка ошибок
    try:
        response = session.get(url, headers=headers, verify=False, timeout=10)
        if response.status_code == 200:
            os.makedirs("../png", exist_ok=True)
            with open("../png/vaxis_1.png", "wb") as f:
                f.write(response.content)
            print("Скачано успешно.")
            break
        else:
            print(f"[Попытка {attempt}] Ошибка загрузки: {response.status_code}")
    except requests.RequestException as e:
        print(f"[Попытка {attempt}] Сетевая ошибка: {e}")

    # Пауза перед следующей попыткой
    time.sleep(10)
else:
    print("Не удалось скачать файл после нескольких попыток.")