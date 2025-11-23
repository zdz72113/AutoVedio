"""
视频生成模块
使用MoviePy合成视频
"""
from moviepy import ImageClip, TextClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips
import re


class VideoGenerator:
    """视频生成器"""
    
    def __init__(self, font_path="./resource/AlibabaPuHuiTi-3-75-SemiBold.ttf", fps=18, video_size=(1080, 1920),
                 text_color="#2C3E50", text_bottom_color="#34495E", title_color="#E74C3C", stroke_color="#FFFFFF", stroke_width=2):
        """
        初始化视频生成器
        
        参数:
            font_path: 字体文件路径
            fps: 视频帧率
            video_size: 视频尺寸 (width, height)，默认1080x1920
            text_color: 顶部文字颜色
            text_bottom_color: 底部文字颜色
            title_color: 标题文字颜色
            stroke_color: 文字描边颜色
            stroke_width: 文字描边宽度
        """
        self.font_path = font_path
        self.fps = fps
        self.video_size = video_size
        self.text_color = text_color
        self.text_bottom_color = text_bottom_color
        self.title_color = title_color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
    
    def _format_text_for_display(self, text, max_chars_per_line=15):
        """
        格式化文本以便显示，支持自动换行
        
        参数:
            text: 原始文本
            max_chars_per_line: 每行最大字符数（用于自动换行）
        
        返回:
            str: 格式化后的文本（包含换行符）
        """
        if not text:
            return ""
        
        # 如果文本中已经包含换行符，直接使用
        if '\n' in text:
            return text
        
        # 如果文本长度超过限制，按字符数强制换行
        # if len(text) > max_chars_per_line:
        #     lines = []
        #     current_line = ""
        #     for char in text:
        #         current_line += char
        #         if len(current_line) >= max_chars_per_line:
        #             lines.append(current_line)
        #             current_line = ""
        #     if current_line:
        #         lines.append(current_line)
        #     text = '\n'.join(lines)
        
        return text
    
    def create_video(self, slides, output_file):
        """
        创建视频
        
        参数:
            slides: 幻灯片列表，每个元素包含 image, audio, text, duration
            output_file: 输出视频文件路径
        
        返回:
            str: 输出视频文件路径
        """
        clips_with_text = []
        
        for index, slide in enumerate(slides):
            print(f"\n处理第 {index + 1}/{len(slides)} 张幻灯片...")
            
            # 创建图片剪辑
            img_clip = ImageClip(slide["image"])
            img_clip = img_clip.with_duration(slide["duration"])
            
            # 调整图片尺寸以适应视频尺寸（保持宽高比）
            # 计算缩放比例，使图片能够完全适应视频尺寸
            scale_w = self.video_size[0] / img_clip.w
            scale_h = self.video_size[1] / img_clip.h
            scale = max(scale_w, scale_h)  # 使用较大的缩放比例，确保图片完全覆盖
            
            # 缩放图片
            new_width = int(img_clip.w * scale)
            new_height = int(img_clip.h * scale)
            img_clip = img_clip.resized((new_width, new_height))
            
            # 如果图片尺寸大于视频尺寸，居中裁剪
            if new_width > self.video_size[0] or new_height > self.video_size[1]:
                img_clip = img_clip.cropped(
                    x_center=new_width/2,
                    y_center=new_height/2,
                    width=self.video_size[0],
                    height=self.video_size[1]
                )
            
            # 确保图片尺寸完全匹配视频尺寸
            if img_clip.w != self.video_size[0] or img_clip.h != self.video_size[1]:
                img_clip = img_clip.resized(self.video_size)
            
            # 创建顶部文字剪辑
            text_top = slide.get("text_top", "")
            text_bottom = slide.get("text_bottom", "")
            title = slide.get("title", "")
            
            clips_to_composite = [img_clip]
            
            # 文本区域宽度（留出左右边距）
            text_area_width = self.video_size[0] - 100  # 左右各留50像素边距
            
            # 如果存在Title，显示在中间
            if title:
                title_clip = TextClip(
                    text=title,
                    font=self.font_path,
                    font_size=80,
                    color=self.title_color,
                    stroke_color=self.stroke_color,
                    stroke_width=self.stroke_width,
                    method='caption',
                    size=(text_area_width, None)
                ).with_duration(slide["duration"])
                # 标题位置：水平居中，垂直居中
                title_y = (self.video_size[1] - title_clip.h) / 2
                title_clip = title_clip.with_position(("center", title_y))
                clips_to_composite.append(title_clip)
            
            if text_top:
                # 格式化文本，支持换行
                formatted_text_top = self._format_text_for_display(text_top, max_chars_per_line=20)
                text_top_clip = TextClip(
                    text=formatted_text_top,
                    font=self.font_path,
                    font_size=60,
                    color=self.text_color,
                    stroke_color=self.stroke_color,
                    stroke_width=self.stroke_width,
                    method='caption',  # 使用caption方法支持自动换行
                    size=(text_area_width, None)  # 指定宽度，高度自动计算
                ).with_duration(slide["duration"])
                # 顶部文字位置：水平居中，距离顶部有一定边距
                text_top_clip = text_top_clip.with_position(("center", 30))
                clips_to_composite.append(text_top_clip)
            
            if text_bottom:
                # 格式化文本，支持换行
                formatted_text_bottom = self._format_text_for_display(text_bottom, max_chars_per_line=20)
                text_bottom_clip = TextClip(
                    text=formatted_text_bottom,
                    font=self.font_path,
                    font_size=60,
                    color=self.text_bottom_color,
                    stroke_color=self.stroke_color,
                    stroke_width=self.stroke_width,
                    method='caption',  # 使用caption方法支持自动换行
                    size=(text_area_width, None)  # 指定宽度，高度自动计算
                ).with_duration(slide["duration"])
                # 底部文字位置：水平居中，距离底部有一定边距
                bottom_margin = 30
                # 计算底部位置（需要先获取clip的高度）
                bottom_y = self.video_size[1] - text_bottom_clip.h - bottom_margin
                text_bottom_clip = text_bottom_clip.with_position(("center", bottom_y))
                clips_to_composite.append(text_bottom_clip)
            
            # 加载音频剪辑
            audio_clip = AudioFileClip(slide["audio"])
            
            # 合成视频：图片 + 顶部文字 + 底部文字 + 语音
            # 明确指定尺寸以确保所有clip尺寸一致
            video_clip = CompositeVideoClip(clips_to_composite, size=self.video_size)
            video_clip = video_clip.with_audio(audio_clip)
            
            clips_with_text.append(video_clip)
        
        # 拼接所有剪辑
        print("\n正在合成最终视频...")
        final_clip = concatenate_videoclips(clips_with_text, method="compose")
        
        # 输出视频
        print(f"正在保存视频到: {output_file}")
        final_clip.write_videofile(output_file, fps=self.fps)
        
        # 清理资源
        final_clip.close()
        for clip in clips_with_text:
            clip.close()
        
        print(f"\n[视频生成] 视频已保存到: {output_file}")
        return output_file

