import os
import json

# 1. 基础路径 (代码所在位置)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 用户配置文件路径 (用来“记忆”用户的选择)
# 这个文件会生成在项目根目录下，名叫 app_settings.json
SETTINGS_FILE = os.path.join(BASE_DIR, "app_settings.json")

# 3. 全局数据路径 (先设为 None，表示还不知道存在哪)
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
                # 读取 saved_path 字段
                path = settings.get("data_root")
                # 再次确认这个文件夹还在不在
                if path and os.path.exists(path):
                    DATA_ROOT = path
                    return True
        except Exception as e:
            print(f"读取配置失败: {e}")

    return False


def save_settings(path):
    """
    保存用户选择的路径到 JSON 文件
    :param path: 用户选择的文件夹路径
    """
    global DATA_ROOT
    DATA_ROOT = path  # 更新内存中的变量

    settings = {"data_root": path}
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        print(f"设置已保存: {path}")
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False


# 模块加载时，自动尝试读取一次
load_settings()