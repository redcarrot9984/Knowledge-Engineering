import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import re
import csv

# URL
url = "https://kakaku.com/pc/note-pc/ranking_0020/"

# データフレーム初期化
df_list = []

# Seleniumドライバーのセットアップ
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 最初のページを取得して最大ページ数を推測
driver.get(url)
WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "rkgBox")))
soup = BeautifulSoup(driver.page_source, "html.parser", from_encoding="utf-8")
page_info = soup.find("div", class_="pager") or soup.find("ul", class_="pagination") or soup.find("div", class_="pageNavi")
max_page = 10
if page_info:
    pages = page_info.find_all("a")
    page_numbers = [int(page.text) for page in pages if page.text.isdigit()]
    max_page = max(page_numbers) if page_numbers else max_page
print(f"Total pages to scrape: {max_page}")

# 各ページのループ
for page in range(1, max_page + 1):
    page_url = f"{url}?page={page}" if page > 1 else url
    print(f"Scraping page {page}: {page_url}")
    driver.get(page_url)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "rkgBox")))
    except Exception as e:
        print(f"Timeout waiting for page {page}: {e}")
        continue
    soup = BeautifulSoup(driver.page_source, "html.parser", from_encoding="utf-8")

    # 商品ブロックを取得
    items = soup.select("div.rkgBox")
    print(f"Page {page}: Found {len(items)} items")

    if not items:
        print(f"No items found on page {page}. Stopping.")
        break

    for i, item in enumerate(items):
        try:
            # ランキング
            rank_elem = item.find("span", class_="num")
            rank = rank_elem.text.strip() if rank_elem else str(i + 1 + (page - 1) * 12)

            # メーカー
            maker = item.find("span", class_="rkgBoxNameMaker")
            maker = maker.text.strip() if maker else "N/A"

            # 製品名
            product = item.find("span", class_="rkgBoxNameItem")
            product = product.text.strip() if product else "N/A"

            # 価格
            price_elem = item.find("span", class_="price")
            price = price_elem.text.replace("¥", "").replace(",", "") if price_elem and price_elem.text.strip() else "N/A"
            price = int(price) if price != "N/A" and price.isdigit() else price

            # スペック
            detail = item.find("div", class_="rkgRow rowDetail")
            detail = detail.text.strip() if detail else ""
            detail = re.sub(r'\s+', ' ', detail)  # 全角スペースや複数スペースを単一スペースに
            print(f"Item {i} on page {page} detail: {detail}")

            # 正規表現
            cpu_pattern = r"CPU：([^/]+)\/"
            memory_pattern = r"メモリ容量：(\d+GB)"
            storage_pattern = r"(?:ストレージ容量：|SSD|eMMC|NVMe SSD|M\.2 SSD)[:\s]*(\d+\.?\d*)\s*(GB|TB)|(\d+\.?\d*)\s*(GB|TB)"
            os_pattern = r"OS：([^\s]+(?:\s+[^\s]+)*?)(?:\s+重量：|$)"

            cpu_match = re.search(cpu_pattern, detail)
            memory_match = re.search(memory_pattern, detail)
            storage_match = re.search(storage_pattern, detail, re.IGNORECASE)
            os_match = re.search(os_pattern, detail)

            cpu = cpu_match.group(1).strip() if cpu_match else "N/A"
            memory = memory_match.group(1).strip() if memory_match else "N/A"

            # ストレージ処理
            storage = "N/A"
            if storage_match:
                try:
                    storage_value = float(storage_match.group(1) or storage_match.group(3))
                    storage_unit = (storage_match.group(2) or storage_match.group(4)).upper()
                    storage = f"{int(storage_value * 1000) if storage_unit == 'TB' else int(storage_value)}GB"
                    print(f"Storage matched on page {page} item {i}: {storage}")
                except Exception as e:
                    print(f"Storage parsing error on page {page} item {i}: {detail}, error: {e}")
                    storage = "N/A"
            else:
                print(f"No storage match on page {page} item {i}: {detail}")

            os = os_match.group(1).strip() if os_match else "N/A"
            print(f"OS matched on page {page} item {i}: {os}")

            # データ追加
            df_list.append({
                "maker": maker,
                "product": product,
                "price": price,
                "cpu": cpu,
                "memory": memory,
                "storage": storage,
                "os": os,
                "rank": int(rank)
            })

        except Exception as e:
            print(f"Error parsing item {i} on page {page}: {e}")
            continue

    time.sleep(1)

