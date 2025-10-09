"""
快速启动脚本
"""

import sys
import subprocess
from pathlib import Path

def install_requirements():
    """安装依赖包"""
    print("正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依赖包安装完成")
        return True
    except subprocess.CalledProcessError:
        print("❌ 依赖包安装失败")
        return False

def run_web_app():
    """运行Web应用"""
    print("启动Web应用...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "web_app/app.py"])
    except KeyboardInterrupt:
        print("\n👋 Web应用已停止")
    except Exception as e:
        print(f"❌ Web应用启动失败: {e}")

def run_backtest():
    """运行回测"""
    print("运行回测示例...")
    try:
        subprocess.run([sys.executable, "src/main.py"])
    except Exception as e:
        print(f"❌ 回测运行失败: {e}")

def main():
    """主函数"""
    print("🚀 Python量化交易平台")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return
    
    print("请选择操作:")
    print("1. 安装依赖包")  
    print("2. 运行Web应用")
    print("3. 运行回测示例")
    print("4. 安装依赖并启动Web应用")
    print("0. 退出")
    
    while True:
        choice = input("\n请输入选择 (0-4): ").strip()
        
        if choice == "0":
            print("👋 再见!")
            break
        elif choice == "1":
            install_requirements()
        elif choice == "2":
            run_web_app()
        elif choice == "3":
            run_backtest()
        elif choice == "4":
            if install_requirements():
                run_web_app()
        else:
            print("❌ 无效选择，请重试")

if __name__ == "__main__":
    main()