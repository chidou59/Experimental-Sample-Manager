import os
from PIL import Image

# 尝试导入并注册 HEIC 支持库
# 这样 Image.open 就能自动识别 .heic 文件了
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
        :param source_path: 源图片路径 (可以是 .heic)
        :param target_path: 目标保存路径 (建议以 .jpg 结尾)
        :param quality: JPG 质量 (1-100)
        """
        try:
            with Image.open(source_path) as img:
                # 转换为 RGB 模式 (防止 PNG 透明背景或 HEIC 格式导致保存 JPG 报错)
                if img.mode in ('RGBA', 'P'):
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
        生成缩略图
        :param original_path: 原图路径
        :param thumbnail_path: 缩略图保存路径
        :param size: 最大尺寸 (宽, 高)
        """
        try:
            with Image.open(original_path) as img:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                img_copy = img.copy()
                img_copy.thumbnail(size)
                img_copy.save(thumbnail_path, "JPEG", quality=85)
                return True
        except Exception as e:
            print(f"缩略图生成失败 ({original_path}): {e}")
            return False