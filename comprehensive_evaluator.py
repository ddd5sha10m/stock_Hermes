# comprehensive_evaluator.py - 綜合投資價值評估系統

from dataclasses import dataclass
from typing import List, Dict, Tuple
import pandas as pd

@dataclass
class InvestmentEvaluation:
    """綜合投資評估結果"""
    overall_score: float  # 總體評分 (0-100)
    investment_grade: str  # 投資等級 (A+到D-)
    risk_level: str  # 風險等級 (低/中/高/極高)
    time_horizon: str  # 適合投資期間
    position_suggestion: str  # 倉位建議
    core_thesis: str  # 核心投資論點
    key_strengths: List[str]  # 主要優勢
    key_risks: List[str]  # 主要風險
    action_items: List[str]  # 具體行動建議
    monitoring_points: List[str]  # 需要持續關注的指標

class ComprehensiveEvaluator:
    """綜合投資價值評估器"""
    
    def __init__(self):
        # 權重配置
        self.weights = {
            'fundamental': 0.40,  # 基本面權重
            'technical': 0.35,    # 技術面權重
            'risk': 0.15,        # 風險評估權重
            'momentum': 0.10     # 動能評估權重
        }
        
    def evaluate_fundamental_quality(self, fundamental_data: Dict) -> Tuple[float, Dict]:
        """評估基本面品質"""
        if not fundamental_data:
            return 0, {'score': 0, 'grade': 'N/A', 'details': ['無基本面數據']}
            
        score = 0
        details = []
        
        # 1. 獲利能力評估 (40分)
        profitability_score = 0
        
        # ROE評估
        roe = fundamental_data.get('ROE', 0)
        if roe > 20:
            profitability_score += 15
            details.append(f"卓越ROE {roe:.1f}% - 管理層經營效率極佳")
        elif roe > 15:
            profitability_score += 10
            details.append(f"優良ROE {roe:.1f}% - 穩定獲利能力")
        elif roe > 8:
            profitability_score += 5
            details.append(f"合格ROE {roe:.1f}% - 獲利能力尚可")
        else:
            details.append(f"ROE偏低 {roe:.1f}% - 需關注獲利改善")
            
        # 毛利率評估
        gross_margin = fundamental_data.get('毛利率', 0)
        if gross_margin > 40:
            profitability_score += 10
            details.append(f"高毛利率 {gross_margin:.1f}% - 產品競爭力強")
        elif gross_margin > 25:
            profitability_score += 6
            details.append(f"毛利率 {gross_margin:.1f}% - 產業地位穩固")
        elif gross_margin > 15:
            profitability_score += 3
            details.append(f"毛利率 {gross_margin:.1f}% - 一般水準")
            
        # 營業利益率
        op_margin = fundamental_data.get('營業利益率', 0)
        if op_margin > 15:
            profitability_score += 10
            details.append(f"營業利益率 {op_margin:.1f}% - 營運效率優異")
        elif op_margin > 8:
            profitability_score += 5
            details.append(f"營業利益率 {op_margin:.1f}% - 營運表現良好")
            
        # EPS
        eps = fundamental_data.get('EPS', 0)
        if eps > 5:
            profitability_score += 5
            details.append(f"EPS ${eps:.2f} - 每股獲利豐厚")
        elif eps > 0:
            profitability_score += 2
            details.append(f"EPS ${eps:.2f} - 維持獲利")
        else:
            details.append("EPS為負 - 虧損中")
            
        score += profitability_score
        
        # 2. 成長性評估 (20分)
        growth_score = 0
        revenue_growth = fundamental_data.get('營收成長率', 0)
        
        if revenue_growth > 20:
            growth_score += 20
            details.append(f"營收高速成長 {revenue_growth:.1f}% - 業務快速擴張")
        elif revenue_growth > 10:
            growth_score += 15
            details.append(f"營收穩健成長 {revenue_growth:.1f}% - 成長動能佳")
        elif revenue_growth > 0:
            growth_score += 8
            details.append(f"營收正成長 {revenue_growth:.1f}% - 業務穩定")
        else:
            details.append(f"營收衰退 {revenue_growth:.1f}% - 需關注轉機")
            
        score += growth_score
        
        # 3. 財務健康度 (25分)
        financial_health_score = 0
        
        # 負債比率
        debt_ratio = fundamental_data.get('負債比率', 100)
        if debt_ratio < 40:
            financial_health_score += 10
            details.append(f"負債比 {debt_ratio:.1f}% - 財務結構健全")
        elif debt_ratio < 60:
            financial_health_score += 6
            details.append(f"負債比 {debt_ratio:.1f}% - 財務槓桿適中")
        else:
            details.append(f"負債比 {debt_ratio:.1f}% - 財務槓桿偏高")
            
        # 流動比率
        current_ratio = fundamental_data.get('流動比率', 0)
        if current_ratio > 2:
            financial_health_score += 8
            details.append(f"流動比率 {current_ratio:.1f} - 短期償債能力強")
        elif current_ratio > 1.5:
            financial_health_score += 5
            details.append(f"流動比率 {current_ratio:.1f} - 流動性充足")
        elif current_ratio > 1:
            financial_health_score += 2
            details.append(f"流動比率 {current_ratio:.1f} - 流動性尚可")
        else:
            details.append(f"流動比率 {current_ratio:.1f} - 流動性風險")
            
        # 自由現金流
        fcf = fundamental_data.get('自由現金流', 0)
        if fcf > 0:
            financial_health_score += 7
            details.append("自由現金流為正 - 現金創造能力佳")
        else:
            details.append("自由現金流為負 - 需關注資金狀況")
            
        score += financial_health_score
        
        # 4. 價值評估 (15分)
        valuation_score = 0
        pe_ratio = fundamental_data.get('本益比', 999)
        
        if 0 < pe_ratio <= 12:
            valuation_score += 15
            details.append(f"本益比 {pe_ratio:.1f} - 估值偏低，具投資價值")
        elif pe_ratio <= 20:
            valuation_score += 10
            details.append(f"本益比 {pe_ratio:.1f} - 估值合理")
        elif pe_ratio <= 30:
            valuation_score += 5
            details.append(f"本益比 {pe_ratio:.1f} - 估值偏高，需有成長支撐")
        elif pe_ratio > 0:
            details.append(f"本益比 {pe_ratio:.1f} - 估值過高，風險較大")
            
        score += valuation_score
        
        # 判定等級
        if score >= 80:
            grade = 'A+'
        elif score >= 70:
            grade = 'A'
        elif score >= 60:
            grade = 'B+'
        elif score >= 50:
            grade = 'B'
        elif score >= 40:
            grade = 'C+'
        elif score >= 30:
            grade = 'C'
        else:
            grade = 'D'
            
        return score, {
            'score': score,
            'grade': grade,
            'details': details
        }
    
    def evaluate_technical_strength(self, tech_data: pd.DataFrame, tech_score: int) -> Tuple[float, Dict]:
        """評估技術面強度"""
        if tech_data is None or tech_data.empty:
            return 0, {'score': 0, 'strength': '無法評估', 'details': ['無技術數據']}
            
        latest = tech_data.iloc[-1]
        score = tech_score  # 使用原始技術評分
        details = []
        
        # 趨勢強度評估
        trend_strength = "不明"
        if score >= 70:
            trend_strength = "強勢上升"
            details.append("技術面呈現強勢上升趨勢")
        elif score >= 55:
            trend_strength = "溫和上升"
            details.append("技術面呈現溫和上升趨勢")
        elif score >= 45:
            trend_strength = "盤整"
            details.append("技術面處於盤整格局")
        elif score >= 30:
            trend_strength = "溫和下降"
            details.append("技術面呈現溫和下降趨勢")
        else:
            trend_strength = "弱勢下降"
            details.append("技術面呈現弱勢下降趨勢")
            
        # 支撐壓力評估
        if 'Support_Level' in latest.index and 'Resistance_Level' in latest.index:
            support = latest['Support_Level']
            resistance = latest['Resistance_Level']
            current_price = latest['Close']
            
            support_distance = (current_price - support) / current_price * 100
            resistance_distance = (resistance - current_price) / current_price * 100
            
            if support_distance < 5:
                details.append(f"接近支撐位 (距離{support_distance:.1f}%)")
            if resistance_distance < 5:
                details.append(f"接近壓力位 (距離{resistance_distance:.1f}%)")
                
        # 動能評估
        if 'RSI' in latest.index:
            rsi = latest['RSI']
            if rsi > 70:
                details.append(f"RSI {rsi:.1f} - 短期超買")
            elif rsi < 30:
                details.append(f"RSI {rsi:.1f} - 短期超賣")
                
        return score, {
            'score': score,
            'strength': trend_strength,
            'details': details
        }
    
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
    
    def generate_comprehensive_evaluation(self, 
                                        tech_data: pd.DataFrame,
                                        tech_score: int,
                                        fundamental_data: Dict,
                                        trading_signal) -> InvestmentEvaluation:
        """生成綜合投資評估"""
        
        # 各維度評估
        fund_score, fund_result = self.evaluate_fundamental_quality(fundamental_data)
        tech_score_norm, tech_result = self.evaluate_technical_strength(tech_data, tech_score)
        risk_score, risk_result = self.evaluate_risk_profile(tech_data, fundamental_data)
        momentum_score, momentum_result = self.evaluate_momentum(tech_data)
        
        # 計算綜合分數
        overall_score = (
            fund_score * self.weights['fundamental'] +
            tech_score_norm * self.weights['technical'] +
            risk_score * self.weights['risk'] +
            momentum_score * self.weights['momentum']
        )
        
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