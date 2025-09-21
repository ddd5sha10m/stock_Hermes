# main.py - 完整優化版 (含交易訊號預測)

from technical_analyzer import analyze_stock_technicals
from trading_signals import TradingSignalGenerator, format_trading_signal

def check_score_signal_consistency(score: int, signal) -> dict:
    """檢查技術評分與交易訊號的一致性"""
    
    # 定義一致性規則
    if score >= 70:
        expected_signal = 'BUY'
    elif score <= 40:
        expected_signal = 'SELL'
    else:
        expected_signal = 'HOLD'
    
    is_consistent = (signal.signal_type == expected_signal)
    
    explanation = ""
    if not is_consistent:
        if score >= 60 and signal.signal_type == 'HOLD':
            explanation = f"技術評分{score}分偏多，但考慮實戰風險因素後建議觀望"
        elif score <= 50 and signal.signal_type == 'BUY':
            explanation = f"技術評分{score}分中性，但發現短期買進機會"
        elif score >= 60 and signal.signal_type == 'SELL':
            explanation = f"技術評分{score}分不錯，但檢測到反轉風險，建議賣出"
        else:
            explanation = "評分與訊號出現分歧，請特別注意風險"
    
    return {
        'is_consistent': is_consistent,
        'expected_signal': expected_signal,
        'actual_signal': signal.signal_type,
        'explanation': explanation
    }

