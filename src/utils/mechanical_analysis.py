import numpy as np
from scipy import stats


class MechanicalAnalyzer:
    """
    力学分析工具类：专门用于计算应力-应变曲线的特征参数。
    支持：弹性模量(E)、峰值强度(UCS)、韧性(能量吸收)等。
    """

    @staticmethod
    def analyze(data_points):
        """
        主分析函数
        :param data_points: 列表，格式 [{"strain": 1.2, "stress": 300}, ...]
        :return: 字典，包含分析结果
        """
        # 1. 数据预处理：转为 numpy 数组方便计算
        if not data_points or len(data_points) < 5:
            return {"success": False, "msg": "数据点太少，无法进行有效分析"}

        # 提取并排序（按应变从小到大）
        # 必须排序，否则积分和寻找峰值会出错
        sorted_data = sorted(data_points, key=lambda x: x["strain"])
        strain = np.array([p["strain"] for p in sorted_data])
        stress = np.array([p["stress"] for p in sorted_data])

        # 2. 寻找峰值点 (UCS)
        peak_idx = np.argmax(stress)
        peak_stress = stress[peak_idx]
        peak_strain = strain[peak_idx]

        # 3. 计算残余强度 (Residual Strength)
        # 策略：取最后 5 个点的平均值，避免最后一个点是噪点
        if len(stress) > 5:
            residual_stress = np.mean(stress[-5:])
        else:
            residual_stress = stress[-1]

        # 4. 计算弹性模量 (Elastic Modulus, E)
        # 策略：智能寻找“最线性”的上升段
        e_modulus, r_squared, fit_line = MechanicalAnalyzer._calculate_elastic_modulus(strain, stress, peak_idx)

        # 5. 计算韧性/断裂能 (Toughness)
        # 定义：应力-应变曲线下的面积，代表材料破坏前吸收的能量。
        # 单位推导：
        # Stress (kPa) = kN/m²
        # Strain (无量纲) = m/m
        # Area = kPa * 1 = kN/m² * m/m = kN*m / m³ = kJ/m³ (单位体积吸收的能量)
        # 注意：传入的 strain 是百分比 (如 1.5)，积分时要除以 100 还原为小数
        toughness = np.trapz(stress, strain / 100.0)

        return {
            "success": True,
            "peak_stress": peak_stress,  # 峰值应力 (kPa)
            "peak_strain": peak_strain,  # 峰值应变 (%)
            "residual_stress": residual_stress,  # 残余强度 (kPa)
            "elastic_modulus": e_modulus,  # 弹性模量 (MPa)
            "r_squared": r_squared,  # 拟合优度 (越接近1越好)
            "toughness": toughness,  # 韧性 (kJ/m³)
            "fit_line": fit_line,  # 拟合直线的坐标点 [(x1,y1), (x2,y2)] 用于画图
        }

    @staticmethod
    def _calculate_elastic_modulus(strain, stress, peak_idx):
        """
        计算弹性模量的核心算法。
        学术惯例：取峰值应力 30%~70% 之间的直线段进行拟合。
        原因：
        1. 避开 0%~30% 的“压密阶段”（孔隙闭合，非线性）。
        2. 避开 70%~100% 的“塑性屈服阶段”。
        """
        try:
            # 截取峰值前的段
            pre_peak_strain = strain[:peak_idx]
            pre_peak_stress = stress[:peak_idx]

            if len(pre_peak_strain) < 5:
                return 0, 0, None

            # 定义搜索区间：最大应力的 30% 到 70%
            max_s = np.max(pre_peak_stress)
            mask = (pre_peak_stress > 0.3 * max_s) & (pre_peak_stress < 0.7 * max_s)

            target_strain = pre_peak_strain[mask]
            target_stress = pre_peak_stress[mask]

            # 如果筛选出的点太少（比如数据很稀疏），放宽范围到 10%-90%
            if len(target_strain) < 3:
                mask = (pre_peak_stress > 0.1 * max_s) & (pre_peak_stress < 0.9 * max_s)
                target_strain = pre_peak_strain[mask]
                target_stress = pre_peak_stress[mask]

            # 还是太少？那就取前 50% 的所有点
            if len(target_strain) < 2:
                limit_idx = int(peak_idx * 0.5)
                target_strain = strain[:limit_idx]
                target_stress = stress[:limit_idx]

            if len(target_strain) < 2:
                return 0, 0, None

            # 线性回归 (Linear Regression) y = kx + b
            slope, intercept, r_value, p_value, std_err = stats.linregress(target_strain, target_stress)

            # 单位换算：
            # 斜率 slope 单位是 kPa / %
            # E = Stress / Strain_decimal
            #   = Stress / (Strain_percent / 100)
            #   = 100 * slope (kPa)
            #   = (100 * slope) / 1000 (MPa)
            #   = slope / 10 (MPa)
            e_modulus_mpa = slope / 10.0

            # 生成拟合线数据（用于在图上画红线）
            # 我们让线稍微长一点，画出整个弹性阶段
            start_x = 0
            end_x = target_strain[-1] * 1.5  # 延伸一点
            x_fit = np.linspace(start_x, end_x, 10)
            y_fit = slope * x_fit + intercept

            fit_line = list(zip(x_fit, y_fit))

            return e_modulus_mpa, r_value ** 2, fit_line

        except Exception as e:
            print(f"计算弹性模量出错: {e}")
            return 0, 0, None