from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import re
import requests

# Set up headless Chrome
options = Options()
#options.add_argument("--headless")
options.add_argument("--disable-gpu")  # Optional but useful for Windows
options.add_argument("--no-sandbox")   # Helpful if you're running in restricted environments

# Use your extracted driver
service = Service("C:/Users/Vitaliy/Desktop/chrome-win64/chrome.exe")
driver = webdriver.Chrome(service=service, options=options)

# Load the page
url = "https://bi.gks.ru/biportal/contourbi.jsp?project=%2FDashboard%2Ftrade&report=_1102_%D0%98%D0%BD%D0%B4_%D1%84%D0%B8%D0%B7_%D0%BE%D0%B1%D1%8C%D0%B5%D0%BC%D0%B0_-_%D0%92%D0%B8%D1%82%D0%B0&toolbar=on&slice=slice1&view=view1"  # replace ... with actual report value
driver.get(url)

# Give JS time to load
time.sleep(10)

target_img = driver.find_element("id", "x-auto-79")

# Get the style attribute from that image
style = target_img.get_attribute("style")
print("TARGET STYLE:", style)

background_url = None
match = re.search(r'url\("?(tmp/[^")]+)"?\)', style)
if match:
    background_url = match.group(1)
    full_url = f"https://bi.gks.ru/biportal/{background_url}"
    print("Found target image URL:", full_url)
else:
    print("Target <img> found, but no background-image style.")

if background_url:
    img_data = requests.get(full_url, verify=False).content
    with open("../grid.png", "wb") as f:
        f.write(img_data)
    print("Image saved as grid.png")
