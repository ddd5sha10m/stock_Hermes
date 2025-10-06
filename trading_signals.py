# trading_signals.py - 交易訊號預測系統

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Tuple

@dataclass
class TradingSignal:
    """交易訊號資料結構"""
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 信心度 0-100
    entry_price: float  # 建議進場價
    stop_loss: float   # 停損價
    take_profit: List[float]  # 分批獲利了結價位
    risk_reward_ratio: float  # 風險報酬比
    holding_period: str  # 建議持有期間
    reasons: List[str]  # 訊號理由
    warnings: List[str]  # 風險警告

class TradingSignalGenerator:
    """交易訊號產生器"""
    
    def __init__(self):
        self.min_confidence_threshold = 60  # 最低信心度門檻
        
    def calculate_support_resistance(self, data: pd.DataFrame, window: int = 20) -> Tuple[float, float, List[float], List[float]]:
        """計算動態支撐壓力位"""
        if len(data) < window:
            return None, None, [], []
            
        recent_data = data.tail(window * 2)  # 取更多數據來分析
        
        # 尋找局部高低點
        highs = []
        lows = []
        
        for i in range(5, len(recent_data) - 5):
            # 檢查是否為局部高點
            if all(recent_data['High'].iloc[i] >= recent_data['High'].iloc[i-j] for j in range(1, 6)) and \
               all(recent_data['High'].iloc[i] >= recent_data['High'].iloc[i+j] for j in range(1, 6)):
                highs.append(recent_data['High'].iloc[i])
            
            # 檢查是否為局部低點
            if all(recent_data['Low'].iloc[i] <= recent_data['Low'].iloc[i-j] for j in range(1, 6)) and \
               all(recent_data['Low'].iloc[i] <= recent_data['Low'].iloc[i+j] for j in range(1, 6)):
                lows.append(recent_data['Low'].iloc[i])
        
        # 計算關鍵支撐壓力
        current_price = data['Close'].iloc[-1]
        
        # 找出最接近當前價格的支撐壓力
        resistance_levels = [h for h in highs if h > current_price]
        support_levels = [l for l in lows if l < current_price]
        
        resistance = min(resistance_levels) if resistance_levels else current_price * 1.1
        support = max(support_levels) if support_levels else current_price * 0.9
        
        return support, resistance, support_levels, resistance_levels
    
    def calculate_atr_stops(self, data: pd.DataFrame, multiplier: float = 2.0) -> Tuple[float, float]:
        """基於ATR計算動態停損停利"""
        if 'ATR' not in data.columns or len(data) < 2:
            return None, None
            
        latest = data.iloc[-1]
        atr = latest['ATR']
        current_price = latest['Close']
        
        # 動態停損 (ATR的2倍)
        stop_loss = current_price - (atr * multiplier)
        
        # 動態停利 (ATR的3-4倍，分批出場)
        take_profit_1 = current_price + (atr * 3)
        take_profit_2 = current_price + (atr * 5)
        take_profit_3 = current_price + (atr * 7)
        
        return stop_loss, [take_profit_1, take_profit_2, take_profit_3]
    
    def analyze_volume_profile(self, data: pd.DataFrame, window: int = 20) -> Dict:
        """分析成交量特徵"""
        if 'Volume_Ratio' not in data.columns:
            return {}
            
        recent_data = data.tail(window)
        latest = data.iloc[-1]
        
        avg_volume_ratio = recent_data['Volume_Ratio'].mean()
        volume_trend = recent_data['Volume_Ratio'].rolling(5).mean().diff().iloc[-1]
        
        return {
            'current_volume_ratio': latest['Volume_Ratio'],
            'avg_volume_ratio': avg_volume_ratio,
            'volume_trend': volume_trend,
            'is_volume_surge': latest['Volume_Ratio'] > 2.0,
            'is_volume_drying': latest['Volume_Ratio'] < 0.5
        }
    
    def detect_chart_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """識別圖表型態"""
        patterns = []
        
        if len(data) < 20:
            return patterns
            
        recent_data = data.tail(20)
        closes = recent_data['Close'].values
        
        # 檢測雙底型態
        if self._is_double_bottom(closes):
            patterns.append({
                'pattern': '雙底',
                'signal': 'BUY',
                'confidence': 70,
                'description': '價格形成雙底型態，可能反轉向上'
            })
        
        # 檢測頭肩頂
        if self._is_head_shoulders(closes):
            patterns.append({
                'pattern': '頭肩頂',
                'signal': 'SELL',
                'confidence': 75,
                'description': '價格形成頭肩頂型態，可能反轉向下'
            })
        
        # 檢測上升三角形
        if self._is_ascending_triangle(recent_data):
            patterns.append({
                'pattern': '上升三角形',
                'signal': 'BUY',
                'confidence': 65,
                'description': '價格形成上升三角形，突破後看漲'
            })
        
        return patterns
    
    def _is_double_bottom(self, prices: np.array) -> bool:
        """檢測雙底型態"""
        if len(prices) < 15:
            return False
            
        # 簡化的雙底檢測邏輯
        min_idx = np.argmin(prices[:10])
        min_idx2 = np.argmin(prices[10:]) + 10
        
        if abs(prices[min_idx] - prices[min_idx2]) < prices[min_idx] * 0.05:  # 兩個底部價差小於5%
            if min_idx2 - min_idx > 5:  # 兩個底部間隔足夠
                return True
        return False
    
    def _is_head_shoulders(self, prices: np.array) -> bool:
        """檢測頭肩頂型態"""
        if len(prices) < 15:
            return False
            
        # 簡化的頭肩頂檢測邏輯
        max_idx = np.argmax(prices[5:15]) + 5  # 頭部
        left_shoulder = np.argmax(prices[:max_idx])
        right_shoulder = np.argmax(prices[max_idx:]) + max_idx
        
        if prices[left_shoulder] > prices[0] and prices[right_shoulder] > prices[-1]:
            if prices[max_idx] > prices[left_shoulder] and prices[max_idx] > prices[right_shoulder]:
                return True
        return False
    
    def _is_ascending_triangle(self, data: pd.DataFrame) -> bool:
        """檢測上升三角形"""
        highs = data['High'].values
        lows = data['Low'].values
        
        # 檢查高點是否持平（阻力線）
        recent_highs = highs[-10:]
        high_resistance = np.std(recent_highs) < np.mean(recent_highs) * 0.02
        
        # 檢查低點是否上升（上升支撐線）
        recent_lows = lows[-10:]
        low_trend = np.polyfit(range(len(recent_lows)), recent_lows, 1)[0]
        
        return high_resistance and low_trend > 0
    
    def generate_signal(self, data: pd.DataFrame, current_score: int, market_state: str) -> TradingSignal:
        """生成主要交易訊號"""
        latest = data.iloc[-1]
        current_price = latest['Close']
        
        # 初始化變數
        confidence = current_score  # 🔥 直接以技術評分為基礎信心度
        signal_type = 'HOLD'
        reasons = []
        warnings = []
        
        # --- 1. 基於技術分數的基礎判斷 (調整門檻) ---
        if current_score >= 65:  # 降低買入門檻
            signal_type = 'BUY'
            reasons.append(f"技術綜合評分達{current_score}分，多項指標看好")
        elif current_score <= 40:  # 提高賣出門檻
            signal_type = 'SELL' 
            confidence = min(100 - current_score, 85)
            reasons.append(f"技術綜合評分僅{current_score}分，多項指標看壞")
        else:
            signal_type = 'HOLD'
            reasons.append(f"技術評分{current_score}分，訊號不夠明確，建議觀望")
        if market_state == "空頭" and signal_type == "BUY":
            signal_type = "HOLD" # 在空頭市場中，將買入訊號降級為觀望
            reasons.append("⚠️ 大盤處於空頭趨勢，暫緩買入")
            warnings.append("大盤逆風，逆勢操作風險較高")
            confidence -= 20 # 大幅降低信心度
        elif market_state == "多頭" and signal_type == "BUY":
            reasons.append("👍 大盤處於多頭趨勢，順勢操作")
            confidence += 10 # 順風時增加信心度

        
        # --- 2. 支撐壓力位分析 ---
        support, resistance, support_levels, resistance_levels = self.calculate_support_resistance(data)
        
        if support and resistance:
            price_position = (current_price - support) / (resistance - support)
            
            if signal_type == 'BUY':
                if price_position < 0.3:  # 接近支撐
                    confidence += 10
                    reasons.append("價格接近重要支撐位，風險有限")
                elif price_position > 0.8:  # 接近壓力
                    confidence -= 15
                    warnings.append("價格接近壓力位，突破風險較高")
            
            elif signal_type == 'SELL':
                if price_position > 0.7:  # 接近壓力
                    confidence += 10
                    reasons.append("價格接近重要壓力位，下跌機率高")
        
        # --- 3. 成交量確認 ---
        volume_analysis = self.analyze_volume_profile(data)
        
        if signal_type == 'BUY' and volume_analysis:
            if volume_analysis.get('is_volume_surge', False):
                confidence += 15
                reasons.append("爆量突破，資金積極進場")
            elif volume_analysis.get('current_volume_ratio', 1) < 0.8:
                confidence -= 10
                warnings.append("成交量偏低，突破力道不足")
        
        # --- 4. 圖表型態確認 ---
        patterns = self.detect_chart_patterns(data)
        for pattern in patterns:
            if pattern['signal'] == signal_type:
                confidence += 10
                reasons.append(f"檢測到{pattern['pattern']}型態：{pattern['description']}")
            elif pattern['signal'] != 'HOLD' and pattern['signal'] != signal_type:
                confidence -= 5
                warnings.append(f"檢測到相反型態{pattern['pattern']}，需謹慎")
        
        # --- 5. 波動率風險調整 (減少懲罰) ---
        if 'Volatility_Risk' in latest.index:
            vol_risk = latest['Volatility_Risk']
            if vol_risk > 10:  # 提高門檻
                confidence -= 15
                warnings.append(f"極高波動率({vol_risk:.1f}%)，風險較大")
            elif vol_risk > 7:  # 提高門檻
                confidence -= 8
                warnings.append(f"高波動率({vol_risk:.1f}%)，需注意風險")
        
        # --- 6. 計算具體進出場點位 ---
        if signal_type == 'BUY':
            # 買入價：當前價格或回檔到支撐
            entry_price = current_price
            if support and current_price > support * 1.02:  # 如果還有回檔空間
                entry_price = min(current_price, support * 1.01)
            
            # ATR停損停利
            atr_stop, atr_profits = self.calculate_atr_stops(data)
            stop_loss = atr_stop if atr_stop else support * 0.98 if support else current_price * 0.95
            take_profit = atr_profits if atr_profits else [current_price * 1.08, current_price * 1.15, current_price * 1.25]
            
        elif signal_type == 'SELL':
            entry_price = current_price
            if resistance and current_price < resistance * 0.98:
                entry_price = max(current_price, resistance * 0.99)
            
            stop_loss = resistance * 1.02 if resistance else current_price * 1.05
            take_profit = [current_price * 0.92, current_price * 0.85, current_price * 0.78]
            
        else:  # HOLD
            entry_price = current_price
            stop_loss = support * 0.98 if support else current_price * 0.9
            take_profit = [resistance * 0.98] if resistance else [current_price * 1.1]
        
        # 計算風險報酬比
        if signal_type in ['BUY', 'SELL']:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit[0] - entry_price) if take_profit else risk
            risk_reward_ratio = reward / risk if risk > 0 else 0
        else:
            risk_reward_ratio = 0
        
        # 持有期間建議
        if confidence > 70:
            holding_period = "3-7個交易日"
        elif confidence > 50:
            holding_period = "1-3個交易日"
        else:
            holding_period = "觀望，等待更好時機"
        
        # 信心度最終調整
        confidence = max(20, min(confidence, 95))  # 最低給20%，最高95%
        
        # 🔥 調整信心度門檻，與技術評分更一致
        min_threshold = 50  # 降低門檻到50%
        if confidence < min_threshold and signal_type != 'HOLD':
            original_signal = signal_type
            signal_type = 'HOLD'
            reasons.insert(0, f"原本為{original_signal}訊號，但綜合考量後建議觀望")
            reasons.append(f"信心度{confidence}%，建議等待更好時機")
        
        return TradingSignal(
            signal_type=signal_type,
            confidence=confidence,
            entry_price=round(entry_price, 2),
            stop_loss=round(stop_loss, 2),
            take_profit=[round(tp, 2) for tp in take_profit] if take_profit else [],
            risk_reward_ratio=round(risk_reward_ratio, 2),
            holding_period=holding_period,
            reasons=reasons,
            warnings=warnings
        )

