# dashboard.py - 修復緩存問題版本

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import warnings
import numpy as np
import yfinance as yf
warnings.filterwarnings('ignore')

# 導入所有需要的分析模組
from technical_analyzer import analyze_stock_technicals
from fundamental_analyzer import analyze_stock_fundamentals
from trading_signals import TradingSignalGenerator, format_trading_signal
from comprehensive_evaluator import ComprehensiveEvaluator, format_comprehensive_report
from market_analyzer import get_market_state
from chip_analyzer import get_institutional_trades
from stock_list import STOCK_LIST

# 設定頁面配置
st.set_page_config(
    page_title="投資荷密斯 - 綜合投資分析儀表板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義CSS樣式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        border: 2px solid #e1e5e9;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .buy-signal {
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
    }
    .sell-signal {
        background-color: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
    }
    .hold-signal {
        background-color: #fff3cd;
        border-color: #ffeaa7;
        color: #856404;
    }
    .excellent-grade {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .good-grade {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .poor-grade {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .risk-low {
        background-color: #d4edda;
        color: #155724;
    }
    .risk-medium {
        background-color: #fff3cd;
        color: #856404;
    }
    .risk-high {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)  # 快取1小時 - 只快取可序列化的數據
def load_stock_data(stock_code):
    """載入股票數據，返回可序列化的數據"""
    
    # 嘗試不同的ticker格式
    ticker_formats = [f"{stock_code}.TW", f"{stock_code}.TWO"]
    
    for ticker_format in ticker_formats:
        try:
            ticker_obj = yf.Ticker(ticker_format)
            
            # 檢查ticker是否有效
            info = ticker_obj.info
            if info.get('regularMarketPrice') is None:
                continue
                
            # 獲取技術數據
            tech_data = analyze_stock_technicals(ticker_obj)
            if tech_data is None or tech_data.empty:
                continue
                
            # 獲取基本面數據
            fundamental_data = analyze_stock_fundamentals(ticker_obj)
            
            # 返回可序列化的數據，不返回 ticker_obj
            return {
                'tech_data': tech_data,
                'fundamental_data': fundamental_data,
                'ticker': ticker_format,
                'success': True
            }
            
        except Exception as e:
            continue
    
    return {
        'tech_data': None,
        'fundamental_data': None,
        'ticker': None,
        'success': False
    }

@st.cache_data(ttl=300)
def get_market_data():
    """獲取市場數據"""
    try:
        market_state = get_market_state()
        chip_data = get_institutional_trades(days_to_fetch=3)
        return market_state, chip_data
    except:
        return "盤整", None

def create_candlestick_chart(data, stock_name):
    """創建K線圖with技術指標疊加"""
    
    if data is None or data.empty:
        return go.Figure()
    
    # 取最近120個交易日的數據
    recent_data = data.tail(120).copy()
    
    # 創建子圖
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(
            f'{stock_name} - K線圖 & 技術指標',
            'MACD',
            'RSI & KD',
            '成交量'
        ),
        row_heights=[0.5, 0.15, 0.15, 0.2]
    )
    
    # K線圖
    fig.add_trace(
        go.Candlestick(
            x=recent_data.index,
            open=recent_data['Open'],
            high=recent_data['High'],
            low=recent_data['Low'],
            close=recent_data['Close'],
            name='K線',
            increasing_line_color='#ff4444',
            decreasing_line_color='#00aa00'
        ),
        row=1, col=1
    )
    
    # 移動平均線
    for ma_period, color in [(5, '#ff6b6b'), (20, '#4ecdc4'), (60, '#45b7d1')]:
        if f'MA{ma_period}' in recent_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=recent_data.index,
                    y=recent_data[f'MA{ma_period}'],
                    mode='lines',
                    name=f'MA{ma_period}',
                    line=dict(color=color, width=1.5),
                    opacity=0.8
                ),
                row=1, col=1
            )
    
    # 布林通道
    if all(col in recent_data.columns for col in ['BB_Upper', 'BB_Lower', 'BB_Middle']):
        fig.add_trace(
            go.Scatter(
                x=recent_data.index,
                y=recent_data['BB_Upper'],
                mode='lines',
                name='布林上軌',
                line=dict(color='purple', width=1, dash='dash'),
                opacity=0.6
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=recent_data.index,
                y=recent_data['BB_Middle'],
                mode='lines',
                name='布林中軌',
                line=dict(color='purple', width=1),
                opacity=0.6
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=recent_data.index,
                y=recent_data['BB_Lower'],
                mode='lines',
                name='布林下軌',
                line=dict(color='purple', width=1, dash='dash'),
                fill='tonexty',
                fillcolor='rgba(128, 0, 128, 0.1)',
                opacity=0.6
            ),
            row=1, col=1
        )
    
    # MACD
    if all(col in recent_data.columns for col in ['DIF', 'DEM', 'OSC']):
        fig.add_trace(
            go.Scatter(
                x=recent_data.index,
                y=recent_data['DIF'],
                mode='lines',
                name='DIF',
                line=dict(color='blue', width=1.5)
            ),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=recent_data.index,
                y=recent_data['DEM'],
                mode='lines',
                name='DEM',
                line=dict(color='red', width=1.5)
            ),
            row=2, col=1
        )
        fig.add_trace(
            go.Bar(
                x=recent_data.index,
                y=recent_data['OSC'],
                name='OSC',
                marker_color=np.where(recent_data['OSC'] >= 0, '#ff4444', '#00aa00'),
                opacity=0.6
            ),
            row=2, col=1
        )
        # MACD零軸線
        fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5, row=2, col=1)
    
    # RSI
    if 'RSI' in recent_data.columns:
        fig.add_trace(
            go.Scatter(
                x=recent_data.index,
                y=recent_data['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='orange', width=2)
            ),
            row=3, col=1
        )
        # RSI超買超賣線
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.3, row=3, col=1)
    
    # KD
    if all(col in recent_data.columns for col in ['K', 'D']):
        fig.add_trace(
            go.Scatter(
                x=recent_data.index,
                y=recent_data['K'],
                mode='lines',
                name='K',
                line=dict(color='blue', width=1.5)
            ),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=recent_data.index,
                y=recent_data['D'],
                mode='lines',
                name='D',
                line=dict(color='red', width=1.5)
            ),
            row=3, col=1
        )
        # KD超買超賣線
        fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.3, row=3, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.3, row=3, col=1)
    
    # 成交量
    colors = ['red' if row['Close'] >= row['Open'] else 'green' 
              for _, row in recent_data.iterrows()]
    
    fig.add_trace(
        go.Bar(
            x=recent_data.index,
            y=recent_data['Volume'],
            name='成交量',
            marker_color=colors,
            opacity=0.6
        ),
        row=4, col=1
    )
    
    # 成交量移動平均
    if 'Volume_MA20' in recent_data.columns:
        fig.add_trace(
            go.Scatter(
                x=recent_data.index,
                y=recent_data['Volume_MA20'],
                mode='lines',
                name='成交量MA20',
                line=dict(color='darkblue', width=1.5)
            ),
            row=4, col=1
        )
    
    # 更新布局
    fig.update_layout(
        height=800,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # 更新x軸
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='lightgray')
    
    return fig