def calculate_technical_score(data):
    """
    優化的技術分析綜合評分系統
    考慮趨勢強度、風險評估、多重確認等因素
    """
    score = 0
    total_possible_score = 100
    details = []
    
    if data is None or data.empty:
        return 0, ["技術數據不足"]
        
    latest = data.iloc[-1]
    
    # 檢查必要的指標欄位
    required_basic_cols = ['Close', 'MA20', 'MA60']
    if not all(col in latest.index for col in required_basic_cols):
        return 0, ["基礎技術指標計算失敗"]

    # --- 1. 趨勢分析 (30分) ---
    trend_score = 0
    
    # MA趨勢判斷 (考慮乖離率)
    if 'Deviation_MA60' in latest.index:
        deviation_60 = latest['Deviation_MA60']
        if deviation_60 > 0:  # 在MA60之上
            if deviation_60 <= 10:  # 健康的上升趨勢
                trend_score += 15
                details.append(f"價格在60MA之上，乖離率{deviation_60:.1f}% (+15)")
            elif deviation_60 <= 20:  # 有點過熱但還可接受
                trend_score += 10
                details.append(f"價格在60MA之上但乖離較大{deviation_60:.1f}% (+10)")
            else:  # 乖離過大，風險高
                trend_score += 5
                details.append(f"價格乖離60MA過大{deviation_60:.1f}%，回調風險 (+5)")
    
    # MA20與MA60關係
    if latest['MA20'] > latest['MA60']:
        trend_score += 10
        details.append("20MA > 60MA，中期趨勢向上 (+10)")
    
    # MA5短期趨勢
    if 'MA5' in latest.index and latest['MA5'] > latest['MA20']:
        trend_score += 5
        details.append("5MA > 20MA，短期趨勢向上 (+5)")
    
    score += trend_score

    # --- 2. 動量指標 (25分) ---
    momentum_score = 0
    
    # 改進的KD分析 (結合趨勢環境)
    if 'K' in latest.index and 'D' in latest.index:
        is_uptrend = latest['Close'] > latest['MA60']
        
        if latest['K'] > latest['D']:
            momentum_score += 5
            details.append("K > D，短期動量向上 (+5)")
        
        # 根據趨勢環境調整KD超買超賣標準
        if is_uptrend:  # 多頭趨勢
            if latest['K'] < 30:  # 強勢股回檔買點
                momentum_score += 8
                details.append("多頭趨勢中K<30，強勢回檔買點 (+8)")
            elif latest['K'] > 80:  # 多頭中超買
                momentum_score += 2
                details.append("多頭趨勢中K>80，注意短期過熱 (+2)")
        else:  # 空頭趨勢
            if latest['K'] < 20:  # 弱勢股超賣反彈
                momentum_score += 3
                details.append("空頭趨勢中K<20，超賣反彈機會 (+3)")
    
    # RSI分析
    if 'RSI' in latest.index:
        rsi = latest['RSI']
        if 30 <= rsi <= 70:  # 健康區間
            momentum_score += 5
            details.append(f"RSI={rsi:.1f}在健康區間 (+5)")
        elif rsi < 30:  # 超賣
            momentum_score += 3
            details.append(f"RSI={rsi:.1f}超賣，反彈機會 (+3)")
        elif rsi > 70:  # 超買
            momentum_score += 1
            details.append(f"RSI={rsi:.1f}超買，注意回調 (+1)")
    
    # 改進的MACD分析
    if all(col in latest.index for col in ['DIF', 'DEM']):
        if len(data) >= 5:
            dif_trend = latest['DIF'] - data.iloc[-5]['DIF']  # 5日趨勢
            
            if latest['DIF'] > latest['DEM']:
                if latest['DIF'] > 0 and dif_trend > 0:
                    momentum_score += 10
                    details.append("MACD零軸上方且加速向上 (+10)")
                elif dif_trend > 0:
                    momentum_score += 7
                    details.append("MACD金叉且上升 (+7)")
                else:
                    momentum_score += 3
                    details.append("MACD金叉但動能轉弱 (+3)")
            elif latest['DIF'] > 0 and dif_trend > 0:
                momentum_score += 5
                details.append("MACD零軸上方，等待金叉 (+5)")
    
    score += momentum_score

    # --- 3. 布林通道分析 (10分) ---
    bb_score = 0
    
    if all(col in latest.index for col in ['Close', 'BB_Upper', 'BB_Lower']):
        if len(data) >= 5:
            # 檢查突破上軌的持續性
            recent_5_days = data.tail(5)
            days_above_upper = sum(recent_5_days['Close'] > recent_5_days['BB_Upper'])
            
            if latest['Close'] > latest['BB_Upper']:
                if days_above_upper <= 2:
                    bb_score += 15
                    details.append("剛突破布林上軌，強勢訊號 (+15)")
                else:
                    bb_score += 5
                    details.append("持續在布林上軌，注意回調風險 (+5)")
            elif latest['Close'] < latest['BB_Lower']:
                bb_score -= 5
                details.append("跌破布林下軌，弱勢訊號 (-5)")
            elif 'BB_Position' in latest.index:
                bb_pos = latest['BB_Position']
                if 0.6 <= bb_pos <= 0.8:  # 在通道上半部但未突破
                    bb_score += 8
                    details.append("價格在布林通道上半部，強勢整理 (+8)")
    
    score += bb_score

    # --- 4. 成交量分析 (15分) ---
    volume_score = 0
    
    if 'Volume_Ratio' in latest.index:
        vol_ratio = latest['Volume_Ratio']
        vp_signal = latest.get('Volume_Price_Signal', '')
        
        if vp_signal == '價漲量增':
            if vol_ratio > 2.0:  # 爆量上漲
                volume_score += 15
                details.append(f"爆量上漲(量比{vol_ratio:.1f}) (+15)")
            elif vol_ratio > 1.5:  # 放量上漲
                volume_score += 12
                details.append(f"放量上漲(量比{vol_ratio:.1f}) (+12)")
            else:  # 溫和放量
                volume_score += 8
                details.append(f"溫和放量上漲(量比{vol_ratio:.1f}) (+8)")
        elif vp_signal == '價漲量縮':
            volume_score += 3
            details.append("價漲量縮，追高意願不強 (+3)")
        elif vp_signal == '價跌量增':
            volume_score -= 10
            details.append(f"價跌量增(量比{vol_ratio:.1f})，賣壓沉重 (-10)")
        elif vp_signal == '價跌量縮':
            volume_score += 5
            details.append("價跌量縮，賣壓減輕 (+5)")
    
    score += volume_score

    # --- 5. 風險評估 (扣分項目) ---
    risk_penalty = 0
    
    # 波動率風險
    if 'Volatility_Risk' in latest.index:
        vol_risk = latest['Volatility_Risk']
        if vol_risk > 8:  # 極高波動
            risk_penalty += 15
            details.append(f"極高波動率{vol_risk:.1f}% (-15)")
        elif vol_risk > 5:  # 高波動
            risk_penalty += 10
            details.append(f"高波動率{vol_risk:.1f}% (-10)")
        elif vol_risk > 3:  # 中等波動
            risk_penalty += 5
            details.append(f"中等波動率{vol_risk:.1f}% (-5)")
    
    score -= risk_penalty

    # --- 6. 交叉訊號加分 (10分) ---
    signal_bonus = 0
    
    if latest.get('Golden_Cross_KD', False):
        signal_bonus += 5
        details.append("KD黃金交叉 (+5)")
    
    if latest.get('Golden_Cross_MACD', False):
        signal_bonus += 8
        details.append("MACD黃金交叉 (+8)")
    
    if latest.get('Golden_Cross_5_20', False):
        signal_bonus += 7
        details.append("5MA突破20MA (+7)")
    
    score += signal_bonus

    # --- 7. 多空力道平衡評估 (10分) ---
    balance_score = 0
    
    if 'Bull_Bear_Balance' in latest.index:
        balance = latest['Bull_Bear_Balance']
        if balance > 0.6:
            balance_score += 10
            details.append(f"多空力道強烈偏多({balance:.2f}) (+10)")
        elif balance > 0.3:
            balance_score += 6
            details.append(f"多空力道偏多({balance:.2f}) (+6)")
        elif balance > -0.3:
            balance_score += 2
            details.append(f"多空力道均衡({balance:.2f}) (+2)")
        else:
            balance_score -= 5
            details.append(f"多空力道偏空({balance:.2f}) (-5)")
    
    score += balance_score

    # --- 8. 趨勢強度調整 (ADX) ---
    if 'ADX_14' in latest.index:
        adx = latest['ADX_14']
        if adx > 25:  # 強趨勢
            if score > 60:  # 在強趨勢中的強勢股
                trend_strength_bonus = int(score * 0.1)
                score += trend_strength_bonus
                details.append(f"強趨勢環境(ADX={adx:.1f})加成 (+{trend_strength_bonus})")
        elif adx < 20:  # 震盪行情
            if score > 50:  # 在震盪中評分仍高，需要謹慎
                consolidation_penalty = int(score * 0.05)
                score -= consolidation_penalty
                details.append(f"震盪行情(ADX={adx:.1f})減分 (-{consolidation_penalty})")

    # 確保分數在合理範圍內
    score = max(0, min(score, total_possible_score))
    
    return score, details

