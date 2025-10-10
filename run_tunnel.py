#!/usr/bin/env python3
"""
内网穿透专用启动脚本
解决WebSocket连接问题
"""

import sys
import subprocess
import os
from pathlib import Path

def run_for_tunnel():
    """为内网穿透优化的启动方式"""
    print("🌐 启动内网穿透模式...")
    print("=" * 50)
    
    try:
        # 导入配置
        sys.path.append(str(Path(__file__).parent))
        from config.settings import WEB_CONFIG
        
        # 设置环境变量禁用WebSocket
        env = os.environ.copy()
        env['STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION'] = 'false'
        env['STREAMLIT_SERVER_ENABLE_CORS'] = 'true'
        env['STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION'] = 'false'
        env['STREAMLIT_SERVER_MAX_UPLOAD_SIZE'] = '200'
        
        # 构建命令
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            "web_app/app.py",
            "--server.port", str(WEB_CONFIG['port']),
            "--server.address", WEB_CONFIG['host'],
            "--server.enableWebsocketCompression", "false",
            "--server.enableCORS", "true",
            "--server.enableXsrfProtection", "false",
            "--server.maxUploadSize", "200",
            "--browser.gatherUsageStats", "false"
        ]
        
        print(f"🌐 本地地址: http://localhost:{WEB_CONFIG['port']}")
        print("📡 请在内网穿透工具中配置以下信息:")
        print(f"   - 本地端口: {WEB_CONFIG['port']}")
        print(f"   - 协议: HTTP")
        print("   - 确保支持WebSocket或禁用WebSocket功能")
        print("\n⚠️  如果仍有WebSocket问题，请尝试以下解决方案:")
        print("   1. 使用支持WebSocket的内网穿透服务 (如ngrok)")
        print("   2. 或者联系节点小宝客服开启WebSocket支持")
        print("   3. 或者使用其他内网穿透工具")
        print("\n🚀 启动中...")
        
        subprocess.run(cmd, env=env)
        
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def main():
    """主函数"""
    print("🌐 内网穿透专用启动器")
    print("适用于节点小宝等内网穿透服务")
    print("=" * 50)
    
    choice = input("是否启动内网穿透模式? (y/n): ").strip().lower()
    if choice in ['y', 'yes', '是']:
        run_for_tunnel()
    else:
        print("👋 已取消启动")

if __name__ == "__main__":
    main()