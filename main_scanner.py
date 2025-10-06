# main_scanner.py - 完整版投資荷密斯掃描系統

import pandas as pd
from datetime import datetime
import time
import multiprocessing as mp
from functools import partial
import math
import os
from tqdm import tqdm
import logging
import traceback

# 從我們自訂的模組中，匯入所有需要的類別、函式和資料
from market_analyzer import get_market_state
from chip_analyzer import get_institutional_trades
from stock_list import STOCK_LIST
from technical_analyzer import analyze_stock_technicals
from fundamental_analyzer import analyze_stock_fundamentals
from trading_signals import TradingSignalGenerator
from comprehensive_evaluator import ComprehensiveEvaluator

# ===== 批次處理配置 =====
BATCH_SIZE = 300  # 減小批次大小以避免資源耗盡
REST_BETWEEN_BATCHES = 30  # 批次間休息時間
MAX_RETRIES = 2  # 最大重試次數
# =========================

def setup_logging():
    """設置日誌記錄"""
    log_filename = f'scanner_log_{datetime.now().strftime("%Y%m%d_%H%M")}.txt'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return log_filename

def get_valid_ticker(stock_code: str):
    """獲取有效的股票ticker"""
    import yfinance as yf
    tickers_to_try = [f"{stock_code}.TW", f"{stock_code}.TWO"]
    for ticker in tickers_to_try:
        try:
            ticker_obj = yf.Ticker(ticker)
            # 嘗試獲取基本信息來驗證ticker是否有效
            info = ticker_obj.info
            if info.get('regularMarketPrice') is not None:
                return ticker
            # 如果無法獲取價格，嘗試檢查歷史數據
            hist = ticker_obj.history(period="1d")
            if not hist.empty:
                return ticker
        except Exception:
            continue
    return None

def run_comprehensive_analysis_for_stock(args):
    """
    對單一股票執行完整的綜合評估分析
    """
    stock_item, market_state, chip_data_for_stock = args
    stock_code, stock_name = stock_item
    
    try:
        import yfinance as yf
        
        stock_ticker = get_valid_ticker(stock_code)
        if stock_ticker is None: 
            return {"error": f"無效ticker", "代號": stock_code, "名稱": stock_name}

        # 1. 獲取原始數據
        ticker_obj = yf.Ticker(stock_ticker)
        
        # 技術分析
        tech_data = analyze_stock_technicals(ticker_obj)
        if tech_data is None or tech_data.empty or len(tech_data) < 20: 
            return {"error": "技術資料不足", "代號": stock_code, "名稱": stock_name}
        
        # 基本面分析
        fundamental_data = analyze_stock_fundamentals(ticker_obj)
        if fundamental_data is None:
            fundamental_data = {}  # 使用空字典而不是None
        
        # 2. 建立評估器與訊號產生器
        evaluator = ComprehensiveEvaluator()
        signal_generator = TradingSignalGenerator()
        
        # 3. 取得技術分數
        technical_score, tech_result = evaluator.evaluate_technical_strength(tech_data)
        
        # 4. 產生交易訊號
        trading_signal = signal_generator.generate_signal(tech_data, technical_score, market_state)
        
        # 5. 取得其他評估結果
        fund_score, fund_result = evaluator.evaluate_fundamental_quality(fundamental_data)
        risk_score, risk_result = evaluator.evaluate_risk_profile(tech_data, fundamental_data)
        momentum_score, momentum_result = evaluator.evaluate_momentum(tech_data)
        
        # 處理籌碼數據
        chip_score = 50  # 預設中性分數
        chip_result = {'score': 50, 'grade': '中性', 'details': ['籌碼數據不足']}
        if chip_data_for_stock is not None and not chip_data_for_stock.empty:
            try:
                chip_score, chip_result = evaluator.evaluate_chip_flow(chip_data_for_stock)
            except Exception as e:
                logging.warning(f"籌碼分析失敗 {stock_code}: {e}")
        
        # 6. 產生最終評估
        evaluation = evaluator.generate_comprehensive_evaluation(
            tech_data=tech_data,
            tech_score=technical_score,
            fundamental_data=fundamental_data,
            trading_signal=trading_signal,
            market_state=market_state,
            chip_data=chip_data_for_stock
        )
        
        # 7. 整理回傳結果
        latest = tech_data.iloc[-1]
        current_price = latest['Close']
        
        return {
            "代號": stock_code, 
            "名稱": stock_name, 
            "收盤價": f"${current_price:.2f}",
            "綜合評分": evaluation.overall_score,
            "投資等級": evaluation.investment_grade.split()[0],
            "技術評分": technical_score, 
            "基本面評分": fund_score, 
            "籌碼評分": chip_score,
            "風險等級": evaluation.risk_level, 
            "交易訊號": trading_signal.signal_type,
            "信心度": f"{trading_signal.confidence:.0f}%", 
            "倉位建議": evaluation.position_suggestion,
            "核心論點": evaluation.core_thesis[:50] + "..." if len(evaluation.core_thesis) > 50 else evaluation.core_thesis,
            "狀態": "成功"
        }
        
    except Exception as e:
        error_msg = f"{str(e)[:80]}..." if len(str(e)) > 80 else str(e)
        return {
            "error": error_msg, 
            "代號": stock_code, 
            "名稱": stock_name,
            "狀態": "失敗"
        }

