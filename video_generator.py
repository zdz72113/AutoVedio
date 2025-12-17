"""
视频生成模块
使用MoviePy合成视频
"""
from moviepy import ImageClip, TextClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips, ColorClip


class VideoGenerator:
    """视频生成器"""
    
    def __init__(self, font_path="./resource/AlibabaPuHuiTi-3-75-SemiBold.ttf", fps=10, video_size=(1080, 1920),
                 font_size=50, stroke_width=5, bg_opacity=0.7, bg_padding=20):
        """
        初始化视频生成器
        
        参数:
            font_path: 字体文件路径
            fps: 视频帧率
            video_size: 视频尺寸 (width, height)，默认1080x1920
            font_size: 字体大小
            stroke_width: 文字描边宽度
            bg_opacity: 背景不透明度（0-1）
            bg_padding: 背景内边距（像素）
        """
        self.font_path = font_path
        self.fps = fps
        self.video_size = video_size
        self.font_size = font_size
        self.stroke_width = stroke_width
        self.bg_opacity = bg_opacity
        self.bg_padding = bg_padding
    
    def _format_text_for_display(self, text):
        """
        格式化文本以便显示
        
        参数:
            text: 原始文本
        
        返回:
            str: 格式化后的文本
        """
        if not text:
            return ""
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
            
            # 创建文字剪辑
            title = slide.get("title", "")
            subtitle = slide.get("subtitle", "")
            
            clips_to_composite = [img_clip]
            
            # 文本区域宽度（留出左右边距）
            text_area_width = self.video_size[0] - 100  # 左右各留50像素边距
            
            # 如果存在title，显示在顶部
            if title:
                formatted_title = self._format_text_for_display(title)
                title_text_clip = TextClip(
                    text=formatted_title,
                    font=self.font_path,
                    font_size=int(self.font_size * 1.4),  # 标题字体稍大
                    color="#FF6600",  # 亮金色文字，更醒目
                    stroke_color="#FFFFFF",  # 白色描边，增强对比度
                    stroke_width=self.stroke_width,  # 加粗描边
                    method='caption',
                    size=(text_area_width, None)
                ).with_duration(slide["duration"])
                
                # 创建半透明深色背景，增强对比度
                # 增加额外高度以容纳描边和确保最后一行完整显示
                extra_height = self.stroke_width * 2 + 10  # 描边上下各占stroke_width，额外10像素缓冲
                title_bg = ColorClip(
                    size=(title_text_clip.w + self.bg_padding * 2, title_text_clip.h + self.bg_padding * 2 + extra_height),
                    color=(20, 20, 20),  # 深灰色背景，比纯黑更柔和
                    duration=slide["duration"]
                ).with_opacity(0.8)  # 稍微提高不透明度，使背景更明显
                
                # 将文字叠加在背景上
                title_composite = CompositeVideoClip([
                    title_bg.with_position(("center", "center")),
                    title_text_clip.with_position(("center", "center"))
                ], size=(title_bg.w, title_bg.h))
                
                # 标题位置：水平居中，距离顶部有一定边距
                title_composite = title_composite.with_position(("center", 30))
                clips_to_composite.append(title_composite)
            
            # 如果存在subtitle，显示在底部
            if subtitle:
                formatted_subtitle = self._format_text_for_display(subtitle)
                subtitle_text_clip = TextClip(
                    text=formatted_subtitle,
                    font=self.font_path,
                    font_size=self.font_size,
                    color="#FFFFFF",  # 白色文字
                    stroke_color="#000000",  # 黑色描边
                    stroke_width=self.stroke_width,  # 使用配置的描边宽度
                    method='caption',  # 使用caption方法支持自动换行
                    size=(text_area_width, None)  # 指定宽度，高度自动计算
                ).with_duration(slide["duration"])
                
                # 创建半透明背景
                # 增加额外高度以容纳描边和确保最后一行完整显示
                extra_height = self.stroke_width * 2 + 10  # 描边上下各占stroke_width，额外10像素缓冲
                subtitle_bg = ColorClip(
                    size=(subtitle_text_clip.w + self.bg_padding * 2, subtitle_text_clip.h + self.bg_padding * 2 + extra_height),
                    color=(0, 0, 0),  # 黑色背景
                    duration=slide["duration"]
                ).with_opacity(self.bg_opacity)  # 半透明背景
                
                # 将文字叠加在背景上
                subtitle_composite = CompositeVideoClip([
                    subtitle_bg.with_position(("center", "center")),
                    subtitle_text_clip.with_position(("center", "center"))
                ], size=(subtitle_bg.w, subtitle_bg.h))
                
                # 字幕位置：水平居中，距离底部有一定边距
                bottom_margin = 30
                # 计算底部位置（需要先获取clip的高度）
                bottom_y = self.video_size[1] - subtitle_composite.h - bottom_margin
                subtitle_composite = subtitle_composite.with_position(("center", bottom_y))
                clips_to_composite.append(subtitle_composite)
            
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

