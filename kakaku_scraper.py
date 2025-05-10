from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import pandas as pd
import time

# Chrome�h���C�o�[�̃p�X
driver_path = 'C:/tools/chromedriver.exe'  # �����Ȃ��̊��ɍ��킹�ĕύX

# Selenium��Chrome���N��
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

# �����L���O�y�[�W�ɃA�N�Z�X
url = "https://kakaku.com/pc/note-pc/ranking_0020/"
driver.get(url)
time.sleep(3)  # �y�[�W�ǂݍ��ݑҋ@

# HTML�擾����BeautifulSoup�Ńp�[�X
soup = BeautifulSoup(driver.page_source, "html.parser")

# �f�[�^�i�[�p
data = []

# ���i�u���b�N�����ׂĎ擾
items = soup.find_all("div", class_="p-list-rank__item")

# �e���i���𒊏o
for item in items:
    try:
        name = item.find("p", class_="p-list-rank__product-name").get_text(strip=True)
        maker = name.split()[0]
        price = item.find("span", class_="p-list-rank__price-num").get_text(strip=True)
        rating = item.find("span", class_="c-review__average").get_text(strip=True) if item.find("span", class_="c-review__average") else None
        reviews = item.find("span", class_="c-review__count").get_text(strip=True).replace("��", "") if item.find("span", class_="c-review__count") else None
        detail_url = "https://kakaku.com" + item.find("a", class_="p-list-rank__product-name-link")['href']

        data.append({
            "���i��": name,
            "���[�J�[": maker,
            "���i": price,
            "�]��": rating,
            "���r���[��": reviews,
            "�ڍ�URL": detail_url
        })

    except Exception as e:
        print(f"�G���[: {e}")
        continue

driver.quit()

# pandas�ŕ\��
df = pd.DataFrame(data)
print(df)

# CSV�ŕۑ�
df.to_csv("kakaku_laptops.csv", index=False, encoding="utf-8-sig")