def process_batch(batch_items, batch_num, total_batches, num_processes, market_state: str, chip_data_df: pd.DataFrame):
    """處理單一批次的股票"""
    print(f"\n{'='*80}")
    print(f"批次 {batch_num}/{total_batches}: 處理 {len(batch_items)} 支股票 (大盤: {market_state})")
    print(f"{'='*80}\n")
    
    batch_results = []
    tasks = []
    
    for item in batch_items:
        stock_code, stock_name = item
        single_stock_chip_data = None
        
        # 安全地獲取籌碼數據
        if chip_data_df is not None and not chip_data_df.empty:
            try:
                if stock_code in chip_data_df.index.get_level_values(1):
                    single_stock_chip_data = chip_data_df.loc[(slice(None), stock_code), :]
            except Exception as e:
                logging.warning(f"獲取 {stock_code} 籌碼數據時出錯: {e}")
        
        tasks.append((item, market_state, single_stock_chip_data))
    
    try:
        with mp.Pool(processes=num_processes) as pool:
            for result in tqdm(pool.imap_unordered(run_comprehensive_analysis_for_stock, tasks), 
                             total=len(tasks), desc=f"批次 {batch_num} 進度"):
                if result is not None:
                    batch_results.append(result)
            
            pool.close()
            pool.join()
            
    except Exception as e:
        print(f"批次處理發生嚴重錯誤: {e}")
        logging.error(f"批次 {batch_num} 處理失敗: {e}")
        # 如果多進程失敗，嘗試單進程處理
        print("嘗試單進程處理...")
        for task in tasks:
            try:
                result = run_comprehensive_analysis_for_stock(task)
                if result is not None:
                    batch_results.append(result)
            except Exception as single_e:
                logging.error(f"單進程處理失敗: {single_e}")
    
    return batch_results

def generate_detailed_report(results_df, market_state):
    """生成詳細分析報告"""
    
    if results_df.empty:
        print("\n!!! 沒有成功分析的股票，無法產生報告。")
        return
    
    # 按評分排序
    ranked_df = results_df.sort_values(by="綜合評分", ascending=False)
    top_df = ranked_df.head(200)
    
    print("\n\n" + "="*120)
    print(f"           💎 投資荷密斯 Top 200 綜合投資價值排行榜 💎")
    print(f"           掃描時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"           大盤狀態: {market_state}")
    print("="*120)
    
    # 設定顯示選項
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)
    pd.set_option('display.unicode.east_asian_width', True)
    
    top_df.index = range(1, len(top_df) + 1)
    
    # 完整的顯示欄位
    display_columns = [
        "代號", "名稱", "收盤價", "綜合評分", "投資等級", 
        "技術評分", "基本面評分", "籌碼評分",
        "風險等級", "交易訊號", "信心度", "倉位建議"
    ]
    
    print(top_df[display_columns].to_string())
    
    # 生成統計摘要
    generate_statistics_summary(top_df, results_df)

