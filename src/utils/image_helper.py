import os
from PIL import Image


class ImageHelper:
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
                # 转换为 RGB 模式 (防止 PNG 透明背景导致报错)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                # copy() 创建副本，thumbnail() 会直接修改副本
                img_copy = img.copy()
                img_copy.thumbnail(size)

                # 保存为 JPG 格式，质量 85
                img_copy.save(thumbnail_path, "JPEG", quality=85)
                return True
        except Exception as e:
            print(f"缩略图生成失败: {e}")
            return False