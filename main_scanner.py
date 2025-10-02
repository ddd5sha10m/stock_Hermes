# main_scanner.py - 綜合評估版本

import pandas as pd
from datetime import datetime
import time

# 從我們自訂的模組中，匯入需要的函式和資料
from stock_list import STOCK_LIST
from technical_analyzer import analyze_stock_technicals
from fundamental_analyzer import analyze_stock_fundamentals
from trading_signals import TradingSignalGenerator
from comprehensive_evaluator import ComprehensiveEvaluator

def get_valid_ticker(stock_code: str):
    """
    智能獲取有效的 ticker
    優先嘗試 .TW (上市)，如果失敗則嘗試 .TWO (上櫃)
    """
    import yfinance as yf
    
    # 先嘗試 .TW (上市)
    ticker_tw = f"{stock_code}.TW"
    try:
        test_data = yf.Ticker(ticker_tw).history(period="5d")
        if not test_data.empty:
            return ticker_tw, "TW"
    except:
        pass
    
    # 如果 .TW 失敗，嘗試 .TWO (上櫃)
    ticker_two = f"{stock_code}.TWO"
    try:
        test_data = yf.Ticker(ticker_two).history(period="5d")
        if not test_data.empty:
            return ticker_two, "TWO"
    except:
        pass
    
    # 都失敗則返回 None
    return None, None

def run_comprehensive_analysis_for_stock(stock_code: str, stock_name: str):
    """
    對單一股票執行完整的綜合評估分析
    包含技術面、基本面、風險評估、動能分析
    """
    # 智能獲取正確的 ticker
    stock_ticker, market = get_valid_ticker(stock_code)
    
    if stock_ticker is None:
        return None
    
    try:
        # 1. 執行技術分析
        tech_data = analyze_stock_technicals(stock_ticker)
        
        if tech_data is None or tech_data.empty:
            return None

        # 2. 執行基本面分析
        fundamental_data = analyze_stock_fundamentals(stock_ticker)
        
        # 3. 計算技術評分
        from main import calculate_technical_score
        technical_score, tech_details = calculate_technical_score(tech_data)
        
        # 4. 產生交易訊號
        signal_generator = TradingSignalGenerator()
        trading_signal = signal_generator.generate_signal(tech_data, technical_score)
        
        # 5. 執行綜合評估
        evaluator = ComprehensiveEvaluator()
        
        # 獲取各維度評估結果
        fund_score, fund_result = evaluator.evaluate_fundamental_quality(fundamental_data)
        tech_score_norm, tech_result = evaluator.evaluate_technical_strength(tech_data, technical_score)
        risk_score, risk_result = evaluator.evaluate_risk_profile(tech_data, fundamental_data)
        momentum_score, momentum_result = evaluator.evaluate_momentum(tech_data)
        
        # 產生最終綜合評估
        evaluation = evaluator.generate_comprehensive_evaluation(
            tech_data=tech_data,
            tech_score=technical_score,
            fundamental_data=fundamental_data,
            trading_signal=trading_signal
        )
        
        # 獲取當前價格和重要指標
        latest = tech_data.iloc[-1]
        current_price = latest['Close']
        
        # 整理關鍵財務指標（安全處理可能為 None 的情況）
        eps = fundamental_data.get('EPS', 'N/A') if fundamental_data else 'N/A'
        roe = fundamental_data.get('ROE', 'N/A') if fundamental_data else 'N/A'
        pe_ratio = fundamental_data.get('本益比', 'N/A') if fundamental_data else 'N/A'
        debt_ratio = fundamental_data.get('負債比率', 'N/A') if fundamental_data else 'N/A'
        
        # 格式化數字顯示
        eps_str = f"{eps:.2f}" if isinstance(eps, (int, float)) else "N/A"
        roe_str = f"{roe:.1f}%" if isinstance(roe, (int, float)) else "N/A"
        pe_str = f"{pe_ratio:.1f}" if isinstance(pe_ratio, (int, float)) else "N/A"
        debt_str = f"{debt_ratio:.1f}%" if isinstance(debt_ratio, (int, float)) else "N/A"
        
        # 回傳完整的結果字典
        return {
            "代號": stock_code,
            "名稱": stock_name,
            "收盤價": f"${current_price:.2f}",
            "綜合評分": round(evaluation.overall_score, 1),
            "投資等級": evaluation.investment_grade.split()[0],  # 只取等級代號
            "技術評分": technical_score,
            "基本面評分": fund_score,
            "風險等級": evaluation.risk_level,
            "交易訊號": trading_signal.signal_type,
            "信心度": f"{trading_signal.confidence:.0f}%",
            "倉位建議": evaluation.position_suggestion,
            "持有期間": evaluation.time_horizon,
            "EPS": eps_str,
            "ROE": roe_str,
            "本益比": pe_str,
            "負債比": debt_str,
            "核心論點": evaluation.core_thesis,
            "主要優勢": " | ".join(evaluation.key_strengths[:2]),  # 只取前2個優勢
            "主要風險": " | ".join(evaluation.key_risks[:2]) if evaluation.key_risks else "風險可控"
        }
        
    except Exception as e:
        print(f"!!! 分析 {stock_code} {stock_name} 時發生錯誤: {str(e)[:100]}")
        return None

