import os
from PIL import Image

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    print("Warning: 'pillow_heif' library not found. HEIC conversion will fail.")


class ImageHelper:
    @staticmethod
    def convert_to_jpg(source_path, target_path, quality=90):
        """
        将任意支持的图片格式转换为 JPG 并保存
        """
        try:
            # [优化] 增加 try-catch 块，防止因单个文件损坏导致整个程序崩溃
            with Image.open(source_path) as img:
                # 转换为 RGB 模式 (防止 PNG 透明背景或 HEIC 格式导致保存 JPG 报错)
                if img.mode in ('RGBA', 'P', 'LA'):
                    img = img.convert('RGB')

                # 保存为新文件
                img.save(target_path, "JPEG", quality=quality)
                return True
        except Exception as e:
            print(f"格式转换失败 ({source_path}): {e}")
            return False

    @staticmethod
    def generate_thumbnail(original_path, thumbnail_path, size=(200, 200)):
        """
        生成缩略图，保持高宽比
        """
        try:
            with Image.open(original_path) as img:
                if img.mode in ('RGBA', 'P', 'LA'):
                    img = img.convert('RGB')

                img_copy = img.copy()
                # thumbnail 方法本身就会保持高宽比
                img_copy.thumbnail(size, Image.Resampling.LANCZOS)
                img_copy.save(thumbnail_path, "JPEG", quality=85)
                return True
        except Exception as e:
            print(f"缩略图生成失败 ({original_path}): {e}")
            return False