def generate_investment_advice(score, details, data):
    """根據評分生成投資建議"""
    latest = data.iloc[-1]
    advice = []
    
    if score >= 80:
        advice.append("🔥 強烈買入訊號")
        advice.append("多項技術指標呈現強勢突破態勢")
        if 'Volatility_Risk' in latest.index and latest['Volatility_Risk'] > 5:
            advice.append("⚠️ 但請注意波動風險，建議分批進場")
    elif score >= 65:
        advice.append("📈 買入訊號")
        advice.append("技術面整體偏多，可考慮進場")
        advice.append("建議設定停損點並控制倉位")
    elif score >= 50:
        advice.append("⚖️ 中性偏多")
        advice.append("技術面呈現整理態勢，可等待更明確訊號")
        advice.append("適合有經驗的投資者小幅參與")
    elif score >= 35:
        advice.append("📉 中性偏空")
        advice.append("技術面偏弱，建議觀望")
        advice.append("如有持股可考慮減碼")
    else:
        advice.append("🚨 賣出訊號")
        advice.append("多項技術指標呈現弱勢，建議避開")
        advice.append("如有持股建議盡快出場")
    
    # 風險提醒
    if 'Volatility_Risk' in latest.index:
        vol_risk = latest['Volatility_Risk']
        if vol_risk > 8:
            advice.append("⚠️ 極高風險：該股波動率極大，請謹慎操作")
        elif vol_risk > 5:
            advice.append("⚠️ 高風險：該股波動較大，請控制倉位")
    
    return advice

