import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import warnings
import numpy as np
warnings.filterwarnings('ignore')

# 導入所有需要的分析模組
from technical_analyzer import analyze_stock_technicals
from fundamental_analyzer import analyze_stock_fundamentals
from main import calculate_technical_score # 我們仍然需要它來取得原始技術分數
from trading_signals import TradingSignalGenerator
from comprehensive_evaluator import ComprehensiveEvaluator
from stock_list import STOCK_LIST

# 設定頁面配置
st.set_page_config(
    page_title="投資荷密斯 - 股票技術分析儀表板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義CSS樣式
st.markdown("""
<style>
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
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #ff4444, #ffaa00, #44ff44);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # 快取5分鐘
def load_all_data(stock_code):
    """
    一次性載入所有需要的數據，並自動嘗試 .TW 和 .TWO 後綴。
    """
    print(f"\n--- 開始載入 {stock_code} 的數據 ---")
    
    # 1. 優先嘗試 .TW (上市市場)
    ticker_tw = f"{stock_code}.TW"
    print(f"嘗試使用 {ticker_tw} (上市市場)...")
    tech_data = analyze_stock_technicals(ticker_tw)
    
    successful_ticker = ""

    # 2. 檢查 .TW 的結果
    if tech_data is not None and not tech_data.empty:
        # .TW 成功
        successful_ticker = ticker_tw
        print(f"成功使用 {successful_ticker} 獲取技術數據。")
    else:
        # 3. 如果 .TW 失敗，則切換至 .TWO (上櫃市場)
        print(f"使用 {ticker_tw} 失敗或無數據，切換至 .TWO 再次嘗試...")
        ticker_two = f"{stock_code}.TWO"
        tech_data = analyze_stock_technicals(ticker_two)
        
        # 4. 檢查 .TWO 的結果
        if tech_data is not None and not tech_data.empty:
            # .TWO 成功
            successful_ticker = ticker_two
            print(f"成功使用 {successful_ticker} 獲取技術數據。")
        else:
            # 兩種嘗試都失敗
            print(f"!!! 使用 {ticker_tw} 和 {ticker_two} 均無法獲取數據。")
            return None, None

    # 5. 使用成功的 ticker 來獲取基本面數據
    print(f"繼續使用 {successful_ticker} 獲取基本面數據...")
    fundamental_data = analyze_stock_fundamentals(successful_ticker)
    
    return tech_data, fundamental_data

def create_candlestick_chart(data, stock_name):
    """創建K線圖with技術指標疊加"""
    
    # 取最近365個交易日的數據
    recent_data = data.tail(365).copy()
    
    # 創建子圖
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=(
            f'{stock_name} - K線圖 & 技術指標',
            'MACD',
            'RSI & KD',
            '成交量'
        ),
        row_heights=[0.5, 0.2, 0.2, 0.1]
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
                name='MACD-DIF',
                line=dict(color='blue', width=1.5)
            ),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=recent_data.index,
                y=recent_data['DEM'],
                mode='lines',
                name='MACD-DEM',
                line=dict(color='red', width=1.5)
            ),
            row=2, col=1
        )
        fig.add_trace(
            go.Bar(
                x=recent_data.index,
                y=recent_data['OSC'],
                name='MACD-OSC',
                marker_color=np.where(recent_data['OSC'] >= 0, '#ff4444', '#00aa00'),
                opacity=0.6
            ),
            row=2, col=1
        )
    
    # RSI & KD
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
    
    if all(col in recent_data.columns for col in ['K', 'D']):
        fig.add_trace(
            go.Scatter(
                x=recent_data.index,
                y=recent_data['K'],
                mode='lines',
                name='K線',
                line=dict(color='blue', width=1.5),
                yaxis='y4'
            ),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=recent_data.index,
                y=recent_data['D'],
                mode='lines',
                name='D線',
                line=dict(color='red', width=1.5),
                yaxis='y4'
            ),
            row=3, col=1
        )
        # KD超買超賣線
        fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.3, row=3, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.3, row=3, col=1)
    
    # 成交量
    fig.add_trace(
        go.Bar(
            x=recent_data.index,
            y=recent_data['Volume'],
            name='成交量',
            marker_color='lightblue',
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
    title=dict(
        text=f"{stock_name} 技術分析圖表",
        x=0.5,   # 水平置中
        y=0.99,  # 調高一點
        xanchor="center",
        yanchor="top"
    ),
    xaxis_rangeslider_visible=False,
    height=850,
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

def create_evaluation_radar_chart(fund_result, tech_result, risk_result, momentum_result):
    """【全新】創建綜合評估雷達圖"""
    categories = ['基本面', '技術面', '風險面', '動能面']
    scores = [
        fund_result['score'],
        tech_result['score'],
        risk_result['score'],
        momentum_result['score']
    ]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=categories + [categories[0]],
        fill='toself',
        name='綜合評估',
        fillcolor='rgba(78, 205, 196, 0.2)',
        line=dict(color='rgba(78, 205, 196, 0.8)', width=2)
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        title="四大維度評估雷達圖",
        height=400
    )
    return fig


def create_risk_reward_gauge(confidence, volatility_risk):
    """創建風險報酬儀表圖"""
    
    fig = go.Figure()
    
    # 信心度儀表
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=confidence,
        domain={'x': [0, 0.5], 'y': [0, 1]},
        title={'text': "交易信心度 (%)"},
        delta={'reference': 70},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkgreen"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    # 風險儀表
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=volatility_risk,
        domain={'x': [0.5, 1], 'y': [0, 1]},
        title={'text': "波動率風險 (%)"},
        delta={'reference': 5},
        gauge={
            'axis': {'range': [None, 15]},
            'bar': {'color': "darkred"},
            'steps': [
                {'range': [0, 3], 'color': "lightgreen"},
                {'range': [3, 7], 'color': "yellow"},
                {'range': [7, 15], 'color': "lightcoral"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 10
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def main():
    st.title("💎 投資荷米斯 - 綜合投資價值評估儀表板")
    
    with st.sidebar:
        st.header("⚙️ 分析設定")
        stock_options = {f"{code} - {name}": code for code, name in STOCK_LIST.items()}
        selected_option = st.selectbox("選擇要分析的股票:", options=list(stock_options.keys()), index=0)
        stock_code = stock_options[selected_option]
        stock_name = STOCK_LIST[stock_code]
        analyze_button = st.button("🚀 開始評估", type="primary", use_container_width=True)
    
    if not analyze_button:
        st.info("👈 請在左側選擇股票並點擊「開始評估」按鈕。投資有風險，此工具僅提供參考，購買前仍需自行評估，本站不承擔任何相關責任。")
        st.markdown("---")
        st.image("/Users/wdwddaniel/Downloads/stockH.png")
        return

    with st.spinner(f"正在為 {stock_code} {stock_name} 進行深度評估..."):
        # 1. 載入所有數據
        tech_data, fundamental_data = load_all_data(stock_code)
        if tech_data is None or tech_data.empty:
            st.error(f"❌ 無法獲取 {stock_code} 的技術資料，無法產生報告。")
            return

        # 2. 執行所有必要的計算與評估
        technical_score, _ = calculate_technical_score(tech_data)
        signal_generator = TradingSignalGenerator()
        trading_signal = signal_generator.generate_signal(tech_data, technical_score)
        
        evaluator = ComprehensiveEvaluator()
        fund_score, fund_result = evaluator.evaluate_fundamental_quality(fundamental_data)
        tech_score_norm, tech_result = evaluator.evaluate_technical_strength(tech_data, technical_score)
        risk_score, risk_result = evaluator.evaluate_risk_profile(tech_data, fundamental_data)
        momentum_score, momentum_result = evaluator.evaluate_momentum(tech_data)
        evaluation = evaluator.generate_comprehensive_evaluation(tech_data, technical_score, fundamental_data, trading_signal)
    
    st.success(f"✅ {stock_code} {stock_name} 評估完成！")

    # --- 儀表板佈局 ---
    
    # 頂層總覽
    st.header(f"💎 {evaluation.investment_grade}")
    st.markdown(f"**核心投資論點:** *{evaluation.core_thesis}*")

    # 四大關鍵指標
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("綜合評分", f"{evaluation.overall_score}/100", delta=f"{evaluation.overall_score - 50:.1f}")
    col2.metric("風險等級", evaluation.risk_level)
    col3.metric("倉位建議", evaluation.position_suggestion)
    col4.metric("建議投資期間", evaluation.time_horizon)
    
    st.markdown("---")

    # 中層圖表與關鍵點
    left_col, right_col = st.columns([2, 1.2])
    with left_col:
        st.subheader("📈 K線圖與技術指標")
        candlestick_chart = create_candlestick_chart(tech_data, stock_name)
        st.plotly_chart(candlestick_chart, use_container_width=True)
        
    with right_col:
        st.subheader("🎯 四大維度評估")
        radar_chart = create_evaluation_radar_chart(fund_result, tech_result, risk_result, momentum_result)
        st.plotly_chart(radar_chart, use_container_width=True)

        with st.container():
            st.markdown("**✅ 主要優勢:**")
            for strength in evaluation.key_strengths:
                st.markdown(f" - {strength}")
            
            st.markdown("**⚠️ 主要風險:**")
            for risk in evaluation.key_risks:
                st.markdown(f" - {risk}")

    st.markdown("---")

    # 底層詳細報告
    st.subheader("📋 詳細分析與建議")
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 交易訊號", "🏦 基本面分析", "📊 技術面分析", "👀 監控重點"])

    with tab1:
        st.markdown(f"#### {trading_signal.signal_type} ({trading_signal.confidence:.0f}% 信心度)")
        if trading_signal.signal_type != 'HOLD':
            c1, c2, c3 = st.columns(3)
            c1.metric("建議進場價", f"${trading_signal.entry_price}")
            c2.metric("建議停損價", f"${trading_signal.stop_loss}")
            c3.metric("風險報酬比", f"1:{trading_signal.risk_reward_ratio}")
        st.markdown("**訊號依據:**")
        for reason in trading_signal.reasons:
            st.markdown(f"- {reason}")
        if trading_signal.warnings:
            st.markdown("**風險警告:**")
            for warning in trading_signal.warnings:
                st.warning(warning)
    
    with tab2:
        st.markdown(f"#### 基本面評分: {fund_result['score']}/100 (等級: {fund_result['grade']})")
        for detail in fund_result['details']:
            st.markdown(f"- {detail}")

    with tab3:
        st.markdown(f"#### 技術面評分: {tech_result['score']}/100 (趨勢: {tech_result['strength']})")
        # 這裡我們直接使用 main.py 產出的 tech_details
        _, tech_details = calculate_technical_score(tech_data)
        for detail in tech_details:
            st.markdown(f"- {detail}")
            
    with tab4:
        st.markdown("#### 建議持續關注以下指標變化:")
        for point in evaluation.monitoring_points:
            st.markdown(f"- {point}")

if __name__ == "__main__":
    main()