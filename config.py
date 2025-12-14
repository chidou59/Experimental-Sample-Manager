import os
import json
import sys

# 1. 基础路径 (智能判断是 源代码环境 还是 EXE环境)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# -------------------------------------------------------------
# 【核心修改】将配置文件的存储位置改为“用户主目录”，而不是EXE旁边
# 这样无论 EXE 搬到哪里，配置都不会丢！
# Windows 路径示例: C:\Users\YourName\.sample_manager_config\app_settings.json
# -------------------------------------------------------------
USER_HOME = os.path.expanduser("~")
CONFIG_DIR = os.path.join(USER_HOME, ".sample_manager_config")

# 如果这个配置文件夹不存在，就创建一个
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

SETTINGS_FILE = os.path.join(CONFIG_DIR, "app_settings.json")

# 3. 全局数据路径
DATA_ROOT = None


def load_settings():
    """
    尝试从 JSON 文件加载用户的设置
    """
    global DATA_ROOT
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                path = settings.get("data_root")
                if path and os.path.exists(path):
                    DATA_ROOT = path
                    return True
        except Exception as e:
            print(f"读取配置失败: {e}")
    return False


def save_settings(path):
    """
    保存用户选择的路径到 JSON 文件
    """
    global DATA_ROOT
    DATA_ROOT = path

    settings = {"data_root": path}
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False


# 模块加载时，自动尝试读取一次
load_settings()