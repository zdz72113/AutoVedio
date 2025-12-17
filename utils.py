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


def clean_items_for_first_json(items):
    """
    清理items，只保留title, subtitle, Prompt, Image字段
    
    参数:
        items: 项目列表
    
    返回:
        list: 清理后的项目列表
    """
    cleaned_items = []
    for item in items:
        cleaned_item = {
            'title': item.get('title', ''),
            'subtitle': item.get('subtitle', ''),
            'Prompt': item.get('Prompt', ''),
            'Image': item.get('Image', '')
        }
        cleaned_items.append(cleaned_item)
    return cleaned_items


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


def split_text_by_length(text, max_chars=50):
    """
    智能拆分文本，先按句号、问号、感叹号拆分，如果某段还是太长，按逗号拆分
    
    参数:
        text: 要拆分的文本
        max_chars: 最大字符数，默认50
    
    返回:
        list: 拆分后的文本段列表
    """
    if not text or len(text) <= max_chars:
        return [text]
    
    import re
    
    # 第一步：按句号、问号、感叹号拆分
    sentences = re.split(r'([。！？])', text)
    # 重新组合句子和标点
    parts = []
    for i in range(0, len(sentences), 2):
        if i + 1 < len(sentences):
            parts.append(sentences[i] + sentences[i + 1])
        elif sentences[i].strip():
            parts.append(sentences[i])
    
    # 过滤空字符串
    parts = [p.strip() for p in parts if p.strip()]
    
    # 第二步：检查每段长度，如果还是太长，按逗号拆分
    result = []
    for part in parts:
        if len(part) <= max_chars:
            result.append(part)
        else:
            # 按逗号、分号拆分
            sub_parts = re.split(r'([，；])', part)
            current = ""
            for i in range(0, len(sub_parts), 2):
                segment = sub_parts[i]
                if i + 1 < len(sub_parts):
                    segment += sub_parts[i + 1]
                
                if len(current + segment) <= max_chars:
                    current += segment
                else:
                    if current:
                        result.append(current.strip())
                    current = segment
                    # 如果单个segment就超过max_chars，强制拆分
                    while len(current) > max_chars:
                        result.append(current[:max_chars])
                        current = current[max_chars:]
            
            if current:
                result.append(current.strip())
    
    return [r for r in result if r]


def split_item_if_needed(item, max_chars=50):
    """
    如果需要，拆分item的subtitle
    
    参数:
        item: 原始item
        max_chars: 最大字符数，默认50
    
    返回:
        list: 拆分后的item列表（如果不需要拆分，返回包含原item的列表）
    """
    subtitle = item.get('subtitle', '')
    if not subtitle or len(subtitle) <= max_chars:
        return [item]
    
    # 拆分subtitle
    split_subtitles = split_text_by_length(subtitle, max_chars)
    
    # 如果只拆分成一段，返回原item
    if len(split_subtitles) <= 1:
        return [item]
    
    # 创建多个item，共享原item的其他字段
    split_items = []
    # 尝试从audio文件名中提取基础索引
    audio_path = item.get('audio', '')
    base_index = None
    if audio_path:
        import re
        audio_filename = audio_path.replace('\\', '/').split('/')[-1]
        match = re.search(r'audio_(\d+)', audio_filename)
        if match:
            base_index = match.group(1)
    
    for i, sub_subtitle in enumerate(split_subtitles):
        new_item = item.copy()
        new_item['subtitle'] = sub_subtitle
        # 清除原有的audio和duration，需要重新生成
        new_item.pop('audio', None)
        new_item.pop('duration', None)
        # 标记这是拆分后的item（用于后续生成audio时的命名）
        if base_index is not None:
            new_item['_split_index'] = f"{base_index}_{i+1}"
        else:
            # 如果没有基础索引，使用临时标记，后续会按顺序生成
            new_item['_split_index'] = None
        split_items.append(new_item)
    
    return split_items

