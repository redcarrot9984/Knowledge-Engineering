from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import pandas as pd
import time

# Chromeドライバーのパス
driver_path = 'C:/tools/chromedriver.exe'  # ※あなたの環境に合わせて変更

# SeleniumでChromeを起動
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

# ランキングページにアクセス
url = "https://kakaku.com/pc/note-pc/ranking_0020/"
driver.get(url)
time.sleep(3)  # ページ読み込み待機

# HTML取得してBeautifulSoupでパース
soup = BeautifulSoup(driver.page_source, "html.parser")

# データ格納用
data = []

# 商品ブロックをすべて取得
items = soup.find_all("div", class_="p-list-rank__item")

# 各商品情報を抽出
for item in items:
    try:
        name = item.find("p", class_="p-list-rank__product-name").get_text(strip=True)
        maker = name.split()[0]
        price = item.find("span", class_="p-list-rank__price-num").get_text(strip=True)
        rating = item.find("span", class_="c-review__average").get_text(strip=True) if item.find("span", class_="c-review__average") else None
        reviews = item.find("span", class_="c-review__count").get_text(strip=True).replace("件", "") if item.find("span", class_="c-review__count") else None
        detail_url = "https://kakaku.com" + item.find("a", class_="p-list-rank__product-name-link")['href']

        data.append({
            "商品名": name,
            "メーカー": maker,
            "価格": price,
            "評価": rating,
            "レビュー数": reviews,
            "詳細URL": detail_url
        })

    except Exception as e:
        print(f"エラー: {e}")
        continue

driver.quit()

# pandasで表示
df = pd.DataFrame(data)
print(df)

# CSVで保存
df.to_csv("kakaku_laptops.csv", index=False, encoding="utf-8-sig")
