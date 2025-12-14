import os
import sys
import tkinter as tk
from tkinter import filedialog
import config
from src.controllers.file_manager import FileManager

print("--- 1. 模拟用户首次打开软件 ---")

# 检查当前配置中是否有路径
if config.DATA_ROOT is None:
    print("系统提示：当前未设置存储路径。")
    print(">>> 正在打开文件夹选择窗口，请选择您想存放数据的文件夹...")

    # 创建一个隐藏的 tkinter 根窗口，否则会多出一个空白的小框框
    root = tk.Tk()
    root.withdraw()

    # 弹出系统原生的文件夹选择框
    user_selected_path = filedialog.askdirectory(title="请选择实验数据存储位置 (例如 D盘/My_Experiments)")

    # 检查用户是否真的选了，还是点了取消
    if user_selected_path:
        print(f"用户选择了路径: {user_selected_path}")

        # 将用户选的路径保存到 settings 中
        config.save_settings(user_selected_path)
    else:
        print("警告：用户取消了选择，无法继续测试。")
        sys.exit()  # 退出程序

else:
    print(f"欢迎回来！已加载存储路径: {config.DATA_ROOT}")
    print("如果要重置路径，请手动删除根目录下的 app_settings.json 文件。")

print("\n--- 2. 启动文件管理器 ---")
# 只有在 config.DATA_ROOT 有值之后，才能启动 Manager
try:
    manager = FileManager()

    print("\n--- 3. 创建测试数据 ---")
    # 创建一个测试项目
    manager.create_project("Interactive_Test_Project", "测试交互式路径选择功能")
    # 创建一个测试试样
    manager.create_sample("Interactive_Test_Project", "Sample_Tk_01", {"note": "这是手动选择路径后创建的"})

    print("\n--- 测试结束 ---")
    print(f"快去你刚才选择的文件夹 [{config.DATA_ROOT}] 看看，有没有生成新的数据？")

except Exception as e:
    print(f"发生错误: {e}")