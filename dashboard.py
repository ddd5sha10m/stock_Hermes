#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票技術分析可視化儀表板
整合現有的技術分析系統，提供互動式Web界面
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 導入你現有的分析模組
from technical_analyzer import analyze_stock_technicals
from main import calculate_technical_score
from trading_signals import TradingSignalGenerator
from stock_list import STOCK_LIST

# 設定頁面配置
st.set_page_config(
    page_title="投資跟密斯 - 股票技術分析儀表板",
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
def load_stock_data(stock_code):
    """載入並快取股票技術分析數據"""
    try:
        stock_ticker = f"{stock_code}.TW"
        return analyze_stock_technicals(stock_ticker)
    except Exception as e:
        st.error(f"無法載入 {stock_code} 的數據: {e}")
        return None

def create_candlestick_chart(data, stock_name):
    """創建K線圖with技術指標疊加"""
    
    # 取最近100個交易日的數據
    recent_data = data.tail(100).copy()
    
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
        title=f'{stock_name} 技術分析圖表',
        xaxis_rangeslider_visible=False,
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

def create_score_radar_chart(score_breakdown):
    """創建評分雷達圖"""
    
    # 定義評分維度（這需要根據你的評分系統調整）
    categories = ['趨勢分析', '動量指標', '布林通道', '成交量分析', '交叉訊號', '多空平衡']
    
    # 模擬各維度分數（實際使用時需要從score_breakdown中提取）
    scores = [75, 68, 82, 60, 45, 70]  # 這裡需要實際解析你的評分詳情
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],  # 閉合圖形
        theta=categories + [categories[0]],
        fill='toself',
        name='當前評分',
        fillcolor='rgba(255, 99, 71, 0.2)',
        line=dict(color='rgba(255, 99, 71, 0.8)', width=2)
    ))
    
    # 添加滿分參考線
    fig.add_trace(go.Scatterpolar(
        r=[100] * (len(categories) + 1),
        theta=categories + [categories[0]],
        fill='toself',
        name='滿分參考',
        fillcolor='rgba(0, 0, 0, 0.05)',
        line=dict(color='rgba(0, 0, 0, 0.3)', width=1, dash='dash')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10)
            )
        ),
        showlegend=True,
        title="技術分析各維度評分",
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
    """主程式"""
    
    st.title("📈 股票荷米斯 - 股票技術分析儀表板")
    st.markdown("---")
    
    # 側邊欄 - 股票選擇
    with st.sidebar:
        st.header("🔍 股票選擇")
        
        # 建立反向對照表 (名稱 -> 代碼)
        stock_options = {f"{code} - {name}": code for code, name in STOCK_LIST.items()}
        
        selected_option = st.selectbox(
            "選擇要分析的股票:",
            options=list(stock_options.keys()),
            index=0
        )
        
        stock_code = stock_options[selected_option]
        stock_name = STOCK_LIST[stock_code]
        
        st.info(f"已選擇: {stock_code} {stock_name}")
        
        # 分析按鈕
        analyze_button = st.button("🚀 開始分析", type="primary")
        
        st.markdown("---")
        st.markdown("### 📊 快速說明")
        st.markdown("""
        - **K線圖**: 顯示價格走勢與技術指標
        - **評分雷達圖**: 各維度技術分析評分
        - **信心度儀表**: 交易訊號可信度
        - **詳細數據**: 完整的分析結果
        """)
    
    # 主要內容區域
    if analyze_button:
        
        with st.spinner(f"正在分析 {stock_code} {stock_name}..."):
            
            # 載入數據
            tech_data = load_stock_data(stock_code)
            
            if tech_data is None or tech_data.empty:
                st.error("❌ 無法載入股票數據，請檢查網路連線或股票代碼")
                return
            
            # 計算技術評分
            technical_score, scoring_details = calculate_technical_score(tech_data)
            
            # 生成交易訊號
            signal_generator = TradingSignalGenerator()
            trading_signal = signal_generator.generate_signal(tech_data, technical_score)
            
            # 獲取最新數據
            latest_data = tech_data.iloc[-1]
            
        # 顯示結果
        st.success(f"✅ {stock_name} 分析完成！")
        
        # 第一行：關鍵指標
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="技術評分",
                value=f"{technical_score}/100",
                delta=f"{technical_score-50}" if technical_score >= 50 else f"{technical_score-50}"
            )
        
        with col2:
            st.metric(
                label="收盤價",
                value=f"${latest_data['Close']:.2f}",
                delta=f"{((latest_data['Close']/latest_data['Close'])-1)*100:.2f}%" if len(tech_data) > 1 else None
            )
        
        with col3:
            signal_color = "🟢" if trading_signal.signal_type == "BUY" else "🔴" if trading_signal.signal_type == "SELL" else "🟡"
            st.metric(
                label="交易訊號",
                value=f"{signal_color} {trading_signal.signal_type}",
                delta=f"信心度 {trading_signal.confidence:.0f}%"
            )
        
        with col4:
            volatility_risk = latest_data.get('Volatility_Risk', 0)
            st.metric(
                label="波動率風險",
                value=f"{volatility_risk:.2f}%",
                delta="高風險" if volatility_risk > 7 else "中等風險" if volatility_risk > 3 else "低風險"
            )
        
        st.markdown("---")
        
        # 第二行：圖表區域
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 K線圖與技術指標")
            candlestick_chart = create_candlestick_chart(tech_data, stock_name)
            st.plotly_chart(candlestick_chart, use_container_width=True)
        
        with col2:
            st.subheader("🎯 評分分析")
            
            # 雷達圖
            radar_chart = create_score_radar_chart(scoring_details)
            st.plotly_chart(radar_chart, use_container_width=True)
            
            # 風險報酬儀表
            st.subheader("⚖️ 風險評估")
            gauge_chart = create_risk_reward_gauge(trading_signal.confidence, volatility_risk)
            st.plotly_chart(gauge_chart, use_container_width=True)
        
        st.markdown("---")
        
        # 第三行：詳細分析
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 評分詳細說明")
            for i, detail in enumerate(scoring_details, 1):
                st.write(f"{i}. {detail}")
        
        with col2:
            st.subheader("💡 交易建議")
            
            # 交易訊號框
            signal_class = f"{trading_signal.signal_type.lower()}-signal"
            st.markdown(f"""
            <div class="metric-container {signal_class}">
                <h4>🎯 交易訊號: {trading_signal.signal_type}</h4>
                <p><strong>信心度:</strong> {trading_signal.confidence:.0f}%</p>
                <p><strong>建議持有期:</strong> {trading_signal.holding_period}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 具體操作建議
            if trading_signal.signal_type != 'HOLD':
                st.write("**💰 具體操作建議:**")
                st.write(f"- 進場價位: ${trading_signal.entry_price}")
                st.write(f"- 停損價位: ${trading_signal.stop_loss}")
                if trading_signal.take_profit:
                    st.write("- 獲利了結:")
                    for i, tp in enumerate(trading_signal.take_profit, 1):
                        percentage = ((tp - trading_signal.entry_price) / trading_signal.entry_price) * 100
                        st.write(f"  第{i}批: ${tp} (+{percentage:.1f}%)")
            
            # 風險警告
            if trading_signal.warnings:
                st.write("**⚠️ 風險警告:**")
                for warning in trading_signal.warnings:
                    st.warning(warning)
        
        st.markdown("---")
        
        # 免責聲明
        st.markdown("""
        ### ⚠️ 重要提醒
        - 本分析僅供參考，不構成投資建議
        - 市場有風險，投資需謹慎
        - 請結合基本面分析做出最終決策
        - 務必做好風險管理和資金控制
        """)
    
    else:
        st.info("👈 請在左側選擇股票並點擊「開始分析」按鈕")
        
        # 顯示範例圖片或說明
        st.markdown("""
        ## 📈 功能特色
        
        ### 🎯 技術分析整合
        - 完整的K線圖與技術指標疊加
        - MA、MACD、RSI、KD、布林通道等主流指標
        - 自動識別關鍵支撐壓力位
        
        ### 📊 智能評分系統
        - 多維度技術分析評分
        - 雷達圖視覺化展示各維度表現
        - 動態風險調整機制
        
        ### 🚀 交易訊號預測
        - AI智能交易訊號生成
        - 信心度量化評估
        - 具體進出場點位建議
        - 風險報酬比計算
        
        ### 🔍 實時數據更新
        - 即時股價數據獲取
        - 快取機制提升載入速度
        - 支援台股上市櫃股票
        """)

if __name__ == "__main__":
    main()