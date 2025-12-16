import os
import json
import shutil
import copy
import random  # 新增引用，用于生成随机演示数据
from datetime import datetime
import config
from src.utils.image_helper import ImageHelper


class FileManager:
    def __init__(self):
        if not config.DATA_ROOT:
            raise ValueError("错误：未设置数据存储路径！")
        os.makedirs(config.DATA_ROOT, exist_ok=True)
        self.root_meta_path = os.path.join(config.DATA_ROOT, "root_meta.json")
        if not os.path.exists(self.root_meta_path):
            self._save_root_meta({"projects_order": []})

        # === 性能优化：内存缓存 ===
        # 结构: { "project_name": { "sample_id": {sample_info_dict}, ... } }
        self._sample_cache = {}
        # 结构: { "project_name": ["s1", "s2", ...] }
        self._structure_cache = None

    def _load_root_meta(self):
        try:
            with open(self.root_meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"projects_order": []}

    def _save_root_meta(self, data):
        try:
            with open(self.root_meta_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存元数据失败: {e}")

    # === 缓存辅助方法 ===
    def _invalidate_structure_cache(self):
        """当项目结构发生变化（增删改）时，标记结构缓存无效"""
        self._structure_cache = None

    def _update_sample_cache(self, project_name, sample_id, data):
        """更新单个试样的缓存"""
        if project_name not in self._sample_cache:
            self._sample_cache[project_name] = {}
        self._sample_cache[project_name][sample_id] = data

    def _remove_sample_from_cache(self, project_name, sample_id):
        """从缓存中移除"""
        if project_name in self._sample_cache and sample_id in self._sample_cache[project_name]:
            del self._sample_cache[project_name][sample_id]

    def create_project(self, project_name, description=""):
        project_path = os.path.join(config.DATA_ROOT, project_name)
        try:
            if os.path.exists(project_path): return False
            os.makedirs(project_path)
            project_info = {
                "name": project_name,
                "description": description,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "project",
                "samples_order": []
            }
            with open(os.path.join(project_path, "project_info.json"), 'w', encoding='utf-8') as f:
                json.dump(project_info, f, ensure_ascii=False, indent=4)

            meta = self._load_root_meta()
            if project_name not in meta["projects_order"]:
                meta["projects_order"].append(project_name)
                self._save_root_meta(meta)

            self._invalidate_structure_cache()  # 刷新结构缓存
            return True
        except Exception as e:
            print(f"Error: {e}");
            return False

    def create_sample(self, project_name, sample_id, sample_data):
        project_path = os.path.join(config.DATA_ROOT, project_name)
        sample_path = os.path.join(project_path, sample_id)
        try:
            if not os.path.exists(project_path): return False
            if os.path.exists(sample_path): return False
            os.makedirs(sample_path)
            os.makedirs(os.path.join(sample_path, "images"))
            os.makedirs(os.path.join(sample_path, "images", "thumbnails"))

            data_to_save = sample_data.copy()
            if "icon_path" in data_to_save: del data_to_save["icon_path"]

            sample_full_info = {
                "id": sample_id,
                "parent_project": project_name,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "weight_records": [],
                **data_to_save
            }
            # 写入磁盘
            with open(os.path.join(sample_path, "sample_info.json"), 'w', encoding='utf-8') as f:
                json.dump(sample_full_info, f, ensure_ascii=False, indent=4)

            # 更新项目列表
            p_json_path = os.path.join(project_path, "project_info.json")
            if os.path.exists(p_json_path):
                with open(p_json_path, 'r', encoding='utf-8') as f:
                    p_data = json.load(f)
                if "samples_order" not in p_data: p_data["samples_order"] = []
                if sample_id not in p_data["samples_order"]: p_data["samples_order"].append(sample_id)
                with open(p_json_path, 'w', encoding='utf-8') as f:
                    json.dump(p_data, f, ensure_ascii=False, indent=4)

            # 更新缓存
            self._update_sample_cache(project_name, sample_id, sample_full_info)
            self._invalidate_structure_cache()
            return True
        except Exception as e:
            print(f"Error creating sample: {e}");
            return False

    def update_sample_info(self, project_name, sample_id, new_data):
        try:
            # 先获取现有数据（优先从缓存拿）
            data = self.get_sample_info(project_name, sample_id)
            if not data: return False

            # 这里的逻辑保持不变
            editable_fields = [
                "description", "date_prep", "date_complete", "date_demold", "date_test", "initial_mass",
                "shape", "radius", "height", "side_length", "length", "width", "icon_emoji",
                "recipe", "key_variable", "key_variable_name"
            ]

            for field in editable_fields:
                if field in new_data:
                    data[field] = new_data[field]

            # 写入磁盘
            json_path = os.path.join(config.DATA_ROOT, project_name, sample_id, "sample_info.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            # 更新缓存
            self._update_sample_cache(project_name, sample_id, data)
            return True
        except Exception as e:
            print(f"更新试样信息失败: {e}")
            return False

    def get_project_structure(self):
        # === 缓存命中 ===
        if self._structure_cache is not None:
            return self._structure_cache

        # === 缓存未命中，重新扫描 ===
        structure = {}
        if not os.path.exists(config.DATA_ROOT): return structure
        meta = self._load_root_meta()
        saved_order = meta.get("projects_order", [])
        existing_projects = []
        try:
            items = os.listdir(config.DATA_ROOT)
            for item in items:
                p_path = os.path.join(config.DATA_ROOT, item)
                if os.path.isdir(p_path) and os.path.exists(os.path.join(p_path, "project_info.json")):
                    existing_projects.append(item)
        except:
            pass

        final_projects = []
        for p in saved_order:
            if p in existing_projects: final_projects.append(p)
        for p in existing_projects:
            if p not in final_projects: final_projects.append(p)

        for project_name in final_projects:
            structure[project_name] = []
            project_path = os.path.join(config.DATA_ROOT, project_name)
            p_info_path = os.path.join(project_path, "project_info.json")
            saved_sample_order = []
            try:
                with open(p_info_path, 'r', encoding='utf-8') as f:
                    saved_sample_order = json.load(f).get("samples_order", [])
            except:
                pass

            existing_samples = []
            try:
                sub_items = os.listdir(project_path)
                for sub in sub_items:
                    s_path = os.path.join(project_path, sub)
                    if os.path.isdir(s_path) and os.path.exists(os.path.join(s_path, "sample_info.json")):
                        existing_samples.append(sub)
            except:
                pass

            final_samples = []
            for s in saved_sample_order:
                if s in existing_samples: final_samples.append(s)
            for s in existing_samples:
                if s not in final_samples: final_samples.append(s)

            structure[project_name] = final_samples

        # 存入缓存
        self._structure_cache = structure
        return structure

    def update_structure_order(self, new_structure_dict):
        new_projects_order = list(new_structure_dict.keys())
        self._save_root_meta({"projects_order": new_projects_order})
        for project_name, samples_list in new_structure_dict.items():
            p_info_path = os.path.join(config.DATA_ROOT, project_name, "project_info.json")
            if os.path.exists(p_info_path):
                try:
                    with open(p_info_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    data["samples_order"] = samples_list
                    with open(p_info_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                except Exception as e:
                    print(f"保存试样顺序失败 {project_name}: {e}")

        # 结构变了，更新缓存
        self._structure_cache = new_structure_dict

    def rename_project(self, old_name, new_name):
        old_path = os.path.join(config.DATA_ROOT, old_name)
        new_path = os.path.join(config.DATA_ROOT, new_name)
        if not os.path.exists(old_path) or os.path.exists(new_path): return False
        try:
            os.rename(old_path, new_path)
            json_path = os.path.join(new_path, "project_info.json")
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f: data = json.load(f)
                data['name'] = new_name
                with open(json_path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)
            meta = self._load_root_meta()
            if old_name in meta["projects_order"]:
                idx = meta["projects_order"].index(old_name)
                meta["projects_order"][idx] = new_name
                self._save_root_meta(meta)

            # 清理旧缓存，结构缓存失效
            if old_name in self._sample_cache:
                del self._sample_cache[old_name]
            self._invalidate_structure_cache()
            return True
        except Exception as e:
            print(f"重命名项目失败: {e}");
            return False

    def rename_sample(self, project_name, old_id, new_id):
        base_path = os.path.join(config.DATA_ROOT, project_name)
        old_path = os.path.join(base_path, old_id)
        new_path = os.path.join(base_path, new_id)
        if not os.path.exists(old_path) or os.path.exists(new_path): return False
        try:
            os.rename(old_path, new_path)
            json_path = os.path.join(new_path, "sample_info.json")
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f: data = json.load(f)
                data['id'] = new_id
                with open(json_path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)
            p_info_path = os.path.join(base_path, "project_info.json")
            if os.path.exists(p_info_path):
                with open(p_info_path, 'r', encoding='utf-8') as f:
                    p_data = json.load(f)
                if "samples_order" in p_data and old_id in p_data["samples_order"]:
                    idx = p_data["samples_order"].index(old_id)
                    p_data["samples_order"][idx] = new_id
                    with open(p_info_path, 'w', encoding='utf-8') as f: json.dump(p_data, f, ensure_ascii=False,
                                                                                  indent=4)
            # 清理缓存
            self._remove_sample_from_cache(project_name, old_id)
            self._invalidate_structure_cache()
            return True
        except Exception as e:
            print(f"重命名试样失败: {e}");
            return False

    def delete_project(self, project_name):
        path = os.path.join(config.DATA_ROOT, project_name)
        try:
            shutil.rmtree(path)
            meta = self._load_root_meta()
            if project_name in meta["projects_order"]:
                meta["projects_order"].remove(project_name)
                self._save_root_meta(meta)

            if project_name in self._sample_cache:
                del self._sample_cache[project_name]
            self._invalidate_structure_cache()
            return True
        except Exception as e:
            print(f"删除项目失败: {e}");
            return False

    def delete_sample(self, project_name, sample_id):
        path = os.path.join(config.DATA_ROOT, project_name, sample_id)
        try:
            shutil.rmtree(path)
            p_info_path = os.path.join(config.DATA_ROOT, project_name, "project_info.json")
            if os.path.exists(p_info_path):
                with open(p_info_path, 'r', encoding='utf-8') as f:
                    p_data = json.load(f)
                if "samples_order" in p_data and sample_id in p_data["samples_order"]:
                    p_data["samples_order"].remove(sample_id)
                    with open(p_info_path, 'w', encoding='utf-8') as f: json.dump(p_data, f, ensure_ascii=False,
                                                                                  indent=4)
            self._remove_sample_from_cache(project_name, sample_id)
            self._invalidate_structure_cache()
            return True
        except Exception as e:
            print(f"删除试样失败: {e}");
            return False

    def get_sample_info(self, project_name, sample_id):
        # === 缓存优化 ===
        # 1. 检查内存缓存
        if project_name in self._sample_cache and sample_id in self._sample_cache[project_name]:
            return self._sample_cache[project_name][sample_id]

        # 2. 从磁盘读取并存入缓存
        try:
            json_path = os.path.join(config.DATA_ROOT, project_name, sample_id, "sample_info.json")
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._update_sample_cache(project_name, sample_id, data)
                return data
        except:
            return None

    def add_file_to_sample(self, project_name, sample_id, source_path):
        """
        添加文件到试样。如果是 HEIC，自动转换为 JPG。
        """
        try:
            base_dir = os.path.join(config.DATA_ROOT, project_name, sample_id, "images")
            thumb_dir = os.path.join(base_dir, "thumbnails")
            os.makedirs(thumb_dir, exist_ok=True)

            filename = os.path.basename(source_path)
            name, ext = os.path.splitext(filename)
            ext_lower = ext.lower()

            target_path = ""

            # 如果是 HEIC，直接转为 JPG 保存，不存原件
            if ext_lower == '.heic':
                new_filename = name + ".jpg"
                target_path = os.path.join(base_dir, new_filename)

                # 转换并保存
                if not ImageHelper.convert_to_jpg(source_path, target_path):
                    print(f"HEIC 转换失败: {source_path}")
                    return None

                filename = new_filename
                ext_lower = '.jpg'
            else:
                target_path = os.path.join(base_dir, filename)
                shutil.copy(source_path, target_path)

            if ext_lower in ['.png', '.jpg', '.jpeg', '.tif', '.bmp']:
                thumb_path = os.path.join(thumb_dir, filename)
                ImageHelper.generate_thumbnail(target_path, thumb_path)

            return target_path
        except Exception as e:
            print(f"Add file error: {e}")
            return None

    def get_sample_files(self, project_name, sample_id):
        try:
            base_dir = os.path.join(config.DATA_ROOT, project_name, sample_id, "images")
            thumb_dir = os.path.join(base_dir, "thumbnails")
            if not os.path.exists(base_dir): return []
            files_list = []

            valid_exts = [
                '.png', '.jpg', '.jpeg', '.tif', '.bmp', '.heic',
                '.pdf', '.xls', '.xlsx', '.csv',
                '.txt', '.doc', '.docx'
            ]

            for f in os.listdir(base_dir):
                if os.path.isdir(os.path.join(base_dir, f)): continue
                ext = os.path.splitext(f)[1].lower()
                if ext in valid_exts:
                    file_info = {
                        "name": f,
                        "path": os.path.join(base_dir, f),
                        "type": "image" if ext in ['.png', '.jpg', '.jpeg', '.tif', '.bmp', '.heic'] else "file",
                        "ext": ext
                    }
                    if file_info["type"] == "image":
                        thumb_path = os.path.join(thumb_dir, f)
                        file_info["thumb"] = thumb_path if os.path.exists(thumb_path) else file_info["path"]

                    files_list.append(file_info)
            return files_list
        except:
            return []

    def delete_file(self, file_path):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                directory = os.path.dirname(file_path)
                filename = os.path.basename(file_path)
                thumb_path = os.path.join(directory, "thumbnails", filename)
                if os.path.exists(thumb_path): os.remove(thumb_path)
                return True
            return False
        except:
            return False

    def add_weight_record(self, project_name, sample_id, record):
        try:
            data = self.get_sample_info(project_name, sample_id)
            if not data: return False

            if "weight_records" not in data: data["weight_records"] = []
            data["weight_records"].append(record)
            data["weight_records"].sort(key=lambda x: x["days"] if isinstance(x["days"], (int, float)) else -1)

            # 更新磁盘和缓存
            json_path = os.path.join(config.DATA_ROOT, project_name, sample_id, "sample_info.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self._update_sample_cache(project_name, sample_id, data)
            return True
        except:
            return False

    def update_weight_record(self, project_name, sample_id, index, new_record):
        try:
            data = self.get_sample_info(project_name, sample_id)
            if not data: return False

            records = data.get("weight_records", [])
            if 0 <= index < len(records):
                records[index] = new_record
                records.sort(key=lambda x: x["days"] if isinstance(x["days"], (int, float)) else -1)
                data["weight_records"] = records

                json_path = os.path.join(config.DATA_ROOT, project_name, sample_id, "sample_info.json")
                with open(json_path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)
                self._update_sample_cache(project_name, sample_id, data)
                return True
            return False
        except:
            return False

    def delete_weight_record(self, project_name, sample_id, index):
        try:
            data = self.get_sample_info(project_name, sample_id)
            if not data: return False

            records = data.get("weight_records", [])
            if 0 <= index < len(records):
                del records[index]
                data["weight_records"] = records

                json_path = os.path.join(config.DATA_ROOT, project_name, sample_id, "sample_info.json")
                with open(json_path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)
                self._update_sample_cache(project_name, sample_id, data)
                return True
            return False
        except:
            return False

    def batch_copy_weights(self, project_name, source_id, target_ids, overwrite=False):
        source_info = self.get_sample_info(project_name, source_id)
        if not source_info: return False

        source_records = source_info.get("weight_records", [])
        if not source_records: return True

        success_count = 0
        for tid in target_ids:
            if tid == source_id: continue

            try:
                # 获取目标（优先缓存）
                t_info = self.get_sample_info(project_name, tid)
                if not t_info: continue

                new_records = copy.deepcopy(source_records)

                if overwrite:
                    t_info["weight_records"] = new_records
                else:
                    current_records = t_info.get("weight_records", [])
                    existing_dates = set()
                    for r in current_records:
                        if "date" in r: existing_dates.add(r["date"])

                    for rec in new_records:
                        if rec.get("date") not in existing_dates:
                            current_records.append(rec)

                    current_records.sort(key=lambda x: x["days"] if isinstance(x["days"], (int, float)) else -1)
                    t_info["weight_records"] = current_records

                # 写入磁盘
                json_path = os.path.join(config.DATA_ROOT, project_name, tid, "sample_info.json")
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(t_info, f, ensure_ascii=False, indent=4)

                # 更新缓存
                self._update_sample_cache(project_name, tid, t_info)
                success_count += 1
            except Exception as e:
                print(f"复制到 {tid} 失败: {e}")

        return success_count

    def save_stress_data(self, project_name, sample_id, data_points):
        try:
            path = os.path.join(config.DATA_ROOT, project_name, sample_id, "stress_data.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data_points, f, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存应力数据失败: {e}")
            return False

    def get_stress_data(self, project_name, sample_id):
        try:
            path = os.path.join(config.DATA_ROOT, project_name, sample_id, "stress_data.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []

    # =========================================================================
    # ✨✨✨ 新增：生成演示数据功能 ✨✨✨
    # =========================================================================
    def generate_demo_data(self):
        """
        在当前数据根目录下生成一个示例项目，包含几个典型的 MICP 实验试样。
        方便用户首次安装后快速理解软件功能。
        """
        demo_project_name = "示例项目_MICP固化实验"

        # 如果示例项目已存在，则不再生成，防止重复覆盖用户数据
        if os.path.exists(os.path.join(config.DATA_ROOT, demo_project_name)):
            return False

        print("🚀 正在生成示例数据...")

        # 1. 创建项目
        self.create_project(demo_project_name,
                            "本示例展示了不同钙源浓度对砂柱固化效果的影响 (0M, 0.5M, 1.0M)。请尝试勾选这三个试样进行[对比分析]。")

        # 2. 定义三组对比数据
        # 基础配置：圆柱体砂柱，直径50mm，高100mm，初始干重约300g
        base_info = {
            "initial_mass": 300.0,
            "shape": "圆柱体 (Cylinder)",
            "radius": 25, "height": 100,
            "date_prep": "2024-05-01-09:00",
            "date_complete": "2024-05-14-18:00",
            "date_demold": "2024-05-15-10:00",
            "date_test": "2024-05-16-14:00"
        }

        # --- 试样 A (Control): 0M 浓度 (无处理) ---
        self._create_demo_sample(
            demo_project_name, "A-Control-0M",
            base_info,
            conc=0.0,
            mass_gain_ratio=0.005,  # 几乎无增长
            peak_stress=50.0,  # 强度极低 (松散砂)
            icon="🧱"
        )

        # --- 试样 B (0.5M): 中等浓度 ---
        self._create_demo_sample(
            demo_project_name, "B-Treated-0.5M",
            base_info,
            conc=0.5,
            mass_gain_ratio=0.045,  # 增长 4.5%
            peak_stress=850.0,  # 强度中等
            icon="🧪"
        )

        # --- 试样 C (1.0M): 高浓度 ---
        self._create_demo_sample(
            demo_project_name, "C-Treated-1.0M",
            base_info,
            conc=1.0,
            mass_gain_ratio=0.082,  # 增长 8.2%
            peak_stress=1600.0,  # 强度高
            icon="💎"
        )

        return True

    def _create_demo_sample(self, p_name, s_id, base_info, conc, mass_gain_ratio, peak_stress, icon):
        """辅助函数：生成单个演示试样的所有数据"""
        info = base_info.copy()
        info["recipe"] = f"胶结液浓度: {conc} M, 菌液OD600=1.0, 灌注轮数=14"
        info["key_variable_name"] = "浓度(M)"
        info["key_variable"] = conc
        info["icon_emoji"] = icon

        # 1. 创建试样
        self.create_sample(p_name, s_id, info)

        # 2. 生成质量记录 (模拟14天的增长)
        init_m = info["initial_mass"]
        final_m = init_m * (1 + mass_gain_ratio)

        # 模拟 7 次称重 (每2天一次)
        for day in range(0, 15, 2):
            # 使用 S 型曲线模拟增长 (Sigmoid-like) 或简单的线性+随机波动
            # 这里简单用线性插值 + 一点点随机
            progress = day / 14.0
            current_mass = init_m + (final_m - init_m) * progress
            # 加一点随机噪点 (+/- 0.2g)
            current_mass += random.uniform(-0.1, 0.1)

            # 日期字符串模拟
            date_str = f"2024-05-{1 + day:02d}-10:00"
            self.add_weight_record(p_name, s_id, {"date": date_str, "mass": round(current_mass, 2), "days": day})

        # 3. 生成应力应变曲线 (模拟 UCS 曲线)
        # 使用简单的抛物线/软化模型模拟
        stress_data = []
        peak_strain = 1.5 + conc * 0.5  # 浓度越高，峰值应变稍微延后一点

        # 生成 0 ~ 4% 应变的数据点
        for i in range(41):
            strain = i * 0.1
            if strain <= 0:
                stress = 0
            else:
                # 简易模型: y = peak * (2*(x/x0) - (x/x0)^2)  (抛物线直到峰值)
                # 峰值后软化
                rel_x = strain / peak_strain
                if rel_x <= 1:
                    stress = peak_stress * (2 * rel_x - rel_x ** 2)
                else:
                    # 软化阶段
                    stress = peak_stress * (1 - 0.3 * (rel_x - 1))  # 缓慢下降

            # 加一点随机噪音
            stress += random.uniform(-5, 5)
            if stress < 0: stress = 0

            stress_data.append({"strain": round(strain, 2), "stress": round(stress, 2)})

        self.save_stress_data(p_name, s_id, stress_data)