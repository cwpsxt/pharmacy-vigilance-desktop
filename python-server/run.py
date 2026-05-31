#!/usr/bin/env python3
"""
医院药学药物警戒与运营绩效可视化分析系统 - 桌面客户端后端服务
"""
import os
import sys

# 禁用输出缓冲
os.environ['PYTHONUNBUFFERED'] = '1'

import webbrowser
from threading import Timer

# 获取应用根目录（支持 PyInstaller 打包后的路径）
if getattr(sys, 'frozen', False):
    # PyInstaller 打包后的路径
    APP_ROOT = os.path.dirname(sys.executable)
else:
    # 开发环境路径
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# 设置环境变量
os.environ['APP_ROOT'] = APP_ROOT

from app import create_app

def open_browser():
    """延迟打开浏览器"""
    webbrowser.open('http://localhost:5001')

if __name__ == "__main__":
    # 创建 Flask 应用
    app = create_app()
    
    # 是否自动打开浏览器（仅独立运行时）
    auto_open_browser = os.environ.get('AUTO_OPEN_BROWSER', 'false').lower() == 'true'
    
    print("=" * 50)
    print("医院药学药物警戒与运营绩效可视化分析系统")
    print("=" * 50)
    print(f"应用目录: {APP_ROOT}")
    print(f"访问地址: http://localhost:5001")
    print("=" * 50)
    
    if auto_open_browser:
        Timer(1.5, open_browser).start()
    
    # 启动应用（生产模式，禁用调试）
    app.run(
        host="127.0.0.1",
        port=5001,
        debug=False,
        use_reloader=False
    )
