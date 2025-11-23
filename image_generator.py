"""
图片生成模块
使用火山引擎API生成图片
"""
import os
from volcenginesdkarkruntime import Ark
from config import Config


class ImageGenerator:
    """图片生成器"""
    
    def __init__(self):
        self.client = Ark(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=Config.ARK_API_KEY
        )
        self.model = "doubao-seedream-4-0-250828"
    
    def generate_image(self, prompt, output_path, size="1080x1920"):
        """
        生成单张图片
        
        参数:
            prompt: 图片生成提示词
            output_path: 输出图片路径
            size: 图片尺寸，格式为 "宽x高"，例如 "1080x1920" 或 "1080x1440"
        
        返回:
            str: 保存的图片路径，失败返回None
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            
            images_response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=size,
                response_format="url",
                watermark=False
            )
            
            # 下载图片
            import urllib.request
            image_url = images_response.data[0].url
            urllib.request.urlretrieve(image_url, output_path)
            
            print(f"[图片生成] 图片已保存到: {output_path}")
            return output_path
        except Exception as e:
            print(f"[图片生成] 生成图片失败: {e}")
            return None
    
    def generate_images_batch(self, items, output_dir, template=None):
        """
        批量生成图片，并更新到items中
        
        参数:
            items: 项目列表，每个项目包含 Prompt, Image 等字段
            output_dir: 输出目录
            template: 模板配置字典，包含 video_size
        
        返回:
            无，直接更新items中的Image字段
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 从模板获取图片尺寸
        image_size = "1080x1920"  # 默认尺寸
        if template and 'video_size' in template:
            video_size = template['video_size']
            if isinstance(video_size, (list, tuple)) and len(video_size) >= 2:
                image_size = f"{video_size[0]}x{video_size[1]}"
            elif isinstance(video_size, str):
                image_size = video_size
        
        for i, item in enumerate(items):
            # 如果已有Image，跳过
            if item.get('Image'):
                print(f"[图片生成] 第 {i+1}/{len(items)} 项已有图片，跳过")
                continue
            
            # 检查是否有Prompt
            prompt = item.get('Prompt')
            if not prompt:
                print(f"[警告] 第 {i+1} 项缺少Prompt字段，跳过图片生成")
                continue
            
            output_path = os.path.join(output_dir, f"image_{i+1}.jpg")
            result = self.generate_image(prompt, output_path, size=image_size)
            if result:
                item['Image'] = result