def generate_statistics_summary(top_df, all_results_df):
    """生成統計摘要"""
    print("\n\n" + "="*80)
    print("📊 掃描結果統計摘要")
    print("="*80)
    
    total_stocks = len(all_results_df)
    
    # 訊號分布
    if '交易訊號' in all_results_df.columns:
        signal_counts = all_results_df['交易訊號'].value_counts()
        print(f"\n🎯 交易訊號分布:")
        for signal, count in signal_counts.items():
            percentage = (count / total_stocks) * 100
            print(f"   {signal}: {count} 支 ({percentage:.1f}%)")
    
    # 評分分布
    print(f"\n📈 評分區間分布:")
    score_ranges = {
        "A+ (90-100)": len(all_results_df[all_results_df['綜合評分'] >= 90]),
        "A (80-89)": len(all_results_df[(all_results_df['綜合評分'] >= 80) & (all_results_df['綜合評分'] < 90)]),
        "B+ (70-79)": len(all_results_df[(all_results_df['綜合評分'] >= 70) & (all_results_df['綜合評分'] < 80)]),
        "B (60-69)": len(all_results_df[(all_results_df['綜合評分'] >= 60) & (all_results_df['綜合評分'] < 70)]),
        "C (50-59)": len(all_results_df[(all_results_df['綜合評分'] >= 50) & (all_results_df['綜合評分'] < 60)]),
        "D (<50)": len(all_results_df[all_results_df['綜合評分'] < 50])
    }
    
    for range_name, count in score_ranges.items():
        percentage = (count / total_stocks) * 100
        print(f"   {range_name}: {count} 支 ({percentage:.1f}%)")
    
    # 風險等級分布
    if '風險等級' in all_results_df.columns:
        risk_counts = all_results_df['風險等級'].value_counts()
        print(f"\n⚠️  風險等級分布:")
        for risk, count in risk_counts.items():
            percentage = (count / total_stocks) * 100
            print(f"   {risk}: {count} 支 ({percentage:.1f}%)")
    
    # Top 10 推薦
    print(f"\n🏆 Top 10 推薦標的:")
    top_10 = top_df.head(10)
    for idx, (_, row) in enumerate(top_10.iterrows(), 1):
        print(f"   {idx:2d}. {row['代號']} {row['名稱']} - 評分: {row['綜合評分']} | 訊號: {row['交易訊號']} | 風險: {row['風險等級']}")

def print_start_info(total_stocks, market_state, num_processes, cpu_count, total_batches):
    """打印開始信息"""
    print("="*80)
    print("           💎 投資荷密斯 - 綜合投資價值掃描系統 💎")
    print("="*80)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"掃描股票數量: {total_stocks} 支")
    print(f"當前大盤狀態: {market_state}")
    print(f"使用並行進程數: {num_processes} / {cpu_count}")
    print(f"批次大小: {BATCH_SIZE} 支 | 總批次數: {total_batches} 批")
    print(f"批次間隔休息: {REST_BETWEEN_BATCHES} 秒")
    print("="*80)

def process_all_batches(batches, num_processes, market_state, chip_data_df):
    """處理所有批次"""
    all_results = []
    success_count = 0
    user_interrupted = False
    
    for batch_num, batch in enumerate(batches, 1):
        try:
            batch_start_time = time.time()
            batch_results = process_batch(batch, batch_num, len(batches), num_processes, market_state, chip_data_df)
            
            # 統計成功和失敗的結果
            successful_results = [r for r in batch_results if "狀態" in r and r["狀態"] == "成功"]
            failed_results = [r for r in batch_results if "狀態" in r and r["狀態"] == "失敗"]
            
            all_results.extend(successful_results)
            success_in_batch = len(successful_results)
            success_count += success_in_batch
            
            batch_time = time.time() - batch_start_time
            print(f"\n✓ 批次 {batch_num} 完成: 成功 {success_in_batch}/{len(batch)} 支 (耗時: {batch_time:.1f}秒)")
            
            if failed_results:
                print(f"  失敗 {len(failed_results)} 支，常見錯誤:")
                error_counts = {}
                for result in failed_results:
                    error_msg = result.get("error", "未知錯誤")
                    error_counts[error_msg] = error_counts.get(error_msg, 0) + 1
                
                for error, count in list(error_counts.items())[:3]:  # 只顯示前3個常見錯誤
                    print(f"    - {error}: {count}次")
            
            # 批次間休息（除了最後一批）
            if batch_num < len(batches):
                print(f"\n⏳ 休息 {REST_BETWEEN_BATCHES} 秒以避免速率限制... (可按 Ctrl+C 中斷)")
                time.sleep(REST_BETWEEN_BATCHES)
                
        except KeyboardInterrupt:
            user_interrupted = True
            print(f"\n\n⚠️ 使用者在批次 {batch_num} 中斷程序")
            break
        except Exception as e:
            print(f"\n❌ 批次 {batch_num} 處理異常: {e}")
            logging.error(f"批次 {batch_num} 異常: {e}")
            continue
    
    return all_results

