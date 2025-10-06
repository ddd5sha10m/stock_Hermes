# comprehensive_evaluator.py - 最終整合版評估系統

from dataclasses import dataclass
from typing import List, Dict, Tuple
import pandas as pd

@dataclass
class InvestmentEvaluation:
    # (此資料結構不變)
    overall_score: float; investment_grade: str; risk_level: str; time_horizon: str; position_suggestion: str; core_thesis: str; key_strengths: List[str]; key_risks: List[str]; action_items: List[str]; monitoring_points: List[str]

class ComprehensiveEvaluator:
    """綜合投資價值評估器 (單一職責)"""
    
    def __init__(self):
        # 權重配置 - 修正版本
        self.weights = {
            'fundamental': 0.35,  # 基本面權重
            'technical': 0.35,    # 技術面權重
            'chip_flow': 0.15,    # 籌碼面權重 - 新增這行
            'risk': 0.10,         # 風險評估權重
            'momentum': 0.05      # 動能評估權重
        }
        # 確保權重總和為 1.0
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.001:
            # 自動調整權重使其總和為 1.0
            scale_factor = 1.0 / total_weight
            for key in self.weights:
                self.weights[key] *= scale_factor
    
    # 【整合】原 main.py 中的 calculate_fundamental_score 邏輯已完全移入此處
    def evaluate_fundamental_quality(self, fundamental_data: Dict) -> Tuple[int, Dict]:
        """評估基本面品質"""
        if not fundamental_data:
            return 0, {'score': 0, 'grade': 'N/A', 'details': ['無基本面數據']}
            
        score = 0; details = []
        
        # 1. 獲利能力 (40分)
        roe = fundamental_data.get('ROE', 0)
        if roe > 15: score += 15; details.append(f"高ROE: {roe:.1f}% (+15)")
        elif roe > 8: score += 8; details.append(f"良好ROE: {roe:.1f}% (+8)")
        
        gross_margin = fundamental_data.get('毛利率', 0)
        if gross_margin > 30: score += 10; details.append(f"高毛利率: {gross_margin:.1f}% (+10)")
        elif gross_margin > 15: score += 5; details.append(f"尚可毛利率: {gross_margin:.1f}% (+5)")

        op_margin = fundamental_data.get('營業利益率', 0)
        if op_margin > 10: score += 10; details.append(f"高營業利益率: {op_margin:.1f}% (+10)")
        elif op_margin > 5: score += 5; details.append(f"尚可營業利益率: {op_margin:.1f}% (+5)")
        
        if fundamental_data.get('EPS', 0) > 0: score += 5; details.append(f"EPS為正: {fundamental_data.get('EPS', 0):.2f} (+5)")

        # 2. 成長性 (20分)
        revenue_growth = fundamental_data.get('營收成長率', 0)
        if revenue_growth > 10: score += 20; details.append(f"高速營收成長: {revenue_growth:.1f}% (+20)")
        elif revenue_growth > 0: score += 10; details.append(f"營收正成長: {revenue_growth:.1f}% (+10)")
        
        # 3. 財務健康 (25分)
        if fundamental_data.get('負債比率', 100) < 50: score += 10; details.append(f"低負債比: {fundamental_data.get('負債比率', 100):.1f}% (+10)")
        if fundamental_data.get('流動比率', 0) > 2: score += 8; details.append(f"高流動比率: {fundamental_data.get('流動比率', 0):.1f} (+8)")
        if fundamental_data.get('自由現金流', 0) > 0: score += 7; details.append(f"自由現金流為正 (+7)")

        # 4. 價值評估 (15分)
        pe = fundamental_data.get('本益比', 999)
        if 0 < pe <= 15: score += 15; details.append(f"價值區間本益比: {pe:.1f} (+15)")
        elif 15 < pe <= 25: score += 8; details.append(f"合理本益比: {pe:.1f} (+8)")
            
        grade = 'A+' if score >= 80 else 'A' if score >= 70 else 'B+' if score >= 60 else 'B'
        
        return int(score), {'score': int(score), 'grade': grade, 'details': details}

    # 【整合】原 main.py 中的 calculate_technical_score 邏輯已完全移入此處
    
    def evaluate_technical_strength(self, data: pd.DataFrame) -> Tuple[int, Dict]:
        """評估技術面強度"""
        score = 0; details = []
        if data is None or data.empty: return 0, {'score': 0, 'strength': '無法評估', 'details': ['無技術數據']}
        latest = data.iloc[-1]
        
        # (詳細的技術評分邏輯...)
        trend_score=0
        if 'Deviation_MA60' in latest.index:
            deviation_60=latest['Deviation_MA60']
            if deviation_60 > 0:
                if deviation_60 <= 10: trend_score += 15; details.append(f"價格在60MA之上，乖離率健康 (+15)")
                elif deviation_60 <= 20: trend_score += 10; details.append(f"價格在60MA之上但乖離稍大 (+10)")
                else: trend_score += 5; details.append(f"價格乖離60MA過大，回調風險 (+5)")
        if 'MA20' in latest.index and 'MA60' in latest.index and latest['MA20'] > latest['MA60']: trend_score += 10; details.append("20MA > 60MA，中期趨勢向上 (+10)")
        if 'MA5' in latest.index and 'MA20' in latest.index and latest['MA5'] > latest['MA20']: trend_score += 5; details.append("5MA > 20MA，短期趨勢向上 (+5)")
        score += trend_score; momentum_score=0
        if 'K' in latest.index and 'D' in latest.index and 'MA60' in latest.index:
            is_uptrend = latest['Close'] > latest['MA60']
            if latest['K'] > latest['D']: momentum_score += 5; details.append("K > D，短期動量向上 (+5)")
            if is_uptrend:
                if latest['K'] < 30: momentum_score += 8; details.append("多頭趨勢中K<30，強勢回檔買點 (+8)")
            else:
                if latest['K'] < 20: momentum_score += 3; details.append("空頭趨勢中K<20，超賣反彈機會 (+3)")
        if 'RSI' in latest.index:
            rsi = latest['RSI']
            if 30 <= rsi <= 70: momentum_score += 5; details.append(f"RSI={rsi:.1f}在健康區間 (+5)")
        if all(col in latest.index for col in['DIF','DEM']):
            if len(data) >= 5:
                dif_trend = latest['DIF'] - data.iloc[-5]['DIF']
                if latest['DIF'] > latest['DEM'] and latest['DIF'] > 0 and dif_trend > 0: momentum_score += 10; details.append("MACD零軸上方且加速向上 (+10)")
        score += momentum_score; bb_score=0
        if all(col in latest.index for col in['Close','BB_Upper','BB_Lower']):
            if len(data) >= 5:
                if latest['Close'] > latest['BB_Upper']: bb_score += 10; details.append("突破布林上軌，強勢訊號 (+10)")
        score += bb_score; volume_score=0
        if 'Volume_Ratio' in latest.index:
            vol_ratio=latest['Volume_Ratio']; vp_signal=latest.get('Volume_Price_Signal','');
            if vp_signal == '價漲量增' and vol_ratio > 1.2: volume_score += 15; details.append(f"價漲量增(量比{vol_ratio:.1f}) (+15)")
            elif vp_signal == '價跌量縮': volume_score += 5; details.append("價跌量縮，賣壓減輕 (+5)")
        score += volume_score; risk_penalty=0
        if 'Volatility_Risk' in latest.index:
            vol_risk = latest['Volatility_Risk']
            if vol_risk > 7: risk_penalty += 10; details.append(f"高波動率{vol_risk:.1f}% (-10)")
        score -= risk_penalty
    
        # ADX 趨勢強度調整
        if 'ADX_14' in latest.index:
            adx = latest['ADX_14']
            if adx > 25 and score > 60:
                trend_bonus = int(score * 0.1); score += trend_bonus; details.append(f"強趨勢環境(ADX={adx:.1f})加成 (+{trend_bonus})")
        
        score = int(max(0, min(score, 100)))
        strength = "強勢上升" if score >= 70 else "溫和上升" if score >= 55 else "盤整或下降"
        return score, {'score': score, 'strength': strength, 'details': details}
    
    def evaluate_risk_profile(self, tech_data: pd.DataFrame, fundamental_data: Dict) -> Tuple[float, Dict]:
        """評估風險狀況 (分數越高風險越低)"""
        risk_score = 100  # 從滿分開始扣
        risk_factors = []
        
        if tech_data is not None and not tech_data.empty:
            latest = tech_data.iloc[-1]
            
            # 波動率風險
            if 'Volatility_Risk' in latest.index:
                vol_risk = latest['Volatility_Risk']
                if vol_risk > 10:
                    risk_score -= 30
                    risk_factors.append(f"極高波動率 {vol_risk:.1f}% - 價格劇烈波動")
                elif vol_risk > 7:
                    risk_score -= 20
                    risk_factors.append(f"高波動率 {vol_risk:.1f}% - 價格波動較大")
                elif vol_risk > 5:
                    risk_score -= 10
                    risk_factors.append(f"中等波動率 {vol_risk:.1f}% - 正常波動")
                    
            # 成交量風險
            if 'Volume_Ratio' in latest.index:
                vol_ratio = latest['Volume_Ratio']
                if vol_ratio < 0.5:
                    risk_score -= 15
                    risk_factors.append("成交量萎縮 - 流動性風險")
                    
        if fundamental_data:
            # 財務風險
            debt_ratio = fundamental_data.get('負債比率', 0)
            if debt_ratio > 70:
                risk_score -= 20
                risk_factors.append(f"高負債比 {debt_ratio:.1f}% - 財務風險")
                
            # 獲利風險
            eps = fundamental_data.get('EPS', 0)
            if eps < 0:
                risk_score -= 25
                risk_factors.append("虧損中 - 營運風險")
                
            # 估值風險
            pe = fundamental_data.get('本益比', 0)
            if pe > 40:
                risk_score -= 15
                risk_factors.append(f"高本益比 {pe:.1f} - 估值風險")
                
        # 風險等級判定
        if risk_score >= 80:
            risk_level = "低"
        elif risk_score >= 60:
            risk_level = "中"
        elif risk_score >= 40:
            risk_level = "高"
        else:
            risk_level = "極高"
            
        return risk_score, {
            'score': risk_score,
            'level': risk_level,
            'factors': risk_factors
        }
    
    def evaluate_momentum(self, tech_data: pd.DataFrame) -> Tuple[float, Dict]:
        """評估動能狀況"""
        if tech_data is None or len(tech_data) < 20:
            return 50, {'score': 50, 'trend': '無法評估', 'details': ['數據不足']}
            
        momentum_score = 50  # 中性起始
        details = []
        
        # 短期動能 (5日)
        price_change_5d = (tech_data['Close'].iloc[-1] / tech_data['Close'].iloc[-6] - 1) * 100
        if price_change_5d > 5:
            momentum_score += 15
            details.append(f"5日漲幅 {price_change_5d:.1f}% - 短期動能強")
        elif price_change_5d < -5:
            momentum_score -= 15
            details.append(f"5日跌幅 {abs(price_change_5d):.1f}% - 短期動能弱")
            
        # 中期動能 (20日)
        price_change_20d = (tech_data['Close'].iloc[-1] / tech_data['Close'].iloc[-21] - 1) * 100
        if price_change_20d > 10:
            momentum_score += 20
            details.append(f"20日漲幅 {price_change_20d:.1f}% - 中期動能強")
        elif price_change_20d < -10:
            momentum_score -= 20
            details.append(f"20日跌幅 {abs(price_change_20d):.1f}% - 中期動能弱")
            
        # 相對強弱
        latest = tech_data.iloc[-1]
        if 'Bull_Bear_Balance' in latest.index:
            balance = latest['Bull_Bear_Balance']
            if balance > 0.5:
                momentum_score += 15
                details.append("多空力道偏多")
            elif balance < -0.5:
                momentum_score -= 15
                details.append("多空力道偏空")
                
        momentum_score = max(0, min(100, momentum_score))
        
        if momentum_score >= 70:
            trend = "強勁上升"
        elif momentum_score >= 55:
            trend = "溫和上升"
        elif momentum_score >= 45:
            trend = "橫向整理"
        elif momentum_score >= 30:
            trend = "溫和下降"
        else:
            trend = "明顯下降"
            
        return momentum_score, {
            'score': momentum_score,
            'trend': trend,
            'details': details
        }
    
    def evaluate_chip_flow(self, chip_data: pd.DataFrame) -> Tuple[float, Dict]:
        """評估法人籌碼流向 (分數越高越樂觀)"""
        if chip_data is None or chip_data.empty or len(chip_data) < 3:
            return 50, {'score': 50, 'grade': '中性', 'details': ['籌碼數據不足']}
            
        score = 50  # 中性起始分數
        details = []

        # 外資趨勢分析
        foreign_trend = chip_data['外資買賣超'].head(3) # 取最近3天
        if (foreign_trend > 0).all():
            score += 25
            details.append(f"外資連續 {len(foreign_trend)} 日買超 (+25)")
        elif (foreign_trend < 0).all():
            score -= 20
            details.append(f"外資連續 {len(foreign_trend)} 日賣超 (-20)")
        
        # 投信趨勢分析 (投信的影響力通常更集中)
        trust_trend = chip_data['投信買賣超'].head(3)
        if (trust_trend > 0).all():
            score += 30
            details.append(f"投信連續 {len(trust_trend)} 日買超 (強烈訊號) (+30)")
        elif (trust_trend < 0).all():
            score -= 25
            details.append(f"投信連續 {len(trust_trend)} 日賣超 (-25)")

        # 當日法人同步動向
        latest_trade = chip_data.iloc[0]
        if latest_trade['外資買賣超'] > 0 and latest_trade['投信買賣超'] > 0:
            score += 20
            details.append("外資與投信今日同步買超 (+20)")
        elif latest_trade['外資買賣超'] < 0 and latest_trade['投信買賣超'] < 0:
            score -= 15
            details.append("外資與投信今日同步賣超 (-15)")
            
        score = max(0, min(100, score)) # 確保分數在 0-100 之間

        # 判定等級
        if score >= 80: grade = '非常集中'
        elif score >= 65: grade = '集中'
        elif score >= 40: grade = '普通'
        elif score >= 25: grade = '凌亂'
        else: grade = '非常凌亂'
            
        return score, {'score': score, 'grade': grade, 'details': details}
    
    def generate_comprehensive_evaluation(self, 
                                        tech_data: pd.DataFrame,
                                        tech_score: int,
                                        fundamental_data: Dict,
                                        trading_signal,
                                        market_state: str,
                                        chip_data: pd.DataFrame) -> InvestmentEvaluation:
        """生成綜合投資評估"""
        
        # 各維度評估
        fund_score, fund_result = self.evaluate_fundamental_quality(fundamental_data)
        tech_score_norm, tech_result = self.evaluate_technical_strength(tech_data)
        risk_score, risk_result = self.evaluate_risk_profile(tech_data, fundamental_data)
        momentum_score, momentum_result = self.evaluate_momentum(tech_data)
        chip_score, chip_result = self.evaluate_chip_flow(chip_data)
        
        # 計算綜合分數
        overall_score = (
        fund_score * self.weights.get('fundamental', 0.35) +
        tech_score_norm * self.weights.get('technical', 0.35) +
        chip_score * self.weights.get('chip_flow', 0.15) +
        risk_score * self.weights.get('risk', 0.10) +
        momentum_score * self.weights.get('momentum', 0.05)
    )
        # 市場狀態調整
        adjustment_reason = ""
        if market_state == '多頭' and overall_score >= 60:
            adjustment = 10
            overall_score += adjustment
            adjustment_reason = f"大盤多頭趨勢加成 (+{adjustment}) "
        elif market_state == '空頭':
            adjustment_factor = 0.85
            overall_score *= adjustment_factor
            adjustment_reason = f"大盤空頭趨勢修正 (x{adjustment_factor}) "
    
        overall_score = round(max(0, min(100, overall_score)), 1)
        
        # 判定投資等級
        if overall_score >= 80:
            investment_grade = "A+ (極佳投資標的)"
        elif overall_score >= 70:
            investment_grade = "A (優良投資標的)"
        elif overall_score >= 60:
            investment_grade = "B+ (良好投資標的)"
        elif overall_score >= 50:
            investment_grade = "B (可考慮投資)"
        elif overall_score >= 40:
            investment_grade = "C+ (謹慎投資)"
        elif overall_score >= 30:
            investment_grade = "C (高風險投資)"
        else:
            investment_grade = "D (不建議投資)"
        
        if market_state == '空頭' and fund_score >= 70 and tech_score < 50:
             core_thesis = f"{adjustment_reason}基本面優秀，但受大盤拖累，呈現價值浮現的機會"
        elif fund_result['grade'] in ['A+', 'A'] and tech_result['strength'] in ["強勢上升"]:
            core_thesis = f"{adjustment_reason}基本面優異且技術面向好，具備中長期投資價值"
        elif fund_result['grade'] in ['B+', 'B'] and momentum_result['trend'] in ["強勁上升"]:
            core_thesis = f"{adjustment_reason}基本面穩健，短期動能強勁，適合波段操作"
        else:
            core_thesis = f"{adjustment_reason}綜合評估一般，需要更多催化劑"
            
        # 建議投資期間
        if risk_result['level'] == "低" and momentum_result['trend'] in ["強勁上升", "溫和上升"]:
            time_horizon = "中長期持有 (3-6個月)"
        elif risk_result['level'] in ["低", "中"] and trading_signal.signal_type == "BUY":
            time_horizon = "短中期持有 (1-3個月)"
        elif risk_result['level'] == "高" or trading_signal.signal_type == "SELL":
            time_horizon = "短線操作或觀望"
        else:
            time_horizon = "不建議進場"
            
        # 倉位建議
        if overall_score >= 70 and risk_result['level'] in ["低", "中"]:
            position_suggestion = "可配置20-30%資金"
        elif overall_score >= 60 and risk_result['level'] == "中":
            position_suggestion = "可配置10-20%資金"
        elif overall_score >= 50:
            position_suggestion = "小額試單5-10%"
        else:
            position_suggestion = "不建議配置或減碼"
            
        # 核心投資論點
        if fund_result['grade'] in ['A+', 'A'] and tech_result['strength'] in ["強勢上升", "溫和上升"]:
            core_thesis = "基本面優異且技術面向好，具備中長期投資價值"
        elif fund_result['grade'] in ['B+', 'B'] and momentum_result['trend'] in ["強勁上升"]:
            core_thesis = "基本面穩健，短期動能強勁，適合波段操作"
        elif risk_result['level'] in ["高", "極高"]:
            core_thesis = "風險偏高，建議等待更好的進場時機"
        else:
            core_thesis = "綜合評估一般，需要更多催化劑"
            
        # 主要優勢
        key_strengths = []
        if fund_score >= 70:
            key_strengths.append("基本面表現優異")
        if tech_score_norm >= 70:
            key_strengths.append("技術面趨勢明確")
        if risk_score >= 70:
            key_strengths.append("風險控制良好")
        if momentum_score >= 70:
            key_strengths.append("短期動能強勁")
        if not key_strengths:
            key_strengths.append("暫無明顯優勢")
            
        # 主要風險
        key_risks = risk_result['factors'] if risk_result['factors'] else ["風險可控"]
        
        # 具體行動建議
        action_items = []
        if trading_signal.signal_type == "BUY" and overall_score >= 60:
            action_items.append(f"可在${trading_signal.entry_price}附近分批建倉")
            action_items.append(f"設定停損於${trading_signal.stop_loss}")
            action_items.append(f"第一目標價${trading_signal.take_profit[0] if trading_signal.take_profit else '待定'}")
        elif trading_signal.signal_type == "SELL":
            action_items.append("建議減碼或空手觀望")
            action_items.append("等待更好的進場時機")
        else:
            action_items.append("維持觀望，等待訊號明確")
            
        # 需要監控的指標
        monitoring_points = []
        if tech_data is not None and not tech_data.empty:
            latest = tech_data.iloc[-1]
        if 'Support_Level' in latest.index:
            monitoring_points.append(f"支撐位 ${latest['Support_Level']:.2f}")
        if 'Resistance_Level' in latest.index:
            monitoring_points.append(f"壓力位 ${latest['Resistance_Level']:.2f}")
        monitoring_points.append("成交量變化")
        monitoring_points.append("營收月增率")
        if chip_data is not None and not chip_data.empty:
            monitoring_points.append("法人買賣超變化")
        
        return InvestmentEvaluation(
        overall_score=round(overall_score, 1),
        investment_grade=investment_grade,
        risk_level=risk_result['level'],
        time_horizon=time_horizon,
        position_suggestion=position_suggestion,
        core_thesis=core_thesis,
        key_strengths=key_strengths,
        key_risks=key_risks,
        action_items=action_items,
        monitoring_points=monitoring_points
    )


