class TemplateManager:
    """
    模板管理器：定义不同材料类型的配置。
    包括：显示哪些属性输入框、显示哪些功能卡片。
    """

    TEMPLATES = {
        "micp_sand": {
            "name": "MICP 固化砂柱 (默认)",
            "description": "适用于微生物加固土体实验，关注质量增长与强度。",
            "icon": "🧪",
            # 定义该模板包含的功能卡片 (对应 UI 模块)
            "cards": ["mass_card", "stress_card", "gallery_card"],
            # 定义该模板特有的属性字段
            "attributes": [
                {"key": "concentration", "label": "胶结液浓度", "type": "float", "unit": "M", "default": 0.5},
                {"key": "rounds", "label": "灌注轮数", "type": "int", "unit": "次", "default": 10},
                {"key": "od600", "label": "菌液 OD600", "type": "float", "unit": "", "default": 1.0},
                {"key": "curing_method", "label": "养护方式", "type": "str", "unit": "", "default": "浸泡"}
            ]
        },
        "concrete_std": {
            "name": "普通混凝土 (Concrete)",
            "description": "标准混凝土抗压/抗折实验。",
            "icon": "🧱",
            # 混凝土通常不需要每天称重，所以没有 mass_card
            "cards": ["stress_card", "gallery_card"],
            "attributes": [
                {"key": "w_c_ratio", "label": "水灰比 (w/c)", "type": "float", "unit": "", "default": 0.45},
                {"key": "aggregate_size", "label": "最大骨料粒径", "type": "float", "unit": "mm", "default": 20},
                {"key": "slump", "label": "坍落度", "type": "float", "unit": "mm", "default": 120},
                {"key": "admixture", "label": "外加剂", "type": "str", "unit": "", "default": "无"}
            ]
        },
        "general_material": {
            "name": "通用材料 (General)",
            "description": "适用于金属、岩石、木材等通用力学测试。",
            "icon": "📦",
            "cards": ["stress_card", "gallery_card"],
            "attributes": [
                {"key": "material_source", "label": "材料产地/来源", "type": "str", "unit": "", "default": ""},
                {"key": "treatment", "label": "预处理工艺", "type": "str", "unit": "", "default": "无"},
                {"key": "temperature", "label": "测试温度", "type": "float", "unit": "°C", "default": 25}
            ]
        }
    }

    @staticmethod
    def get_template_names():
        """返回 [(id, name), ...] 供下拉菜单使用"""
        return [(k, v["name"]) for k, v in TemplateManager.TEMPLATES.items()]

    @staticmethod
    def get_template(template_id):
        """获取指定模板的配置，如果不存在则返回默认 MICP"""
        return TemplateManager.TEMPLATES.get(template_id, TemplateManager.TEMPLATES["micp_sand"])