def create_evaluation_radar_chart(fund_result, tech_result, risk_result, momentum_result, chip_result):
    """創建綜合評估雷達圖"""
    categories = ['基本面', '技術面', '風險控管', '動能面', '籌碼面']
    
    scores = [
        fund_result.get('score', 0),
        tech_result.get('score', 0),
        risk_result.get('score', 0),
        momentum_result.get('score', 0),
        chip_result.get('score', 50)  # 預設50分
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],  # 閉合多邊形
        theta=categories + [categories[0]],
        fill='toself',
        name='綜合評估',
        fillcolor='rgba(78, 205, 196, 0.3)',
        line=dict(color='rgba(78, 205, 196, 0.8)', width=2),
        marker=dict(size=4)
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10)
            ),
            angularaxis=dict(
                tickfont=dict(size=11)
            )
        ),
        showlegend=False,
        title=dict(
            text="五維度綜合評估雷達圖",
            x=0.5,
            font=dict(size=14)
        ),
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_score_gauge(score, title, color_scheme='blues'):
    """創建分數儀表板"""
    
    if color_scheme == 'blues':
        colors = ['lightgray', 'lightblue', 'blue', 'darkblue']
    elif color_scheme == 'reds':
        colors = ['lightgray', 'lightcoral', 'red', 'darkred']
    else:  # greens
        colors = ['lightgray', 'lightgreen', 'green', 'darkgreen']
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 14}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': colors[2]},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': colors[0]},
                {'range': [50, 70], 'color': colors[1]},
                {'range': [70, 90], 'color': colors[2]},
                {'range': [90, 100], 'color': colors[3]}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    
    return fig

def get_grade_color(score):
    """根據分數返回對應的顏色class"""
    if score >= 80:
        return "excellent-grade"
    elif score >= 60:
        return "good-grade"
    else:
        return "poor-grade"

