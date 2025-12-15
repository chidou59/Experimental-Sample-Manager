import os
import subprocess
import shutil
import sys


def build_exe():
    print("🚀 正在准备打包程序...")

    # 1. 确认主文件存在
    main_file = "main.py"
    if not os.path.exists(main_file):
        print(f"❌ 错误：找不到 {main_file}，请确保此脚本在项目根目录运行。")
        return

    # 2. 确认 PyInstaller 已安装
    try:
        import PyInstaller
    except ImportError:
        print("⚠️ 检测到未安装 PyInstaller，正在尝试自动安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 3. 定义打包参数
    app_name = "SampleManager_v2.1"

    # --- 资源文件夹处理 ---
    # Windows下是用分号 ; 分隔，格式为 "源路径;目标路径"
    add_data_cmd = ""
    if os.path.exists("assets"):
        print("📦 检测到 assets 文件夹，正在添加资源...")
        # 注意：这里确保将 assets 文件夹里的内容放进打包后的 assets 目录
        add_data_cmd = '--add-data "assets;assets" '
    else:
        print("⚠️ 警告：未检测到 assets 文件夹，程序背景可能无法显示。")

    # --- 图标处理 (新增功能) ---
    # 自动寻找 assets/Dashboard.ico 作为程序图标
    icon_path = os.path.join("assets", "Dashboard.ico")
    icon_cmd = ""
    if os.path.exists(icon_path):
        print(f"🎨 成功检测到图标文件: {icon_path}，将作为 EXE 图标。")
        icon_cmd = f'--icon="{icon_path}" '
    else:
        print(f"⚠️ 未找到图标文件 ({icon_path})，将使用默认图标。")

    # 4. 组装命令
    # --noconsole: 不显示黑框
    # --onefile: 单文件
    # --clean: 清理缓存
    full_command = f'pyinstaller --noconsole --onefile --name="{app_name}" --clean --windowed '

    # 拼接资源和图标参数
    full_command += add_data_cmd
    full_command += icon_cmd

    # 添加必要的隐藏导入，防止 exe 闪退
    # 针对 PySide6, Matplotlib, Pandas 等常用库的隐式调用
    hidden_imports = [
        "pandas", "matplotlib", "openpyxl", "PIL", "pillow_heif",
        "scipy.spatial.transform._rotation_groups", "PySide6.QtXml"
    ]
    for lib in hidden_imports:
        full_command += f'--hidden-import "{lib}" '

    full_command += "main.py"

    print("-" * 50)
    print(f"🛠️ 执行打包命令: {full_command}")
    print("☕ 打包过程可能需要几分钟，请耐心等待...")
    print("-" * 50)

    # 5. 执行打包
    os.system(full_command)

    # 6. 整理结果
    print("-" * 30)
    if os.path.exists("dist"):
        exe_path = os.path.join("dist", f"{app_name}.exe")
        if os.path.exists(exe_path):
            print(f"✅ 打包成功！")
            print(f"📂 你的软件在: {os.path.abspath(exe_path)}")

            # 尝试自动打开文件夹
            try:
                os.startfile(os.path.abspath("dist"))
            except:
                pass
        else:
            print("❌ 打包看似完成，但在 dist 文件夹中未找到 exe 文件。")
    else:
        print("❌ 打包失败，未生成 dist 文件夹。")


if __name__ == "__main__":
    build_exe()