import pandas as pd
import re
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
from sklearn.tree import export_text
import matplotlib.pyplot as plt
from sklearn.tree import plot_tree

# CSV読み込み
gamingPC = pd.read_csv("notebook_pc_ranking.csv", encoding="utf-8")
print(f"Loaded {len(gamingPC)} rows from notebook_pc_ranking.csv")
print(gamingPC.head(10))  # 最初の10行を確認

# ランキング100位までを抽出
gamingPC = gamingPC[gamingPC["rank"] <= 100].sort_values("rank")
print(f"Items after filtering to rank <= 100: {len(gamingPC)}")

# 価格のN/A処理
gamingPC["price"] = gamingPC["price"].apply(lambda x: "N/A" if pd.isna(x) or x == "" or x == "N/A" else float(x))

# ラベル付け（1〜10位：正例, 41位以降：負例）
gamingPC["label"] = 0
gamingPC.loc[gamingPC["rank"] <= 10, "label"] = 1
gamingPC = gamingPC[(gamingPC["rank"] <= 10) | (gamingPC["rank"] >= 41)].copy()
gamingPC = gamingPC[gamingPC["price"] != "N/A"].copy()
print(f"Items after filtering label and price != N/A: {len(gamingPC)}")

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

# カテゴリ変数のエンコーディング
def clean_string(s):
    if pd.isna(s) or s in ["N/A", "", "―"]:
        return "N/A"
    s = str(s).strip()
    s = re.sub(r'\s+', '_', s)  # スペースをアンダースコアに
    s = s.replace(",", "_").replace("\n", "").replace("\r", "").replace("\t", "").replace('"', "_")
    s = re.sub(r'_+', '_', s).strip("_")
    return s

gamingPC["maker"] = gamingPC["maker"].apply(clean_string)
gamingPC["cpu"] = gamingPC["cpu"].apply(clean_string)
gamingPC["os"] = gamingPC["os"].apply(clean_string)

# LabelEncoderでカテゴリ変数を数値化
le_maker = LabelEncoder()
le_cpu = LabelEncoder()
le_os = LabelEncoder()

gamingPC["maker_encoded"] = le_maker.fit_transform(gamingPC["maker"])
gamingPC["cpu_encoded"] = le_cpu.fit_transform(gamingPC["cpu"])
gamingPC["os_encoded"] = le_os.fit_transform(gamingPC["os"])

# 特徴量とターゲットの準備
features = ["maker_encoded", "cpu_encoded", "os_encoded", "memory_size", "storage_size", "price"]
X = gamingPC[features]
y = gamingPC["label"]

# 訓練/テスト分割
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")

# CARTモデルの訓練
clf = DecisionTreeClassifier(max_depth=5, random_state=42)
clf.fit(X_train, y_train)

# 予測と精度評価
y_pred = clf.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Test Accuracy: {accuracy:.4f}")

# 決定木のテキスト表現
tree_text = export_text(clf, feature_names=features)
print("\nDecision Tree Structure:")
print(tree_text)

# 決定木の可視化
plt.figure(figsize=(20, 10))
plot_tree(clf, feature_names=features, class_names=["0", "1"], filled=True, rounded=True)
plt.title("CART Decision Tree for Notebook PC Ranking")
plt.savefig("cart_decision_tree.png")
print("Decision tree saved as cart_decision_tree.png")
plt.close()

# 特徴量の重要度
feature_importance = pd.DataFrame({
    "Feature": features,
    "Importance": clf.feature_importances_
}).sort_values("Importance", ascending=False)
print("\nFeature Importance:")
print(feature_importance)