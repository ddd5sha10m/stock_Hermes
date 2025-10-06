# fundamental_analyzer.py - 股票基本面分析器

import yfinance as yf
import pandas as pd

def analyze_stock_fundamentals(ticker_obj):
    """
    抓取並計算指定股票的13項關鍵基本面指標
    """
    print(f"===== 開始分析 {ticker_obj} 的基本面數據... =====")
    
    try:
        
        # 獲取不同類型的財報數據
        info = ticker_obj.info
        financials = ticker_obj.financials
        balance_sheet = ticker_obj.balance_sheet
        cashflow = ticker_obj.cashflow
        
        if financials.empty or balance_sheet.empty or cashflow.empty:
            print(f"警告：{ticker_obj} 的財報數據不完整，無法進行基本面分析。")
            return None

        # --- 數據提取 (以最新的年度財報為主) ---
        last_financials = financials.iloc[:, 0]
        prev_financials = financials.iloc[:, 1] if financials.shape[1] > 1 else None
        last_balance_sheet = balance_sheet.iloc[:, 0]
        last_cashflow = cashflow.iloc[:, 0]

        # --- 開始計算 13 項指標 ---
        
        # 1. EPS (每股盈餘) - 直接從 info 獲取 TTM (近12個月)
        eps = info.get('trailingEps', 0)
        
        # 2. 毛利率 (Gross Margin)
        gross_profit = last_financials.get('Gross Profit', 0)
        total_revenue = last_financials.get('Total Revenue', 0)
        gross_margin = (gross_profit / total_revenue) * 100 if total_revenue else 0
        
        # 3. 營業利益率 (Operating Margin)
        operating_income = last_financials.get('Operating Income', 0)
        operating_margin = (operating_income / total_revenue) * 100 if total_revenue else 0
        
        # 4. 淨利率 (Net Margin)
        net_income = last_financials.get('Net Income', 0)
        net_margin = (net_income / total_revenue) * 100 if total_revenue else 0
        
        # 5. ROE (股東權益報酬率) - 直接從 info 獲取
        roe = info.get('returnOnEquity', 0) * 100
        
        # 6. ROA (資產報酬率) - 直接從 info 獲取
        roa = info.get('returnOnAssets', 0) * 100
        
        # 7. 營收成長率 (Revenue Growth Rate)
        revenue_growth = 0
        if prev_financials is not None:
            prev_revenue = prev_financials.get('Total Revenue', 0)
            if prev_revenue:
                revenue_growth = ((total_revenue - prev_revenue) / prev_revenue) * 100

        # 8. 股利發放率 (Dividend Payout Ratio) - 直接從 info 獲取
        payout_ratio = info.get('payoutRatio', 0) * 100
        
        # 9. 自由現金流 (Free Cash Flow) - 直接從 info 獲取
        free_cash_flow = info.get('freeCashflow', 0)
        
        # 10. 本益比 (P/E Ratio) - 直接從 info 獲取
        pe_ratio = info.get('trailingPE', 0)
        
        # 11. 負債比率 (Debt Ratio)
        total_liabilities = last_balance_sheet.get('Total Liab', 0)
        total_assets = last_balance_sheet.get('Total Assets', 0)
        debt_ratio = (total_liabilities / total_assets) * 100 if total_assets else 0
        
        # 12. 流動比率 (Current Ratio)
        current_assets = last_balance_sheet.get('Total Current Assets', 0)
        current_liabilities = last_balance_sheet.get('Total Current Liabilities', 0)
        current_ratio = current_assets / current_liabilities if current_liabilities else 0
        
        # 13. 速動比率 (Quick Ratio)
        inventory = last_balance_sheet.get('Inventory', 0)
        quick_ratio = (current_assets - inventory) / current_liabilities if current_liabilities else 0
        
        print(f"===== {ticker_obj} 基本面數據分析完成！ =====")

        return {
            "EPS": eps,
            "毛利率": gross_margin,
            "營業利益率": operating_margin,
            "淨利率": net_margin,
            "ROE": roe,
            "ROA": roa,
            "營收成長率": revenue_growth,
            "股利發放率": payout_ratio,
            "自由現金流": free_cash_flow,
            "本益比": pe_ratio,
            "負債比率": debt_ratio,
            "流動比率": current_ratio,
            "速動比率": quick_ratio,
        }
        
    except Exception as e:
        print(f"錯誤：分析 {ticker_obj} 基本面時發生錯誤: {e}")
        return None