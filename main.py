# main.py (修正版)

import yfinance as yf
from technical_analyzer import analyze_stock_technicals
from fundamental_analyzer import analyze_stock_fundamentals
from trading_signals import TradingSignalGenerator
from comprehensive_evaluator import ComprehensiveEvaluator, format_comprehensive_report, InvestmentEvaluation
from typing import List, Dict, Tuple
import pandas as pd


# --- 主程式執行 ---
# main.py 的 if __name__ == "__main__": 區塊 (修正版)

if __name__ == "__main__":
    STOCK_MAP = {
        "2330": "台積電", "2317": "鴻海", "2454": "聯發科", "2308": "台達電",
        "2382": "廣達", "2881": "富邦金", "2891": "中信金", "2882": "國泰金"
    }
    stock_code = "2330"
    stock_ticker_str = f"{stock_code}.TW"
    stock_name = STOCK_MAP.get(stock_code, stock_code)

    print(f"開始為 {stock_code} {stock_name} 生成綜合投資評估報告...")
    print("-" * 60)

    # --- 1. 建立 Ticker 物件並執行所有基礎分析 ---
    ticker_obj = yf.Ticker(stock_ticker_str)
    tech_data = analyze_stock_technicals(ticker_obj)
    fundamental_data = analyze_stock_fundamentals(ticker_obj)
    
    if tech_data is None or tech_data.empty:
        print(f"❌ 無法獲取 {stock_code} 的技術資料，無法產生報告。")
    else:
    # 建立評估器與訊號產生器
        evaluator = ComprehensiveEvaluator()
        signal_generator = TradingSignalGenerator()

        market_state = "多頭"
    
    # 處理 chip_data - 確保不為 None
    try:
        from chip_analyzer import get_institutional_trades
        chip_data = get_institutional_trades(days_to_fetch=3)
    except:
        chip_data = pd.DataFrame()  # 如果無法獲取籌碼數據，使用空的 DataFrame
    
    # 如果 chip_data 為 None，轉換為空的 DataFrame
    if chip_data is None:
        chip_data = pd.DataFrame()

    else:
        # --- 2. 建立評估器與訊號產生器 ---
        evaluator = ComprehensiveEvaluator()
        signal_generator = TradingSignalGenerator()
        
        # 假設 market_state 為多頭, chip_data 為 None (單一個股分析模式)
        market_state = "多頭"
        chip_data = None
        
        # --- 【核心修正】 ---
        # 步驟 2a: 正確呼叫 evaluator 取得技術分數和結果（只傳入 tech_data）
        technical_score, tech_result = evaluator.evaluate_technical_strength(tech_data)

        # 步驟 2b: 使用計算出的 technical_score 來產生交易訊號
        trading_signal = signal_generator.generate_signal(tech_data, technical_score, market_state)
        
        # 步驟 2c: 取得其他評估結果
        fund_score, fund_result = evaluator.evaluate_fundamental_quality(fundamental_data)
        risk_score, risk_result = evaluator.evaluate_risk_profile(tech_data, fundamental_data)
        momentum_score, momentum_result = evaluator.evaluate_momentum(tech_data)
        chip_score, chip_result = evaluator.evaluate_chip_flow(chip_data)
        
        # 步驟 2d: 產生最終評估
        evaluation = evaluator.generate_comprehensive_evaluation(
            tech_data=tech_data,
            tech_score=technical_score,  # 這裡傳入計算好的技術分數
            fundamental_data=fundamental_data,
            trading_signal=trading_signal,
            market_state=market_state,
            chip_data=chip_data
        )
        
        # --- 3. 格式化並印出最終報告 ---
        latest_price = tech_data.iloc[-1]['Close']
        final_report = format_comprehensive_report(
            evaluation=evaluation,
            stock_code=stock_code, 
            stock_name=stock_name,
            fund_result=fund_result, 
            tech_result=tech_result,
            risk_result=risk_result, 
            momentum_result=momentum_result,
            chip_result=chip_result, 
            current_price=latest_price,
            fundamental_data=fundamental_data
        )
        
        print(final_report)