# 終了
driver.quit()

# データ整形
gamingPC = pd.DataFrame(df_list).reset_index(drop=True)
print(f"Total items scraped: {len(gamingPC)}")
print(gamingPC.head(20))  # 最初の20行を表示して2～11位を確認

# ランキング100位までを抽出
gamingPC = gamingPC[gamingPC["rank"] <= 100].sort_values("rank")
print(f"Items after filtering to rank <= 100: {len(gamingPC)}")

# 価格をN/Aで埋める
gamingPC["price"] = gamingPC["price"].apply(lambda x: "N/A" if pd.isna(x) or x == "" or x == "―" else x)

# 文字列のクリーンアップ
def clean_string(s):
    if pd.isna(s) or s in ["N/A", "", "―"]:
        return "N/A"
    s = str(s).strip()
    s = re.sub(r'\s+', ' ', s)  # 複数スペースを単一に
    s = s.replace("\n", "").replace("\r", "").replace("\t", "")
    return s

gamingPC["maker"] = gamingPC["maker"].apply(clean_string)
gamingPC["product"] = gamingPC["product"].apply(clean_string)
gamingPC["cpu"] = gamingPC["cpu"].apply(clean_string)
gamingPC["os"] = gamingPC["os"].apply(clean_string)

# 保存（Windows互換のためutf-8-sig）
gamingPC.to_csv("notebook_pc_ranking.csv", index=False, encoding="utf-8-sig")
print("Saved to notebook_pc_ranking.csv")

# ラベル付け（1〜10位：正例, 41位以降：負例）
gamingPC["label"] = 0
gamingPC.loc[gamingPC["rank"] <= 10, "label"] = 1
gamingPC = gamingPC[(gamingPC["rank"] <= 10) | (gamingPC["rank"] >= 41)].copy()
gamingPC = gamingPC[gamingPC["price"] != "N/A"]

# 特徴量の前処理
def extract_memory(memory):
    try:
        return int(memory.replace("GB", ""))
    except:
        return 0

def extract_storage(storage):
    try:
        return int(storage.replace("GB", ""))
    except:
        return 0

gamingPC["memory_size"] = gamingPC["memory"].apply(extract_memory)
gamingPC["storage_size"] = gamingPC["storage"].apply(extract_storage)

def clean_string_for_see5(s):
    if pd.isna(s) or s in ["N/A", "", "―"]:
        return "N/A"
    s = str(s).replace(",", "_").replace("\n", "_").replace('"', "_").replace(" ", "_")
    return re.sub(r'_+', '_', s).strip("_")

gamingPC["maker"] = gamingPC["maker"].apply(clean_string_for_see5)
gamingPC["cpu"] = gamingPC["cpu"].apply(clean_string_for_see5)
gamingPC["os"] = gamingPC["os"].apply(clean_string_for_see5)

# See5用データセット
see5_data = gamingPC[["maker", "cpu", "os", "memory_size", "storage_size", "price", "label"]]
see5_data.to_csv("notebook_pc.data", index=False, header=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)
print("Saved to notebook_pc.data")

# .namesファイル作成
makers = sorted(set(see5_data["maker"]) - {"N/A"})
cpus = sorted(set(see5_data["cpu"]) - {"N/A"})
oses = sorted(set(see5_data["os"]) - {"N/A"})

makers_str = ",".join(makers) if makers else "N/A"
cpus_str = ",".join(cpus) if cpus else "N/A"
oses_str = ",".join(oses) if oses else "N/A"

names_content = f"""label: 0,1.
maker: {makers_str}.
cpu: {cpus_str}.
os: {oses_str}.
memory_size: continuous.
storage_size: continuous.
price: continuous.
"""

with open("notebook_pc.names", "w", encoding="utf-8") as f:
    f.write(names_content)
print("Saved to notebook_pc.names")