# --- 主程式執行 ---
if __name__ == "__main__":
    STOCK_MAP = {
        "2330": "台積電", "2317": "鴻海", "2454": "聯發科", "2308": "台達電",
        "2382": "廣達", "2881": "富邦金", "2891": "中信金", "2882": "國泰金",
        "2357": "華碩", "3231": "緯創", "2412": "中華電", "1301": "台塑",
        "1303": "南亞", "2002": "中鋼", "2886": "兆豐金", "2603": "長榮"
    }

    # 可以修改這個股票代碼來測試不同股票
    stock_code = "2412"
    stock_ticker = f"{stock_code}.TW"
    stock_name = STOCK_MAP.get(stock_code, stock_code)
    


    print(f"開始分析股票: {stock_code} {stock_name}")
    print("="*60)
    print("\n--- 技術指標說明 ---")
    print("乖離率：衡量股價與均線的差距。偏低=可能超跌，偏高=可能超漲。")
    print("KD線：衡量相對高低點。偏低(<20)=超賣，偏高(>80)=超買。")
    print("RSI：強弱指標。偏低(<30)=超賣，偏高(>70)=超買。")
    print("MACD：快線-慢線動能。偏低=動能弱，偏高=動能強；黃金交叉=偏多，死亡交叉=偏空。")
    print("ATR：波動指標。偏低=盤整，偏高=波動劇烈。")
    print("ADX：趨勢強度。偏低(<20)=盤整，偏高(>25)=趨勢明顯。")
    print("布林通道：通道上軌/下軌。偏低=超賣，偏高=超買；收窄=大行情將至，擴張=波動加劇。")
    print("量價關係：量與價互動。價漲量增=多頭強，價跌量增=空頭強；價漲量縮=上漲無力。")
    print("OBV：量能累積。偏低=空方力道強，偏高=多方力道強。")
    print("波動率：股價變動幅度。偏低=市場穩定，偏高=市場劇烈波動。")
    print("="*60+"\n")
    # 執行技術分析
    tech_data = analyze_stock_technicals(stock_ticker)
    
    if tech_data is not None and not tech_data.empty:
        # 計算綜合評分
        technical_score, scoring_details = calculate_technical_score(tech_data)
        
        # 生成投資建議
        investment_advice = generate_investment_advice(technical_score, scoring_details, tech_data)
        
        # 🎯 生成交易訊號預測
        signal_generator = TradingSignalGenerator()
        trading_signal = signal_generator.generate_signal(tech_data, technical_score)
        
        # 🔍 一致性檢查 - 偵測評分與訊號的矛盾
        consistency_check = check_score_signal_consistency(technical_score, trading_signal)
        
        # --- 產生詳細報告 ---
        print("\n" + "="*60)
        print(f"      投資跟密斯 - 完整技術分析報告")
        print(f"      股票代號: {stock_code} {stock_name}")
        print("="*60)
        
        print(f"\n📊 技術面綜合評分: {technical_score} / 100")
        
        # 評分等級
        if technical_score >= 80:
            grade = "A+ (極佳)"
        elif technical_score >= 70:
            grade = "A  (優秀)"
        elif technical_score >= 60:
            grade = "B+ (良好)"
        elif technical_score >= 50:
            grade = "B  (中性偏多)"
        elif technical_score >= 40:
            grade = "C+ (中性偏空)"
        elif technical_score >= 30:
            grade = "C  (較弱)"
        else:
            grade = "D  (弱勢)"
        
        print(f"📈 技術等級: {grade}")
        
        # 最新價格資訊
        latest = tech_data.iloc[-1]
        print(f"\n💰 最新收盤價: ${latest['Close']:.2f}")
        
        if 'Support_Level' in latest.index and 'Resistance_Level' in latest.index:
            print(f"📍 支撐位: ${latest['Support_Level']:.2f}")
            print(f"📍 壓力位: ${latest['Resistance_Level']:.2f}")
        
        if 'Volatility_Risk' in latest.index:
            print(f"⚡ 波動率風險: {latest['Volatility_Risk']:.2f}%")
        
        print("\n--- 📋 評分詳細說明 ---")
        for i, detail in enumerate(scoring_details, 1):
            print(f"  {i:2d}. {detail}")
        
        print("\n--- 💡 投資建議 ---")
        for i, advice in enumerate(investment_advice, 1):
            print(f"  {i}. {advice}")
        
        print("\n--- ⚠️ 風險提醒 ---")
        print("  • 本分析僅供參考，投資前請做好功課")
        print("  • 技術分析無法預測所有市場變化")
        print("  • 請根據個人風險承受度調整投資策略")
        print("  • 建議搭配基本面分析做出最終決策")
        
        # 🔍 顯示一致性檢查結果
        if not consistency_check['is_consistent']:
            print(f"\n--- 🤔 評分訊號分析 ---")
            print(f"  技術評分: {technical_score}分 → 預期訊號: {consistency_check['expected_signal']}")
            print(f"  實際訊號: {consistency_check['actual_signal']}")
            print(f"  說明: {consistency_check['explanation']}")
            print("  💡 建議: 當評分與訊號不一致時，以交易訊號為準，因為它考慮了更多實戰因素")
        
        print("\n" + "="*60)
        print("分析完成！祝您投資順利！ 🚀")
        print("="*60)
        
        # 🎯 顯示交易訊號預測
        print("\n")
        print(format_trading_signal(trading_signal, stock_code, stock_name))
        
    else:
        print(f"❌ 無法獲取 {stock_code} 的技術資料，程式終止。")
        print("可能原因：")
        print("  1. 網路連線問題")
        print("  2. 股票代碼錯誤")
        print("  3. 該股票暫停交易")