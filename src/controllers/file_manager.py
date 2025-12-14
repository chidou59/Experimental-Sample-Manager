import os
import json
import shutil
import copy
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

    # === 原有 Project/Sample 基础 CRUD 方法保持不变 (create_project, create_sample...) ===
    # 为节省篇幅，这里假设原有 create_project, create_sample, update_sample_info 等依然存在
    # 请务必保留原文件中的这些代码，仅添加下方的新方法。

    def create_project(self, project_name, description=""):
        # ... (保留原代码) ...
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
            return True
        except Exception as e:
            print(f"Error: {e}");
            return False

    def create_sample(self, project_name, sample_id, sample_data):
        # ... (保留原代码) ...
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
            with open(os.path.join(sample_path, "sample_info.json"), 'w', encoding='utf-8') as f:
                json.dump(sample_full_info, f, ensure_ascii=False, indent=4)

            p_json_path = os.path.join(project_path, "project_info.json")
            if os.path.exists(p_json_path):
                with open(p_json_path, 'r', encoding='utf-8') as f:
                    p_data = json.load(f)
                if "samples_order" not in p_data: p_data["samples_order"] = []
                if sample_id not in p_data["samples_order"]: p_data["samples_order"].append(sample_id)
                with open(p_json_path, 'w', encoding='utf-8') as f:
                    json.dump(p_data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Error creating sample: {e}");
            return False

    def update_sample_info(self, project_name, sample_id, new_data):
        # ... (保留原代码) ...
        try:
            json_path = os.path.join(config.DATA_ROOT, project_name, sample_id, "sample_info.json")
            if not os.path.exists(json_path): return False

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            editable_fields = [
                "description", "date_prep", "date_complete", "date_demold", "date_test", "initial_mass",
                "shape", "radius", "height", "side_length", "length", "width", "icon_emoji"
            ]

            for field in editable_fields:
                if field in new_data:
                    data[field] = new_data[field]

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"更新试样信息失败: {e}")
            return False

    def get_project_structure(self):
        # ... (保留原代码) ...
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
        return structure

    def update_structure_order(self, new_structure_dict):
        # ... (保留原代码) ...
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

    def rename_project(self, old_name, new_name):
        # ... (保留原代码) ...
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
            return True
        except Exception as e:
            print(f"重命名项目失败: {e}");
            return False

    def rename_sample(self, project_name, old_id, new_id):
        # ... (保留原代码) ...
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
            return True
        except Exception as e:
            print(f"重命名试样失败: {e}");
            return False

    def delete_project(self, project_name):
        # ... (保留原代码) ...
        path = os.path.join(config.DATA_ROOT, project_name)
        try:
            shutil.rmtree(path)
            meta = self._load_root_meta()
            if project_name in meta["projects_order"]:
                meta["projects_order"].remove(project_name)
                self._save_root_meta(meta)
            return True
        except Exception as e:
            print(f"删除项目失败: {e}");
            return False

    def delete_sample(self, project_name, sample_id):
        # ... (保留原代码) ...
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
            return True
        except Exception as e:
            print(f"删除试样失败: {e}");
            return False

    def get_sample_info(self, project_name, sample_id):
        # ... (保留原代码) ...
        try:
            json_path = os.path.join(config.DATA_ROOT, project_name, sample_id, "sample_info.json")
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None

    def add_file_to_sample(self, project_name, sample_id, source_path):
        # ... (保留原代码) ...
        try:
            base_dir = os.path.join(config.DATA_ROOT, project_name, sample_id, "images")
            thumb_dir = os.path.join(base_dir, "thumbnails")
            os.makedirs(thumb_dir, exist_ok=True)
            filename = os.path.basename(source_path)
            target_path = os.path.join(base_dir, filename)
            shutil.copy(source_path, target_path)
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.tif', '.bmp']:
                thumb_path = os.path.join(thumb_dir, filename)
                ImageHelper.generate_thumbnail(target_path, thumb_path)
            return target_path
        except:
            return None

    def get_sample_files(self, project_name, sample_id):
        # ... (保留原代码) ...
        try:
            base_dir = os.path.join(config.DATA_ROOT, project_name, sample_id, "images")
            thumb_dir = os.path.join(base_dir, "thumbnails")
            if not os.path.exists(base_dir): return []
            files_list = []
            valid_exts = ['.png', '.jpg', '.jpeg', '.tif', '.bmp', '.pdf', '.xls', '.xlsx', '.csv', '.txt']
            for f in os.listdir(base_dir):
                if os.path.isdir(os.path.join(base_dir, f)): continue
                ext = os.path.splitext(f)[1].lower()
                if ext in valid_exts:
                    file_info = {
                        "name": f,
                        "path": os.path.join(base_dir, f),
                        "type": "image" if ext in ['.png', '.jpg', '.jpeg', '.tif', '.bmp'] else "file",
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
        # ... (保留原代码) ...
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
        # ... (保留原代码) ...
        try:
            json_path = os.path.join(config.DATA_ROOT, project_name, sample_id, "sample_info.json")
            if not os.path.exists(json_path): return False
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "weight_records" not in data: data["weight_records"] = []
            data["weight_records"].append(record)
            data["weight_records"].sort(key=lambda x: x["days"] if isinstance(x["days"], (int, float)) else -1)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except:
            return False

    def update_weight_record(self, project_name, sample_id, index, new_record):
        # ... (保留原代码) ...
        try:
            json_path = os.path.join(config.DATA_ROOT, project_name, sample_id, "sample_info.json")
            if not os.path.exists(json_path): return False
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            records = data.get("weight_records", [])
            if 0 <= index < len(records):
                records[index] = new_record
                records.sort(key=lambda x: x["days"] if isinstance(x["days"], (int, float)) else -1)
                data["weight_records"] = records
                with open(json_path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)
                return True
            return False
        except:
            return False

    def delete_weight_record(self, project_name, sample_id, index):
        # ... (保留原代码) ...
        try:
            json_path = os.path.join(config.DATA_ROOT, project_name, sample_id, "sample_info.json")
            if not os.path.exists(json_path): return False
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            records = data.get("weight_records", [])
            if 0 <= index < len(records):
                del records[index]
                data["weight_records"] = records
                with open(json_path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=4)
                return True
            return False
        except:
            return False

    def batch_copy_weights(self, project_name, source_id, target_ids, overwrite=False):
        # ... (保留原代码) ...
        source_info = self.get_sample_info(project_name, source_id)
        if not source_info: return False

        source_records = source_info.get("weight_records", [])
        if not source_records: return True  # 源没有记录，没必要复制，但也不算失败

        success_count = 0
        for tid in target_ids:
            if tid == source_id: continue  # 跳过自己

            try:
                json_path = os.path.join(config.DATA_ROOT, project_name, tid, "sample_info.json")
                if not os.path.exists(json_path): continue

                with open(json_path, 'r', encoding='utf-8') as f:
                    t_info = json.load(f)

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

                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(t_info, f, ensure_ascii=False, indent=4)

                success_count += 1
            except Exception as e:
                print(f"复制到 {tid} 失败: {e}")

        return success_count

    # === 【新增】应力应变数据管理方法 ===
    def save_stress_data(self, project_name, sample_id, data_points):
        """
        保存应力应变数据到单独的 JSON 文件 (避免主文件过大)
        :param data_points: list of dict [{"strain": x, "stress": y}, ...]
        """
        try:
            # 存放在 sample 文件夹下的 stress_data.json
            path = os.path.join(config.DATA_ROOT, project_name, sample_id, "stress_data.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data_points, f, ensure_ascii=False)  # 不缩进，减小体积
            return True
        except Exception as e:
            print(f"保存应力数据失败: {e}")
            return False

    def get_stress_data(self, project_name, sample_id):
        """读取应力应变数据"""
        try:
            path = os.path.join(config.DATA_ROOT, project_name, sample_id, "stress_data.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except:
            return []