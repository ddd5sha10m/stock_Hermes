import pandas as pd

# 讀取 CSV 檔案 (請改成你的檔名，例如 "stocks.csv")
df = pd.read_csv("StockList.csv", encoding="utf-8")

# 取出股票代號與名稱
stock_dict = dict(zip(df["代號"].astype(str), df["名稱"].str.strip()))

# 將字典存成一個 .py 檔案
with open("stocks_dict.py", "w", encoding="utf-8") as f:
    f.write("STOCK_DICT = {\n")
    for code, name in stock_dict.items():
        f.write(f'"{code}": "{name}",\n')
    f.write("}\n")

print("已經成功輸出 stocks_dict.py，可以直接 import 使用！")