def format_comprehensive_report(evaluation: InvestmentEvaluation, 
                              stock_code: str, 
                              stock_name: str,
                              fund_result: Dict,
                              tech_result: Dict,
                              risk_result: Dict,
                              chip_result: Dict,
                              momentum_result: Dict,
                              current_price: float,
                              fundamental_data: Dict) -> str:
    """格式化綜合評估報告"""
    
    output = []
    output.append("=" * 70)
    output.append(f"        💎 綜合投資價值評估報告 💎")
    output.append(f"        {stock_code} {stock_name}")
    output.append(f"        當前股價: ${current_price:.2f}")
    output.append("=" * 70)
    
    if fundamental_data:
        # 安全地獲取數據，如果不存在則顯示 'N/A'
        eps = fundamental_data.get('EPS', 'N/A')
        gross_margin = fundamental_data.get('毛利率', 'N/A')
        net_margin = fundamental_data.get('淨利率', 'N/A')
        
        # 格式化數字
        eps_str = f"{eps:.2f}" if isinstance(eps, (int, float)) else "N/A"
        gm_str = f"{gross_margin:.1f}%" if isinstance(gross_margin, (int, float)) else "N/A"
        nm_str = f"{net_margin:.1f}%" if isinstance(net_margin, (int, float)) else "N/A"
        
        output.append(f"        EPS: {eps_str} | 毛利率: {gm_str} | 淨利率: {nm_str}")
    
    output.append("=" * 70)
    # 總體評估
    output.append(f"\n📊 綜合評分: {evaluation.overall_score}/100")
    output.append(f"🏆 投資等級: {evaluation.investment_grade}")
    output.append(f"⚡ 風險等級: {evaluation.risk_level}")
    output.append(f"⏱️  建議投資期間: {evaluation.time_horizon}")
    output.append(f"💰 倉位建議: {evaluation.position_suggestion}")
    
    # 核心觀點
    output.append(f"\n💡 核心投資論點:")
    output.append(f"   {evaluation.core_thesis}")
    
    # 各維度評分
    output.append("\n📈 各維度評估:")
    output.append(f"   基本面: {fund_result['score']}/100 (等級: {fund_result['grade']})")
    output.append(f"   技術面: {tech_result['score']}/100 (趨勢: {tech_result['strength']})")
    output.append(f"   籌碼面: {chip_result['score']}/100 (籌碼: {chip_result['grade']})")
    output.append(f"   風險面: {risk_result['score']}/100 (風險: {risk_result['level']})")
    output.append(f"   動能面: {momentum_result['score']}/100 (動能: {momentum_result['trend']})")
    
    # 主要優勢
    output.append("\n✅ 主要優勢:")
    for strength in evaluation.key_strengths:
        output.append(f"   • {strength}")
    
    # 主要風險
    output.append("\n⚠️  主要風險:")
    for risk in evaluation.key_risks:
        output.append(f"   • {risk}")
    
    # 行動建議
    output.append("\n🎯 具體行動建議:")
    for i, action in enumerate(evaluation.action_items, 1):
        output.append(f"   {i}. {action}")
    
    # 監控重點
    output.append("\n👀 需持續監控:")
    for point in evaluation.monitoring_points:
        output.append(f"   • {point}")
    
    # 詳細分析
    output.append("\n" + "-" * 70)
    output.append("📋 詳細分析說明:")
    
    output.append("\n【基本面分析】")
    for detail in fund_result['details'][:5]:  # 只顯示前5項
        output.append(f"   • {detail}")
    
    output.append("\n【技術面分析】")
    for detail in tech_result['details'][:5]:
        output.append(f"   • {detail}")
    
    output.append("\n【動能分析】")
    for detail in momentum_result['details']:
        output.append(f"   • {detail}")
    output.append("\n【籌碼面分析】"); # 新增
    for detail in chip_result['details']: 
        output.append(f"   • {detail}")
    
    # 免責聲明
    output.append("\n" + "-" * 70)
    output.append("📌 重要提醒:")
    output.append("   • 本評估僅供參考，不構成投資建議")
    output.append("   • 投資有風險，決策前請充分了解")
    output.append("   • 建議配合其他資訊綜合判斷")
    output.append("   • 過去績效不代表未來表現")
    
    output.append("\n" + "=" * 70)
    output.append("評估完成！祝您投資順利！ 📈")
    output.append("=" * 70)
    
    return "\n".join(output)