# --- 主程式執行 ---
if __name__ == "__main__":
    start_time = time.time()
    
    print("=" * 80)
    print("           💎 投資荷密斯 - 綜合投資價值掃描系統 💎")
    print("=" * 80)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"掃描股票數量: {len(STOCK_LIST)} 支")
    print("=" * 80)
    print()
    
    # 存放所有股票的分析結果
    all_results = []
    success_count = 0
    fail_count = 0

    # 遍歷股票清單
    total_stocks = len(STOCK_LIST)
    user_interrupted = False
    
    try:
        for i, (stock_code, stock_name) in enumerate(STOCK_LIST.items(), 1):
            
            print(f"[{i}/{total_stocks}] 正在分析: {stock_code} {stock_name}...", end=" ")
            
            try:
                # 對每一支股票執行完整的綜合評估
                result = run_comprehensive_analysis_for_stock(stock_code, stock_name)
                
                # 如果分析成功，將結果加入列表
                if result:
                    all_results.append(result)
                    success_count += 1
                    print(f"✓ 完成 (綜合評分: {result['綜合評分']:.1f})")
                else:
                    fail_count += 1
                    print("✗ 數據不足")
                    
            except KeyboardInterrupt:
                # 不要在這裡捕獲，讓它往外層傳遞
                raise
            except Exception as e:
                fail_count += 1
                print(f"✗ 錯誤: {str(e)[:50]}")
                continue
                
    except KeyboardInterrupt:
        user_interrupted = True
        print("\n\n" + "=" * 80)
        print("⚠️  偵測到使用者中斷 (Ctrl+C)")
        print(f"已完成 {success_count + fail_count}/{total_stocks} 支股票的分析")
        print("=" * 80)
        
        if success_count == 0:
            print("\n沒有任何成功分析的股票，無法產生報告。")
            print("程式結束。")
            exit(0)
    
    print("\n" + "=" * 80)
    print(f"掃描{'中斷' if user_interrupted else '完成'}！成功: {success_count} 支 | 失敗: {fail_count} 支")
    print("=" * 80)
    
    if user_interrupted and success_count > 0:
        print(f"\n雖然掃描被中斷，但仍有 {success_count} 支股票成功分析")
        print("正在使用已完成的數據產生報告...")
    elif not user_interrupted:
        print("\n正在進行排序與報告生成...")

    # 將結果列表轉換為 Pandas DataFrame
    results_df = pd.DataFrame(all_results)
    
    if results_df.empty:
        print("\n!!! 錯誤：沒有成功分析任何股票，無法產生報告。")
    else:
        # 根據「綜合評分」進行降序排序
        ranked_df = results_df.sort_values(by="綜合評分", ascending=False)
        
        # 選出前 200 名
        top_200_df = ranked_df.head(200)

        # --- 產生最終報告 ---
        
        # 1. 在終端機印出 Top 200 排行榜
        print("\n\n" + "=" * 100)
        print(f"           💎 投資荷密斯 Top 200 綜合投資價值排行榜 💎")
        print(f"           掃描時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        
        # 設定顯示選項
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.unicode.east_asian_width', True)
        
        # 將 DataFrame 的索引設為排名 (從 1 開始)
        top_200_df.index = range(1, len(top_200_df) + 1)
        
        # 選擇要顯示的欄位（簡化版）
        display_columns = [
            "代號", "名稱", "收盤價", "綜合評分", "投資等級", 
            "技術評分", "基本面評分", "風險等級", "交易訊號", 
            "信心度", "倉位建議"
        ]
        
        print(top_200_df[display_columns].to_string())
        
        # 2. 將完整的 Top 200 結果儲存為 CSV 檔案
        today_str = datetime.now().strftime('%Y%m%d_%H%M')
        csv_filename = f"investment_hermis_top50_{today_str}.csv"
        
        try:
            top_200_df.to_csv(csv_filename, index_label="排名", encoding='utf-8-sig')
            print(f"\n\n>>> ✓ Top 200 完整結果已成功儲存至檔案: {csv_filename}")
        except Exception as e:
            print(f"\n\n>>> ✗ 儲存 CSV 檔案失敗: {e}")
        
        # 3. 產生統計摘要
        print("\n" + "=" * 100)
        print("📊 統計摘要:")
        print(f"   • 平均綜合評分: {top_200_df['綜合評分'].mean():.1f}")
        print(f"   • 平均技術評分: {top_200_df['技術評分'].mean():.1f}")
        print(f"   • 平均基本面評分: {top_200_df['基本面評分'].mean():.1f}")
        
        # 訊號分布
        signal_counts = top_200_df['交易訊號'].value_counts()
        print(f"\n🎯 交易訊號分布:")
        for signal, count in signal_counts.items():
            print(f"   • {signal}: {count} 支 ({count/len(top_200_df)*100:.1f}%)")
        
        # 風險等級分布
        risk_counts = top_200_df['風險等級'].value_counts()
        print(f"\n⚡ 風險等級分布:")
        for risk, count in risk_counts.items():
            print(f"   • {risk}: {count} 支 ({count/len(top_200_df)*100:.1f}%)")
        
        # 投資等級分布
        grade_counts = top_200_df['投資等級'].value_counts()
        print(f"\n🏆 投資等級分布:")
        for grade, count in grade_counts.items():
            print(f"   • {grade}: {count} 支 ({count/len(top_200_df)*100:.1f}%)")
        
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print("\n" + "=" * 100)
    print(f"⏱️  總掃描耗時: {elapsed_time:.2f} 秒 (平均每支 {elapsed_time/total_stocks:.2f} 秒)")
    print("=" * 100)
    print("\n⚠️  重要提醒:")
    print("   • 本報告僅供參考，不構成投資建議")
    print("   • 投資有風險，決策前請充分了解")
    print("   • 建議配合其他資訊綜合判斷")
    print("   • 過去績效不代表未來表現")
    print("\n" + "=" * 100)
    print("分析完成！祝您投資順利！ 📈")
    print("=" * 100)