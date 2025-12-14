import pandas as pd
import os


class DataImporter:
    @staticmethod
    def load_stress_strain_data(file_path):
        """
        读取 CSV 或 Excel 文件，智能寻找应力应变列。
        返回格式: ([{"strain": 0.1, "stress": 20}, ...], "成功导入信息")
        """
        try:
            ext = os.path.splitext(file_path)[1].lower()

            # 1. 读取文件到 DataFrame
            if ext == '.csv':
                # 尝试不同的编码，防止中文乱码
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except:
                    try:
                        df = pd.read_csv(file_path, encoding='gbk')
                    except:
                        return None, "CSV读取失败，请检查编码"
            elif ext in ['.xls', '.xlsx']:
                df = pd.read_excel(file_path)
            else:
                return None, "不支持的文件格式"

            # 2. 智能清洗数据
            df = df.dropna()

            # 3. 寻找列名
            columns = df.columns.astype(str).tolist()

            stress_col = None
            strain_col = None

            for col in columns:
                c_lower = col.lower()
                if 'stress' in c_lower or '应力' in c_lower or 'kpa' in c_lower or 'mpa' in c_lower:
                    if not stress_col: stress_col = col
                if 'strain' in c_lower or '应变' in c_lower or '%' in c_lower:
                    if not strain_col: strain_col = col

            # 如果没自动找到，就默认取前两列（第一列应变，第二列应力，这是通常的机器输出格式）
            if not stress_col or not strain_col:
                if len(columns) >= 2:
                    strain_col = columns[0]  # 假设第一列是位移/应变
                    stress_col = columns[1]  # 假设第二列是力/应力
                else:
                    return None, "无法识别数据列，请确保文件至少有两列数据"

            # 4. 提取数据并转换为标准格式
            result = []
            for index, row in df.iterrows():
                try:
                    s_val = float(row[stress_col])
                    e_val = float(row[strain_col])
                    result.append({"strain": e_val, "stress": s_val})
                except:
                    continue  # 跳过无法转为数字的行

            # 按照应变排序，确保画图不乱
            result.sort(key=lambda x: x["strain"])

            return result, f"成功导入 {len(result)} 条数据"

        except Exception as e:
            return None, f"读取失败: {str(e)}"