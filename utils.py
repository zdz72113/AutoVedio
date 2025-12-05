"""
工具函数模块
"""
import json
import os
from moviepy import AudioFileClip, concatenate_audioclips


def load_input_config(json_file_path):
    """
    从JSON文件加载输入配置
    
    参数:
        json_file_path: JSON文件路径
    
    返回:
        dict: 配置字典，包含 video_size, images, voice, font, font_color, font_size, name, text, style
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            raise ValueError("JSON格式错误：必须是对象格式")
        
        # 验证必需字段
        required_fields = ['video_size', 'iamges', 'voice', 'font', 'font_color', 'font_size', 'name', 'text']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"JSON格式错误：缺少必需字段: {', '.join(missing_fields)}")
        
        # 处理images字段（兼容拼写错误iamges）
        images_count = data.get('iamges') or data.get('images', 0)
        
        config = {
            'video_size': data['video_size'],
            'images': images_count,
            'voice': data['voice'],
            'font': data['font'],
            'font_color': data['font_color'],
            'font_size': data['font_size'],
            'name': data['name'],
            'text': data['text'],
            'style': data.get('style', '插画') 
        }
        
        print(f"[工具] 从 {json_file_path} 加载配置: name={config['name']}, images={config['images']}, style={config['style']}")
        return config
    except Exception as e:
        print(f"[工具] 加载输入配置失败: {e}")
        raise


def load_items_from_json(json_file_path):
    """
    从JSON文件加载项目列表（数组格式）
    
    参数:
        json_file_path: JSON文件路径
    
    返回:
        list: items列表
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("JSON格式错误：必须是数组格式")
        
        print(f"[工具] 从 {json_file_path} 加载了 {len(data)} 个项目")
        return data
    except Exception as e:
        print(f"[工具] 加载JSON文件失败: {e}")
        raise


def save_items_to_json(items, json_file_path):
    """
    保存项目列表到JSON文件
    
    参数:
        items: 项目列表
        json_file_path: JSON文件路径
    """
    try:
        # 直接保存为数组格式
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print(f"[工具] 已保存更新后的JSON到: {json_file_path}")
    except Exception as e:
        print(f"[工具] 保存JSON文件失败: {e}")
        raise


def calculate_audio_duration(audio_file):
    """
    计算音频文件的时长
    
    参数:
        audio_file: 音频文件路径
    
    返回:
        float: 时长（秒）
    """
    try:
        audio_clip = AudioFileClip(audio_file)
        duration = audio_clip.duration
        audio_clip.close()
        return duration
    except Exception as e:
        print(f"[工具] 计算音频时长失败 {audio_file}: {e}")
        return 0.0


def merge_audio_files(audio_files, output_file):
    """
    合并多个音频文件
    
    参数:
        audio_files: 音频文件路径列表
        output_file: 输出音频文件路径
    
    返回:
        str: 输出音频文件路径
    """
    try:
        clips = []
        for audio_file in audio_files:
            clips.append(AudioFileClip(audio_file))
        
        final_clip = concatenate_audioclips(clips)
        final_clip.write_audiofile(output_file)
        
        # Close clips
        final_clip.close()
        for clip in clips:
            clip.close()
            
        print(f"[工具] 已合并音频到: {output_file}")
        return output_file
    except Exception as e:
        print(f"[工具] 合并音频失败: {e}")
        raise


def generate_slide_list_from_items(items):
    """
    从items生成幻灯片列表，包括图片、语音、字幕和时长
    
    参数:
        items: 项目列表，每个项目包含 title, subtitle, Image, audio, duration 等字段
    
    返回:
        list: 幻灯片列表，每个元素包含 image, audio, title, subtitle, duration
    """
    slides = []
    for i, item in enumerate(items):
        # 检查必需字段
        if not item.get('Image') or not item.get('audio'):
            print(f"[警告] 第 {i+1} 项缺少Image或audio字段，已跳过")
            continue
        
        # 计算或使用已有的duration
        duration = item.get('duration')
        if duration is None or duration == 0:
            duration = calculate_audio_duration(item['audio'])
            if duration == 0:
                duration = 3.0  # 默认时长
            item['duration'] = duration
        
        slides.append({
            "image": item['Image'],
            "audio": item['audio'],
            "title": item.get('title', ''),
            "subtitle": item.get('subtitle', ''),
            "duration": duration
        })
        
        print(f"[工具] 第 {i+1} 张幻灯片：时长 {duration:.2f} 秒")
    
    return slides


def create_temp_dir(name, base_dir="temp"):
    """
    基于name创建临时目录
    
    参数:
        name: 项目名称
        base_dir: 基础目录名
    
    返回:
        str: 创建的临时目录路径
    """
    temp_dir = os.path.join(base_dir, name)
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "audio"), exist_ok=True)
    print(f"[工具] 创建临时目录: {temp_dir}")
    return temp_dir


def generate_output_filename(name, temp_dir):
    """
    基于name和当前时间生成输出文件名，保存到temp目录下
    
    参数:
        name: 项目名称
        temp_dir: 临时目录路径
    
    返回:
        str: 输出文件名（完整路径）
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 确保temp_dir存在
    os.makedirs(temp_dir, exist_ok=True)
    
    filename = f"{name}_{timestamp}.mp4"
    return os.path.join(temp_dir, filename)

