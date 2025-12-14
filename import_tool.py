import os

# 定义需要忽略的文件夹（这些不需要发给AI）
IGNORE_DIRS = {'.venv', '.idea', '__pycache__', '.git', 'assets', 'My_Experiments_Data'}
# 定义需要读取的文件后缀
INCLUDE_EXTS = {'.py', '.txt', '.md', '.json'}


def export_project():
    output_file = "project_context.txt"
    current_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"正在扫描项目: {current_dir} ...")

    with open(output_file, 'w', encoding='utf-8') as outfile:
        # 写入一个头部说明，告诉新的AI这是什么
        outfile.write("这是我目前的 Python PySide6 项目代码。\n")
        outfile.write("项目结构如下，随后是具体文件内容：\n\n")

        # 1. 遍历文件
        for root, dirs, files in os.walk(current_dir):
            # 修改 dirs 列表以跳过忽略的目录
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                # 只处理指定后缀的文件
                if os.path.splitext(file)[1] not in INCLUDE_EXTS:
                    continue

                # 排除这个脚本自己和生成的文本文件
                if file in ['export_for_ai.py', 'project_context.txt', 'app_settings.json']:
                    continue

                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, current_dir)

                print(f"读取: {rel_path}")

                # 写入文件分隔符和路径
                outfile.write(f"\n{'=' * 20}\n")
                outfile.write(f"File: {rel_path}\n")
                outfile.write(f"{'=' * 20}\n")

                # 写入代码内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        outfile.write(content + "\n")
                except Exception as e:
                    outfile.write(f"# 读取错误: {e}\n")

    print(f"\n✅ 成功！所有代码已导出到: {output_file}")
    print("请打开这个 txt 文件，全选复制，发送给新的对话窗口。")


if __name__ == "__main__":
    export_project()