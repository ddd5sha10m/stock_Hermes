# chip_analyzer.py - 法人籌碼分析模組 (多日版)

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from io import StringIO

def get_institutional_trades(days_to_fetch=5):
    """
    從台灣證券交易所抓取三大法人買賣超日報。
    【升級】能夠獲取最近 N 個交易日的數據。
    """
    print(f"\n===== 開始抓取最近 {days_to_fetch} 個交易日的法人籌碼數據... =====")
    
    all_chip_data = {}
    target_date = datetime.now()
    
    # 迴圈直到抓滿指定天數的資料
    while len(all_chip_data) < days_to_fetch:
        date_str = target_date.strftime('%Y%m%d')
        
        # 檢查是否為週末
        if target_date.weekday() >= 5:
            target_date -= timedelta(days=1)
            continue
            
        print(f"嘗試抓取 {date_str} 的數據...")
        url = f"https://www.twse.com.tw/fund/T86?response=html&date={date_str}&selectType=ALL"
        headers = {'User-Agent': 'Mozilla/5.0...'}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if "沒有符合條件的資料" in response.text:
                print(f"日期 {date_str} 非交易日或無資料。")
                target_date -= timedelta(days=1)
                time.sleep(2)
                continue

            all_tables = pd.read_html(StringIO(response.text))
            chip_data_df = all_tables[0]
            
            # (資料清理邏輯不變)
            chip_data_df.columns = chip_data_df.columns.droplevel(0)
            chip_data_df = chip_data_df.set_index('證券代號')
            chip_data_df.columns = chip_data_df.columns.str.strip()
            cols_to_convert = ['外陸資買賣超股數(不含外資自營商)', '投信買賣超股數']
            for col in cols_to_convert:
                chip_data_df[col] = pd.to_numeric(chip_data_df[col].astype(str).str.replace(',', ''), errors='coerce')
            chip_data_df = chip_data_df.rename(columns={
                '外陸資買賣超股數(不含外資自營商)': '外資買賣超',
                '投信買賣超股數': '投信買賣超'
            })
            for col in ['外資買賣超', '投信買賣超']:
                chip_data_df[col] = chip_data_df[col] / 1000

            # 將當天的 DataFrame 存入字典
            all_chip_data[date_str] = chip_data_df[['外資買賣超', '投信買賣超']]
            print(f"✓ 成功獲取 {date_str} 的數據。")
            
        except Exception as e:
            print(f"錯誤：抓取 {date_str} 數據時失敗: {e}")
        
        # 無論成功失敗，都將日期往前推一天，並加入延遲
        target_date -= timedelta(days=1)
        time.sleep(3) # 禮貌性延遲
    
    # 將字典中的所有 DataFrame 合併成一個大的 MultiIndex DataFrame
    if not all_chip_data:
        return None
        
    final_df = pd.concat(all_chip_data)
    final_df.index.names = ['日期', '代號']
    
    print("===== 最近 5 日籌碼數據抓取與處理完成！ =====")
    return final_df.sort_index(ascending=False)