def format_trading_signal(signal: TradingSignal, stock_code: str, stock_name: str) -> str:
    """格式化交易訊號輸出"""
    
    signal_emoji = {
        'BUY': '🟢',
        'SELL': '🔴', 
        'HOLD': '🟡'
    }
    
    signal_text = {
        'BUY': '買入',
        'SELL': '賣出',
        'HOLD': '觀望'
    }
    
    confidence_level = ""
    if signal.confidence >= 80:
        confidence_level = "極高信心"
    elif signal.confidence >= 70:
        confidence_level = "高信心"
    elif signal.confidence >= 60:
        confidence_level = "中等信心"
    else:
        confidence_level = "低信心"
    
    output = []
    output.append("=" * 60)
    output.append(f"🎯 交易訊號預測報告 - {stock_code} {stock_name}")
    output.append("=" * 60)
    output.append("")
    
    output.append(f"{signal_emoji[signal.signal_type]} 主要訊號: {signal_text[signal.signal_type]}")
    output.append(f"📊 信心程度: {signal.confidence}% ({confidence_level})")
    output.append("")
    
    if signal.signal_type != 'HOLD':
        output.append("💰 具體操作建議:")
        output.append(f"   進場價位: ${signal.entry_price}")
        output.append(f"   停損價位: ${signal.stop_loss}")
        
        if signal.take_profit:
            output.append("   獲利了結:")
            for i, tp in enumerate(signal.take_profit, 1):
                percentage = ((tp - signal.entry_price) / signal.entry_price) * 100
                output.append(f"     第{i}批: ${tp} (+{percentage:.1f}%)")
        
        output.append(f"   風險報酬比: 1:{signal.risk_reward_ratio}")
        output.append(f"   建議持有: {signal.holding_period}")
    
    output.append("")
    output.append("📋 訊號依據:")
    for i, reason in enumerate(signal.reasons, 1):
        output.append(f"   {i}. {reason}")
    
    if signal.warnings:
        output.append("")
        output.append("⚠️  風險警告:")
        for i, warning in enumerate(signal.warnings, 1):
            output.append(f"   {i}. {warning}")
    
    output.append("")
    output.append("📝 操作建議:")
    if signal.signal_type == 'BUY':
        output.append("   • 建議分批進場，不要一次滿倉")
        output.append("   • 嚴格執行停損，保護資金安全")
        output.append("   • 達到目標價位分批獲利了結")
        output.append("   • 密切關注成交量變化")
    elif signal.signal_type == 'SELL':
        output.append("   • 如有持股建議分批出場")
        output.append("   • 空單操作需謹慎，控制倉位")
        output.append("   • 注意反彈風險")
    else:
        output.append("   • 當前訊號不明確，建議觀望")
        output.append("   • 等待更好的進場時機")
        output.append("   • 持續觀察技術指標變化")
    
    output.append("")
    output.append("⚠️  重要提醒:")
    output.append("   • 本預測僅供參考，不構成投資建議")
    output.append("   • 市場有風險，投資需謹慎")
    output.append("   • 請結合基本面分析做出最終決策")
    output.append("   • 務必做好風險管理和資金控制")
    
    return "\n".join(output)