def generate_final_report(all_results, market_state, start_time):
    """生成最終報告"""
    if not all_results:
        print("\n!!! 本次掃描未成功分析任何股票，無法產生報告。")
        return
    
    # 轉換為DataFrame
    results_df = pd.DataFrame(all_results)
    
    # 生成詳細報告
    generate_detailed_report(results_df, market_state)
    
    # 儲存結果
    today_str = datetime.now().strftime('%Y%m%d_%H%M')
    
    try:
        # 儲存完整結果
        csv_filename = f"investment_hermis_complete_{today_str}.csv"
        results_df.to_csv(csv_filename, index_label="原始序號", encoding='utf-8-sig')
        print(f"\n\n>>> ✓ 完整掃描結果已儲存至: {csv_filename}")
        
        # 同時儲存 Top 200
        top_200_df = results_df.sort_values(by="綜合評分", ascending=False).head(200)
        top_200_filename = f"investment_hermis_top200_{today_str}.csv"
        top_200_df.to_csv(top_200_filename, index_label="排名", encoding='utf-8-sig')
        print(f">>> ✓ Top 200 結果已儲存至: {top_200_filename}")
        
    except Exception as e:
        print(f"\n\n>>> ✗ 儲存 CSV 檔案失敗: {e}")
        logging.error(f"儲存CSV失敗: {e}")
    
    # 計算總耗時
    end_time = time.time()
    elapsed_time = end_time - start_time
    print("\n" + "="*100)
    print(f"⏱️  總掃描耗時: {elapsed_time:.2f} 秒 ({elapsed_time/60:.1f} 分鐘)")
    print(f"📊 成功分析: {len(results_df)} 支股票")
    print("="*100)

# --- 主程式執行 ---
if __name__ == "__main__":
    # 設置日誌
    log_filename = setup_logging()
    print(f"日誌檔案: {log_filename}")
    
    start_time = time.time()
    
    try:
        # 1. 執行一次性的市場數據抓取
        print("🔄 獲取市場數據...")
        market_state = get_market_state()
        chip_data_df = get_institutional_trades(days_to_fetch=3)  # 減少天數以加快速度
        
        # 2. 設定多進程與批次參數
        cpu_count = mp.cpu_count()
        num_processes = max(1, int(cpu_count * 0.7))  # 使用70%的CPU核心
        stock_items = list(STOCK_LIST.items())
        total_stocks = len(stock_items)
        batches = [stock_items[i:i + BATCH_SIZE] for i in range(0, total_stocks, BATCH_SIZE)]
        total_batches = len(batches)
        
        # 3. 顯示開始資訊
        print_start_info(total_stocks, market_state, num_processes, cpu_count, total_batches)
        
        # 4. 逐批執行分析
        all_results = process_all_batches(batches, num_processes, market_state, chip_data_df)
        
        # 5. 生成最終報告
        generate_final_report(all_results, market_state, start_time)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 使用者中斷掃描程序")
        logging.info("程式被使用者中斷")
    except Exception as e:
        print(f"\n\n❌ 掃描程序發生嚴重錯誤: {e}")
        logging.error(f"主程序錯誤: {e}")
        logging.error(traceback.format_exc())
    finally:
        print(f"\n🎉 掃描程序完成！詳細日誌請查看: {log_filename}")