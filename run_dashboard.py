#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票技術分析儀表板啟動腳本
自動檢查依賴套件並啟動Streamlit應用
"""

import sys
import subprocess
import pkg_resources
import importlib

def check_and_install_packages():
    """檢查並安裝必要的套件"""
    
    required_packages = {
        'streamlit': 'streamlit>=1.28.0',
        'pandas': 'pandas>=2.0.0',
        'numpy': 'numpy>=1.24.0',
        'yfinance': 'yfinance>=0.2.18',
        'pandas_ta': 'pandas-ta>=0.3.14b0',
        'plotly': 'plotly>=5.15.0'
    }
    
    missing_packages = []
    
    for package, requirement in required_packages.items():
        try:
            if package == 'pandas_ta':
                importlib.import_module('pandas_ta')
            else:
                importlib.import_module(package)
            print(f"✓ {package} 已安裝")
        except ImportError:
            missing_packages.append(requirement)
            print(f"✗ {package} 未安裝")
    
    if missing_packages:
        print("\n正在安裝缺少的套件...")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ 成功安裝 {package}")
            except subprocess.CalledProcessError as e:
                print(f"✗ 安裝 {package} 失敗: {e}")
                return False
    
    return True

def check_required_files():
    """檢查必要的程式檔案是否存在"""
    
    required_files = [
        'dashboard.py',
        'technical_analyzer.py',
        'main.py',
        'trading_signals.py',
        'stock_list.py'
    ]
    
    missing_files = []
    
    for file in required_files:
        try:
            with open(file, 'r', encoding='utf-8'):
                print(f"✓ {file} 檔案存在")
        except FileNotFoundError:
            missing_files.append(file)
            print(f"✗ {file} 檔案缺失")
    
    if missing_files:
        print("\n錯誤：以下檔案缺失，請確保所有程式檔案都在同一目錄下：")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    return True

def start_dashboard():
    """啟動Streamlit儀表板"""
    
    print("\n" + "="*50)
    print("🚀 啟動股票技術分析儀表板...")
    print("="*50)
    
    try:
        # 啟動Streamlit應用
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "dashboard.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.serverAddress", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 儀表板已停止運行")
    except Exception as e:
        print(f"\n❌ 啟動失敗: {e}")

def main():
    """主程式"""
    
    print("📈 股票技術分析儀表板 - 啟動檢查")
    print("="*50)
    
    # 檢查Python版本
    if sys.version_info < (3, 8):
        print("❌ 錯誤：需要Python 3.8或更高版本")
        print(f"   當前版本：Python {sys.version}")
        return
    else:
        print(f"✓ Python版本檢查通過: {sys.version}")
    
    print("\n1. 檢查程式檔案...")
    if not check_required_files():
        return
    
    print("\n2. 檢查套件依賴...")
    if not check_and_install_packages():
        print("❌ 套件安裝失敗，請手動執行：pip install -r requirements.txt")
        return
    
    print("\n✅ 所有檢查通過！")
    
    # 啟動儀表板
    start_dashboard()

if __name__ == "__main__":
    main()