def get_risk_color(risk_level):
    """根據風險等級返回對應的顏色class"""
    if risk_level == "低":
        return "risk-low"
    elif risk_level == "中":
        return "risk-medium"
    else:
        return "risk-high"

def main():
    st.markdown('<div class="main-header">💎 投資荷密斯 - 綜合投資分析儀表板</div>', unsafe_allow_html=True)
    
    # 側邊欄
    with st.sidebar:
        st.header("⚙️ 分析設定")
        
        # 股票選擇
        stock_options = {f"{code} - {name}": code for code, name in STOCK_LIST.items()}
        selected_option = st.selectbox("選擇要分析的股票:", options=list(stock_options.keys()), index=0)
        stock_code = stock_options[selected_option]
        stock_name = STOCK_LIST[stock_code]
        
        # 市場數據
        st.subheader("📊 市場狀態")
        market_state, chip_data = get_market_data()
        st.info(f"大盤趨勢: **{market_state}**")
        
        # 分析按鈕
        analyze_button = st.button("🚀 開始綜合評估", type="primary", use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 📈 功能特色")
        st.markdown("• 五維度綜合評估")
        st.markdown("• 技術指標分析")
        st.markdown("• 基本面分析")
        st.markdown("• 交易訊號生成")
        st.markdown("• 風險評估")
        
        st.markdown("---")
        st.markdown("### ⚠️ 風險提示")
        st.markdown("投資有風險，此工具僅供參考。購買前請自行評估，本站不承擔任何相關責任。")
    
    if not analyze_button:
        # 首頁內容
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("👈 請在左側選擇股票並點擊「開始綜合評估」按鈕")
            
            st.subheader("🎯 系統介紹")
            st.markdown("""
            **投資荷密斯**是一個綜合性的股票分析平台，整合了：
            
            - **技術分析**: K線、移動平均線、MACD、RSI、KD等指標
            - **基本面分析**: 財務報表、獲利能力、成長性評估
            - **籌碼分析**: 法人買賣超、主力動向
            - **風險評估**: 波動率、財務風險、估值風險
            - **交易訊號**: 智能買賣建議、進出場點位
            
            ### 📊 評估維度
            1. **技術面** (35%) - 價格趨勢、動能指標
            2. **基本面** (35%) - 財務健康、獲利能力  
            3. **籌碼面** (15%) - 法人動向、資金流向
            4. **風險面** (10%) - 波動風險、財務風險
            5. **動能面** (5%) - 短期動能、趨勢強度
            """)
        
        with col2:
            # 使用本地圖片或移除圖片
            st.markdown("""
            <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;'>
                <h3>💎 投資荷密斯</h3>
                <p>智能投資分析平台</p>
            </div>
            """, unsafe_allow_html=True)
        
        return

    # 執行分析
    with st.spinner(f"🔍 正在為 {stock_code} {stock_name} 進行深度分析..."):
        # 載入數據 - 使用修復後的函數
        data_result = load_stock_data(stock_code)
        
        if not data_result['success']:
            st.error(f"❌ 無法獲取 {stock_code} 的股票數據，請檢查：")
            st.markdown("""
            - 股票代碼是否正確
            - 市場是否在交易時間
            - 網路連線是否正常
            """)
            return

        tech_data = data_result['tech_data']
        fundamental_data = data_result['fundamental_data']
        
        if tech_data is None or tech_data.empty:
            st.error(f"❌ 無法獲取 {stock_code} 的技術數據")
            return

        # 初始化評估器
        evaluator = ComprehensiveEvaluator()
        signal_generator = TradingSignalGenerator()
        
        # 執行各維度評估
        technical_score, tech_result = evaluator.evaluate_technical_strength(tech_data)
        fund_score, fund_result = evaluator.evaluate_fundamental_quality(fundamental_data)
        risk_score, risk_result = evaluator.evaluate_risk_profile(tech_data, fundamental_data)
        momentum_score, momentum_result = evaluator.evaluate_momentum(tech_data)
        
        # 籌碼分析
        chip_score, chip_result = 50, {'score': 50, 'grade': '中性', 'details': ['籌碼數據待更新']}
        if chip_data is not None and not chip_data.empty:
            try:
                stock_chip_data = chip_data[chip_data.index.get_level_values(1) == stock_code]
                if not stock_chip_data.empty:
                    chip_score, chip_result = evaluator.evaluate_chip_flow(stock_chip_data)
            except Exception as e:
                st.warning(f"籌碼分析出現問題: {e}")
        
        # 生成交易訊號
        trading_signal = signal_generator.generate_signal(tech_data, technical_score, market_state)
        
        # 綜合評估
        evaluation = evaluator.generate_comprehensive_evaluation(
            tech_data=tech_data,
            tech_score=technical_score,
            fundamental_data=fundamental_data,
            trading_signal=trading_signal,
            market_state=market_state,
            chip_data=chip_data
        )

    st.success(f"✅ {stock_code} {stock_name} 綜合評估完成！")

    # --- 儀表板佈局 ---
    
    # 頂層總覽
    st.header("📊 投資評估總覽")
    
    # 投資等級顯示
    grade_class = get_grade_color(evaluation.overall_score)
    st.markdown(f'<div class="{grade_class}">🏆 投資等級: {evaluation.investment_grade}</div>', unsafe_allow_html=True)
    
    # 核心論點
    st.markdown(f"**💡 核心投資論點:** {evaluation.core_thesis}")
    
    # 關鍵指標
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("綜合評分", f"{evaluation.overall_score}/100")
    
    with col2:
        risk_class = get_risk_color(evaluation.risk_level)
        st.markdown(f'<div class="{risk_class}">⚠️ 風險等級: {evaluation.risk_level}</div>', unsafe_allow_html=True)
    
    with col3:
        st.metric("交易訊號", trading_signal.signal_type)
    
    with col4:
        st.metric("信心度", f"{trading_signal.confidence:.0f}%")
    
    with col5:
        st.metric("當前股價", f"${tech_data.iloc[-1]['Close']:.2f}")
    
    st.markdown("---")
    
    # 中層：圖表與評估
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 技術分析圖表")
        candlestick_chart = create_candlestick_chart(tech_data, stock_name)
        st.plotly_chart(candlestick_chart, use_container_width=True)
    
    with col2:
        st.subheader("🎯 多維度評估")
        
        # 雷達圖
        radar_chart = create_evaluation_radar_chart(fund_result, tech_result, risk_result, momentum_result, chip_result)
        st.plotly_chart(radar_chart, use_container_width=True)
        
        # 分數儀表板
        st.subheader("📋 各項評分")
        score_col1, score_col2 = st.columns(2)
        
        with score_col1:
            st.plotly_chart(create_score_gauge(technical_score, "技術面"), use_container_width=True)
            st.plotly_chart(create_score_gauge(fund_score, "基本面"), use_container_width=True)
        
        with score_col2:
            st.plotly_chart(create_score_gauge(risk_score, "風險控管", 'reds'), use_container_width=True)
            st.plotly_chart(create_score_gauge(chip_score, "籌碼面"), use_container_width=True)
    
    st.markdown("---")
    
    # 詳細分析區塊
    st.header("🔍 詳細分析報告")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 交易建議", "🏦 基本面", "📊 技術面", "💰 籌碼面", "⚠️ 風險評估"])
    
    with tab1:
        st.subheader("交易訊號與建議")
        
        # 訊號強度顯示
        signal_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
        st.markdown(f"### {signal_emoji[trading_signal.signal_type]} {trading_signal.signal_type} 訊號")
        
        if trading_signal.signal_type != 'HOLD':
            col1, col2, col3 = st.columns(3)
            col1.metric("建議進場價", f"${trading_signal.entry_price:.2f}")
            col2.metric("停損價位", f"${trading_signal.stop_loss:.2f}")
            col3.metric("風險報酬比", f"1:{trading_signal.risk_reward_ratio:.1f}")
            
            if trading_signal.take_profit:
                st.markdown("**🎯 分批獲利了結:**")
                for i, tp in enumerate(trading_signal.take_profit, 1):
                    profit_pct = ((tp - trading_signal.entry_price) / trading_signal.entry_price) * 100
                    st.markdown(f"- 第{i}目標: ${tp:.2f} (+{profit_pct:.1f}%)")
        
        st.markdown("**📋 訊號依據:**")
        for reason in trading_signal.reasons:
            st.markdown(f"- {reason}")
            
        if trading_signal.warnings:
            st.markdown("**⚠️ 風險警告:**")
            for warning in trading_signal.warnings:
                st.warning(warning)
        
        st.markdown(f"**⏱️ 建議持有期間:** {trading_signal.holding_period}")
        st.markdown(f"**💰 倉位建議:** {evaluation.position_suggestion}")
    
    with tab2:
        st.subheader("基本面分析")
        st.markdown(f"#### 評分: {fund_result['score']}/100 (等級: {fund_result.get('grade', 'N/A')})")
        
        if fundamental_data:
            # 關鍵財務指標
            col1, col2, col3 = st.columns(3)
            with col1:
                if 'ROE' in fundamental_data:
                    st.metric("ROE", f"{fundamental_data['ROE']:.1f}%")
                if 'EPS' in fundamental_data:
                    st.metric("EPS", f"${fundamental_data['EPS']:.2f}")
            
            with col2:
                if '毛利率' in fundamental_data:
                    st.metric("毛利率", f"{fundamental_data['毛利率']:.1f}%")
                if '本益比' in fundamental_data:
                    st.metric("本益比", f"{fundamental_data['本益比']:.1f}")
            
            with col3:
                if '營收成長率' in fundamental_data:
                    st.metric("營收成長", f"{fundamental_data['營收成長率']:.1f}%")
                if '負債比率' in fundamental_data:
                    st.metric("負債比率", f"{fundamental_data['負債比率']:.1f}%")
        
        st.markdown("**📈 詳細分析:**")
        for detail in fund_result.get('details', ['基本面數據待更新']):
            st.markdown(f"- {detail}")
    
    with tab3:
        st.subheader("技術面分析")
        st.markdown(f"#### 評分: {tech_result['score']}/100 (趨勢: {tech_result.get('strength', 'N/A')})")
        
        # 技術指標現值
        latest = tech_data.iloc[-1]
        tech_col1, tech_col2, tech_col3 = st.columns(3)
        
        with tech_col1:
            if 'RSI' in latest:
                rsi_color = "red" if latest['RSI'] > 70 else "green" if latest['RSI'] < 30 else "orange"
                st.markdown(f"RSI: <span style='color:{rsi_color}'>{latest['RSI']:.1f}</span>", unsafe_allow_html=True)
            
            if all(x in latest for x in ['K', 'D']):
                kd_signal = "黃金交叉" if latest['K'] > latest['D'] else "死亡交叉"
                st.markdown(f"KD: {kd_signal} (K:{latest['K']:.1f}/D:{latest['D']:.1f})")
        
        with tech_col2:
            if 'MA20' in latest and 'MA60' in latest:
                ma_trend = "多頭" if latest['MA20'] > latest['MA60'] else "空頭"
                st.markdown(f"均線趨勢: {ma_trend}")
            
            if 'Volume_Ratio' in latest:
                vol_signal = "放量" if latest['Volume_Ratio'] > 1.2 else "縮量"
                st.markdown(f"成交量: {vol_signal} ({latest['Volume_Ratio']:.1f}x)")
        
        with tech_col3:
            if 'DIF' in latest and 'DEM' in latest:
                macd_signal = "多頭" if latest['DIF'] > latest['DEM'] else "空頭"
                st.markdown(f"MACD: {macd_signal}")
            
            if 'Volatility_Risk' in latest:
                st.markdown(f"波動率: {latest['Volatility_Risk']:.1f}%")
        
        st.markdown("**📊 技術分析詳情:**")
        for detail in tech_result.get('details', ['技術分析數據待更新']):
            st.markdown(f"- {detail}")
    
    with tab4:
        st.subheader("籌碼面分析")
        st.markdown(f"#### 評分: {chip_result['score']}/100 (等級: {chip_result.get('grade', 'N/A')})")
        
        st.markdown("**🏦 法人動向分析:**")
        for detail in chip_result.get('details', ['籌碼數據更新中...']):
            st.markdown(f"- {detail}")
        
        if chip_data is not None and not chip_data.empty:
            try:
                stock_chip = chip_data[chip_data.index.get_level_values(1) == stock_code]
                if not stock_chip.empty:
                    st.markdown("**📅 近期籌碼變化:**")
                    # 顯示最近3天的籌碼數據
                    recent_chip = stock_chip.head(3)
                    st.dataframe(recent_chip, use_container_width=True)
            except:
                st.info("籌碼數據顯示異常")
    
    with tab5:
        st.subheader("風險評估")
        st.markdown(f"#### 評分: {risk_result['score']}/100 (等級: {evaluation.risk_level})")
        
        st.markdown("**🔍 風險因素分析:**")
        for factor in risk_result.get('factors', ['風險因素分析中...']):
            if "高" in factor or "風險" in factor:
                st.error(f"⚠️ {factor}")
            else:
                st.info(f"✅ {factor}")
        
        st.markdown("**👀 監控重點:**")
        for point in evaluation.monitoring_points:
            st.markdown(f"- {point}")
    
    # 底部免責聲明
    st.markdown("---")
    st.markdown("### 📌 重要提醒")
    st.markdown("""
    - 本評估僅供參考，不構成投資建議
    - 投資有風險，決策前請充分了解
    - 建議配合其他資訊綜合判斷  
    - 過去績效不代表未來表現
    - 請根據個人風險承受度調整投資策略
    """)

if __name__ == "__main__":
    main()