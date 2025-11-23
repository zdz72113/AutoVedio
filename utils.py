"""
工具函数模块
"""
import json
import os
from moviepy import AudioFileClip, concatenate_audioclips


def load_items_from_json(json_file_path):
    """
    从JSON文件加载项目列表
    
    参数:
        json_file_path: JSON文件路径
    
    返回:
        tuple: (items列表, template_name)
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 只支持包含template和items字段的对象格式
        if not isinstance(data, dict):
            raise ValueError("JSON格式错误：必须是包含template和items字段的对象")
        
        if 'items' not in data:
            raise ValueError("JSON格式错误：对象必须包含'items'字段")
        
        items = data['items']
        template_name = data.get('template', 'default')
        
        if not isinstance(items, list):
            raise ValueError("JSON格式错误：items应该是数组")
        
        # 验证每个item
        valid_items = []
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                print(f"[警告] 第 {i+1} 项不是对象，已跳过")
                continue
            
            # 必须要有TextTop或TextBottom
            if not item.get('TextTop') and not item.get('TextBottom'):
                print(f"[警告] 第 {i+1} 项缺少TextTop和TextBottom字段，已跳过")
                continue
            
            # 确保字段存在（可能为空）
            if 'TextTop' not in item:
                item['TextTop'] = None
            if 'TextBottom' not in item:
                item['TextBottom'] = None
            
            # 确保其他字段存在（初始化为None）
            if 'Prompt' not in item:
                item['Prompt'] = None
            if 'Image' not in item:
                item['Image'] = None
            if 'audio' not in item:
                item['audio'] = None
            if 'duration' not in item:
                item['duration'] = None
            
            valid_items.append(item)
        
        print(f"[工具] 从 {json_file_path} 加载了 {len(valid_items)} 个项目，使用模板: {template_name}")
        return valid_items, template_name
    except Exception as e:
        print(f"[工具] 加载JSON文件失败: {e}")
        raise


def save_items_to_json(items, json_file_path, template_name=None):
    """
    保存项目列表到JSON文件，保留template和items字段格式
    
    参数:
        items: 项目列表
        json_file_path: JSON文件路径
        template_name: 模板名称，如果为None则尝试从原文件读取
    """
    try:
        # 如果template_name为None，尝试从原文件读取
        if template_name is None:
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    original_data = json.load(f)
                if isinstance(original_data, dict) and 'template' in original_data:
                    template_name = original_data.get('template', 'default')
                else:
                    template_name = 'default'
            except:
                template_name = 'default'
        
        # 构建保存的数据结构，保留template和items字段
        data_to_save = {
            "template": template_name,
            "items": items
        }
        
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
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
        items: 项目列表，每个项目包含 TextTop, TextBottom, Text, Image, audio, duration 等字段
    
    返回:
        list: 幻灯片列表，每个元素包含 image, audio, text_top, text_bottom, duration
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
            "text_top": item.get('TextTop', ''),
            "text_bottom": item.get('TextBottom', ''),
            "title": item.get('Title', ''),
            "duration": duration
        })
        
        print(f"[工具] 第 {i+1} 张幻灯片：时长 {duration:.2f} 秒")
    
    return slides


def create_temp_dir(json_file_path, base_dir="temp"):
    """
    基于JSON文件名创建临时目录
    
    参数:
        json_file_path: JSON文件路径
        base_dir: 基础目录名
    
    返回:
        str: 创建的临时目录路径
    """
    # 获取JSON文件名（不含扩展名）作为临时文件夹名
    json_name = os.path.splitext(os.path.basename(json_file_path))[0]
    temp_dir = os.path.join(base_dir, json_name)
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "audio"), exist_ok=True)
    print(f"[工具] 创建临时目录: {temp_dir}")
    return temp_dir


def generate_output_filename(json_file_path, temp_dir=None):
    """
    基于JSON文件名和当前时间生成输出文件名，保存到temp目录下
    
    参数:
        json_file_path: JSON文件路径
        temp_dir: 临时目录路径，如果为None则基于JSON文件名创建
    
    返回:
        str: 输出文件名（完整路径）
    """
    from datetime import datetime
    base_name = os.path.splitext(os.path.basename(json_file_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 如果提供了temp_dir，使用它；否则基于JSON文件名创建
    if temp_dir is None:
        temp_dir = create_temp_dir(json_file_path)
    
    # 确保temp_dir存在
    os.makedirs(temp_dir, exist_ok=True)
    
    filename = f"{base_name}_{timestamp}.mp4"
    return os.path.join(temp_dir, filename)

