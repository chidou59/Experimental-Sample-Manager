import os
import json
import shutil
import copy
import random
import pandas as pd
from datetime import datetime
import config
from src.utils.image_helper import ImageHelper
from src.utils.mechanical_analysis import MechanicalAnalyzer


class FileManager:
    def __init__(self):
        if not config.DATA_ROOT:
            raise ValueError("错误：未设置数据存储路径！")
        os.makedirs(config.DATA_ROOT, exist_ok=True)
        self.root_meta_path = os.path.join(config.DATA_ROOT, "root_meta.json")
        if not os.path.exists(self.root_meta_path):
            self._save_root_meta({"projects_order": []})

        # === 性能优化：内存缓存 ===
        self._sample_cache = {}
        self._structure_cache = None

    # === 原子写入 ===
    def _atomic_write_json(self, path, data):
        tmp_path = path + ".tmp"
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            os.replace(tmp_path, path)
            return True
        except Exception as e:
            print(f"写入失败 ({path}): {e}")
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass
            return False

    def _load_root_meta(self):
        try:
            with open(self.root_meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"projects_order": []}

    def _save_root_meta(self, data):
        self._atomic_write_json(self.root_meta_path, data)

    def _invalidate_structure_cache(self):
        self._structure_cache = None

    def _update_sample_cache(self, project_name, sample_id, data):
        if project_name not in self._sample_cache:
            self._sample_cache[project_name] = {}
        self._sample_cache[project_name][sample_id] = data

    def _remove_sample_from_cache(self, project_name, sample_id):
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
            self._atomic_write_json(os.path.join(project_path, "project_info.json"), project_info)

            meta = self._load_root_meta()
            if project_name not in meta["projects_order"]:
                meta["projects_order"].append(project_name)
                self._save_root_meta(meta)

            self._invalidate_structure_cache()
            return True
        except Exception as e:
            print(f"Error: {e}")
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

            self._atomic_write_json(os.path.join(sample_path, "sample_info.json"), sample_full_info)

            p_json_path = os.path.join(project_path, "project_info.json")
            if os.path.exists(p_json_path):
                try:
                    with open(p_json_path, 'r', encoding='utf-8') as f:
                        p_data = json.load(f)
                    if "samples_order" not in p_data: p_data["samples_order"] = []
                    if sample_id not in p_data["samples_order"]:
                        p_data["samples_order"].append(sample_id)
                        self._atomic_write_json(p_json_path, p_data)
                except:
                    pass

            self._update_sample_cache(project_name, sample_id, sample_full_info)
            self._invalidate_structure_cache()
            return True
        except Exception as e:
            print(f"Error creating sample: {e}")
            return False

    def update_sample_info(self, project_name, sample_id, new_data):
        try:
            data = self.get_sample_info(project_name, sample_id)
            if not data: return False

            # 回退到固定的字段列表，移除 attributes
            editable_fields = [
                "description", "date_prep", "date_complete", "date_demold", "date_test", "initial_mass",
                "shape", "radius", "height", "side_length", "length", "width", "icon_emoji",
                "recipe", "key_variable", "key_variable_name"
            ]

            for field in editable_fields:
                if field in new_data:
                    data[field] = new_data[field]

            json_path = os.path.join(config.DATA_ROOT, project_name, sample_id, "sample_info.json")
            if self._atomic_write_json(json_path, data):
                self._update_sample_cache(project_name, sample_id, data)
                return True
            return False
        except Exception as e:
            print(f"更新试样信息失败: {e}")
            return False

    def get_project_structure(self):
        if self._structure_cache is not None:
            return self._structure_cache

        structure = {}
        if not os.path.exists(config.DATA_ROOT): return structure

        meta = self._load_root_meta()
        saved_order = meta.get("projects_order", [])
        existing_projects = []

        try:
            with os.scandir(config.DATA_ROOT) as entries:
                for entry in entries:
                    if entry.is_dir() and os.path.exists(os.path.join(entry.path, "project_info.json")):
                        existing_projects.append(entry.name)
        except Exception as e:
            print(f"Scan dir error: {e}")

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
                with os.scandir(project_path) as sub_entries:
                    for sub in sub_entries:
                        if sub.is_dir() and os.path.exists(os.path.join(sub.path, "sample_info.json")):
                            existing_samples.append(sub.name)
            except:
                pass

            final_samples = []
            for s in saved_sample_order:
                if s in existing_samples: final_samples.append(s)
            for s in existing_samples:
                if s not in final_samples: final_samples.append(s)

            structure[project_name] = final_samples

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
                    self._atomic_write_json(p_info_path, data)
                except Exception as e:
                    print(f"保存试样顺序失败 {project_name}: {e}")

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
                self._atomic_write_json(json_path, data)

            meta = self._load_root_meta()
            if old_name in meta["projects_order"]:
                idx = meta["projects_order"].index(old_name)
                meta["projects_order"][idx] = new_name
                self._save_root_meta(meta)

            if old_name in self._sample_cache:
                del self._sample_cache[old_name]
            self._invalidate_structure_cache()
            return True
        except Exception as e:
            print(f"重命名项目失败: {e}")
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
                self._atomic_write_json(json_path, data)

            p_info_path = os.path.join(base_path, "project_info.json")
            if os.path.exists(p_info_path):
                with open(p_info_path, 'r', encoding='utf-8') as f:
                    p_data = json.load(f)
                if "samples_order" in p_data and old_id in p_data["samples_order"]:
                    idx = p_data["samples_order"].index(old_id)
                    p_data["samples_order"][idx] = new_id
                    self._atomic_write_json(p_info_path, p_data)

            self._remove_sample_from_cache(project_name, old_id)
            self._invalidate_structure_cache()
            return True
        except Exception as e:
            print(f"重命名试样失败: {e}")
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
            print(f"删除项目失败: {e}")
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
                    self._atomic_write_json(p_info_path, p_data)

            self._remove_sample_from_cache(project_name, sample_id)
            self._invalidate_structure_cache()
            return True
        except Exception as e:
            print(f"删除试样失败: {e}")
            return False

    def get_sample_info(self, project_name, sample_id):
        if project_name in self._sample_cache and sample_id in self._sample_cache[project_name]:
            return self._sample_cache[project_name][sample_id]

        try:
            json_path = os.path.join(config.DATA_ROOT, project_name, sample_id, "sample_info.json")
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._update_sample_cache(project_name, sample_id, data)
                return data
        except:
            return None

    def add_file_to_sample(self, project_name, sample_id, source_path):
        try:
            base_dir = os.path.join(config.DATA_ROOT, project_name, sample_id, "images")
            thumb_dir = os.path.join(base_dir, "thumbnails")
            os.makedirs(thumb_dir, exist_ok=True)

            filename = os.path.basename(source_path)
            name, ext = os.path.splitext(filename)
            ext_lower = ext.lower()

            target_path = ""
            if ext_lower == '.heic':
                new_filename = name + ".jpg"
                target_path = os.path.join(base_dir, new_filename)
                if not ImageHelper.convert_to_jpg(source_path, target_path):
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

            valid_exts = {
                '.png', '.jpg', '.jpeg', '.tif', '.bmp', '.heic',
                '.pdf', '.xls', '.xlsx', '.csv',
                '.txt', '.doc', '.docx'
            }
            image_exts = {'.png', '.jpg', '.jpeg', '.tif', '.bmp', '.heic'}

            with os.scandir(base_dir) as entries:
                for entry in entries:
                    if entry.is_file():
                        ext = os.path.splitext(entry.name)[1].lower()
                        if ext in valid_exts:
                            file_info = {
                                "name": entry.name,
                                "path": entry.path,
                                "type": "image" if ext in image_exts else "file",
                                "ext": ext
                            }
                            if file_info["type"] == "image":
                                thumb_path = os.path.join(thumb_dir, entry.name)
                                file_info["thumb"] = thumb_path if os.path.exists(thumb_path) else entry.path
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

            json_path = os.path.join(config.DATA_ROOT, project_name, sample_id, "sample_info.json")
            if self._atomic_write_json(json_path, data):
                self._update_sample_cache(project_name, sample_id, data)
                return True
            return False
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
                if self._atomic_write_json(json_path, data):
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
                if self._atomic_write_json(json_path, data):
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

                json_path = os.path.join(config.DATA_ROOT, project_name, tid, "sample_info.json")
                if self._atomic_write_json(json_path, t_info):
                    self._update_sample_cache(project_name, tid, t_info)
                    success_count += 1
            except Exception as e:
                print(f"复制到 {tid} 失败: {e}")

        return success_count

    def save_stress_data(self, project_name, sample_id, data_points):
        try:
            path = os.path.join(config.DATA_ROOT, project_name, sample_id, "stress_data.json")
            return self._atomic_write_json(path, data_points)
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
    # ✨✨✨ 批量导出项目汇总表 (恢复回退版) ✨✨✨
    # =========================================================================
    def export_project_summary(self, project_name, output_path):
        """
        导出项目汇总表到 Excel。包含：
        - 基础信息: ID, 关键变量, 配方
        - 质量数据: 初始质量, 最终质量, 变化率
        - 力学性能: 峰值应力, 峰值应变, 弹性模量, 韧性 (自动计算)
        """
        try:
            structure = self.get_project_structure()
            if project_name not in structure:
                return False, "项目不存在"

            sample_list = structure[project_name]
            if not sample_list:
                return False, "项目为空"

            data_rows = []

            for s_id in sample_list:
                info = self.get_sample_info(project_name, s_id)
                if not info: continue

                # 1. 基础信息 (恢复直接读取字段)
                row = {
                    "Sample ID": s_id,
                    "Key Variable Name": info.get("key_variable_name", ""),
                    "Key Variable Value": info.get("key_variable", ""),
                    "Recipe/Description": info.get("recipe", ""),  # 这里的 recipe 可能是文本
                    "Description(Note)": info.get("description", ""),  # 备注
                    "Shape": info.get("shape", ""),
                    "Date Prep": info.get("date_prep", ""),
                    "Date Test": info.get("date_test", "")
                }

                # 2. 质量数据
                init_mass = float(info.get("initial_mass", 0))
                row["Initial Mass (g)"] = init_mass

                records = info.get("weight_records", [])
                final_mass = init_mass
                if records:
                    # 取最后一次记录的质量
                    try:
                        final_mass = float(records[-1].get("mass", init_mass))
                    except:
                        pass

                row["Final Mass (g)"] = final_mass

                mass_change_pct = 0.0
                if init_mass > 0:
                    mass_change_pct = ((final_mass - init_mass) / init_mass) * 100
                row["Mass Change (%)"] = round(mass_change_pct, 2)

                # 3. 力学性能 (自动计算)
                # 读取应力应变数据
                stress_data = self.get_stress_data(project_name, s_id)

                # 默认值
                row["Peak Stress (kPa)"] = "-"
                row["Peak Strain (%)"] = "-"
                row["Elastic Modulus (MPa)"] = "-"
                row["Toughness (kJ/m³)"] = "-"

                if stress_data and len(stress_data) > 5:
                    # 调用分析器进行计算
                    analysis_res = MechanicalAnalyzer.analyze(stress_data)
                    if analysis_res["success"]:
                        row["Peak Stress (kPa)"] = round(analysis_res["peak_stress"], 2)
                        row["Peak Strain (%)"] = round(analysis_res["peak_strain"], 2)
                        row["Elastic Modulus (MPa)"] = round(analysis_res["elastic_modulus"], 2)
                        row["Toughness (kJ/m³)"] = round(analysis_res["toughness"], 2)

                data_rows.append(row)

            # 生成 DataFrame 并导出
            df = pd.DataFrame(data_rows)

            # 调整列顺序
            cols_order = [
                "Sample ID", "Key Variable Value", "Peak Stress (kPa)", "Mass Change (%)",
                "Elastic Modulus (MPa)", "Toughness (kJ/m³)",
                "Initial Mass (g)", "Final Mass (g)", "Peak Strain (%)",
                "Key Variable Name", "Recipe/Description", "Description(Note)", "Date Prep", "Date Test"
            ]
            # 仅保留存在的列
            cols_order = [c for c in cols_order if c in df.columns]
            df = df[cols_order]

            df.to_excel(output_path, index=False)
            return True, f"成功导出 {len(data_rows)} 个试样的数据"

        except Exception as e:
            return False, f"导出失败: {str(e)}"

    def generate_demo_data(self):
        demo_project_name = "示例项目_MICP固化实验"
        if os.path.exists(os.path.join(config.DATA_ROOT, demo_project_name)):
            return False

        print("🚀 正在生成示例数据...")
        self.create_project(demo_project_name,
                            "本示例展示了不同钙源浓度对砂柱固化效果的影响 (0M, 0.5M, 1.0M)。请尝试勾选这三个试样进行[对比分析]。")

        base_info = {
            "initial_mass": 300.0,
            "shape": "圆柱体 (Cylinder)",
            "radius": 25, "height": 100,
            "date_prep": "2024-05-01-09:00",
            "date_complete": "2024-05-14-18:00",
            "date_demold": "2024-05-15-10:00",
            "date_test": "2024-05-16-14:00"
        }

        self._create_demo_sample(demo_project_name, "A-Control-0M", base_info, conc=0.0, mass_gain_ratio=0.005,
                                 peak_stress=50.0, icon="🧱")
        self._create_demo_sample(demo_project_name, "B-Treated-0.5M", base_info, conc=0.5, mass_gain_ratio=0.045,
                                 peak_stress=850.0, icon="🧪")
        self._create_demo_sample(demo_project_name, "C-Treated-1.0M", base_info, conc=1.0, mass_gain_ratio=0.082,
                                 peak_stress=1600.0, icon="💎")
        return True

    def _create_demo_sample(self, p_name, s_id, base_info, conc, mass_gain_ratio, peak_stress, icon):
        info = base_info.copy()
        # 恢复旧的生成逻辑
        info["recipe"] = f"胶结液浓度: {conc} M, 菌液OD600=1.0, 灌注轮数=14"
        info["key_variable_name"] = "浓度(M)"
        info["key_variable"] = conc
        info["icon_emoji"] = icon

        self.create_sample(p_name, s_id, info)

        init_m = info["initial_mass"]
        final_m = init_m * (1 + mass_gain_ratio)

        for day in range(0, 15, 2):
            progress = day / 14.0
            current_mass = init_m + (final_m - init_m) * progress
            current_mass += random.uniform(-0.1, 0.1)
            date_str = f"2024-05-{1 + day:02d}-10:00"
            self.add_weight_record(p_name, s_id, {"date": date_str, "mass": round(current_mass, 2), "days": day})

        stress_data = []
        peak_strain = 1.5 + conc * 0.5

        for i in range(41):
            strain = i * 0.1
            if strain <= 0:
                stress = 0
            else:
                rel_x = strain / peak_strain
                if rel_x <= 1:
                    stress = peak_stress * (2 * rel_x - rel_x ** 2)
                else:
                    stress = peak_stress * (1 - 0.3 * (rel_x - 1))

            stress += random.uniform(-5, 5)
            if stress < 0: stress = 0
            stress_data.append({"strain": round(strain, 2), "stress": round(stress, 2)})

        self.save_stress_data(p_name, s_id, stress_data)