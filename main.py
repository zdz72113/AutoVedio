"""
主程序入口
自动化生成视频流程：文本 -> 提示词 -> 图片 -> 语音 -> 视频
支持增量处理：如果字段已有值，跳过该步骤
"""
import sys
import os
from config import Config
from prompt_generator import PromptGenerator
from image_generator import ImageGenerator
from voice_generator import generate_audio_for_items
from utils import (
    load_items_from_json,
    save_items_to_json,
    create_temp_dir,
    generate_slide_list_from_items,
    generate_output_filename,
    calculate_audio_duration
)
from video_generator import VideoGenerator
from templates import get_template


def main(json_file_path):
    """
    主流程函数
    
    参数:
        json_file_path: JSON输入文件路径
    """
    print("=" * 60)
    print("开始自动化视频生成流程")
    print("=" * 60)
    
    # 1. 验证配置
    try:
        Config.validate()
        print("[配置] 配置验证通过")
    except ValueError as e:
        print(f"[错误] {e}")
        return
    
    # 2. 加载项目列表和模板
    try:
        items, template_name = load_items_from_json(json_file_path)
        if not items:
            print("[错误] JSON文件中没有有效的项目")
            return
        
        # 获取模板配置
        template = get_template(template_name)
        print(f"[配置] 使用模板: {template['name']} ({template_name})")
    except Exception as e:
        print(f"[错误] 加载JSON文件失败: {e}")
        return
    
    # 3. 创建临时目录（基于JSON文件名）
    temp_dir = create_temp_dir(json_file_path)
    image_dir = os.path.join(temp_dir, "images")
    audio_dir = os.path.join(temp_dir, "audio")
    
    # 4. 生成提示词
    print("\n" + "=" * 60)
    print("步骤 1/6: 生成提示词")
    print("=" * 60)
    prompt_gen = PromptGenerator()
    
    # 为每段文本生成图片提示词（跳过已有Prompt的项目），传入模板配置
    prompt_gen.generate_image_prompts(items, template)
    
    # 保存更新后的JSON（保留template和items字段）
    save_items_to_json(items, json_file_path, template_name=template_name)
    
    # 5. 生成图片（跳过已有Image的项目）
    print("\n" + "=" * 60)
    print("步骤 2/6: 生成图片")
    print("=" * 60)
    image_gen = ImageGenerator()
    image_gen.generate_images_batch(items, image_dir, template=template)
    
    # 保存更新后的JSON（保留template和items字段）
    save_items_to_json(items, json_file_path, template_name=template_name)
    
    # 6. 生成语音（跳过已有audio的项目）
    print("\n" + "=" * 60)
    print("步骤 3/6: 生成语音")
    print("=" * 60)
    generate_audio_for_items(items, template, audio_dir)
    
    # 保存更新后的JSON（保留template和items字段）
    save_items_to_json(items, json_file_path, template_name=template_name)
    
    # 7. 计算时长并更新到items中
    print("\n" + "=" * 60)
    print("步骤 4/6: 计算时长")
    print("=" * 60)
    for i, item in enumerate(items):
        if item.get('audio') and (not item.get('duration') or item.get('duration') == 0):
            duration = calculate_audio_duration(item['audio'])
            if duration > 0:
                item['duration'] = duration
                print(f"[时长计算] 第 {i+1} 项：{duration:.2f} 秒")
            else:
                item['duration'] = 3.0  # 默认时长
                print(f"[时长计算] 第 {i+1} 项：使用默认时长 3.0 秒")
    
    # 保存更新后的JSON（保留template和items字段）
    save_items_to_json(items, json_file_path, template_name=template_name)
    
    # 8. 生成幻灯片列表
    print("\n" + "=" * 60)
    print("步骤 5/6: 生成幻灯片列表")
    print("=" * 60)
    try:
        slides = generate_slide_list_from_items(items)
        if not slides:
            print("[错误] 没有有效的幻灯片")
            return
    except Exception as e:
        print(f"[错误] 生成幻灯片列表失败: {e}")
        return
    
    # 9. 生成视频
    print("\n" + "=" * 60)
    print("步骤 6/6: 合成视频")
    print("=" * 60)
    # 从模板获取视频尺寸、字体和文字颜色配置
    video_size = template.get('video_size', (1080, 1920))  # 默认9:16
    if isinstance(video_size, list):
        video_size = tuple(video_size)
    video_gen = VideoGenerator(
        font_path=template['font'],
        video_size=video_size,
        text_color=template['text_color'],
        text_bottom_color=template['text_bottom_color'],
        title_color=template.get('title_color', '#E74C3C'),
        stroke_color=template['stroke_color'],
        stroke_width=template['stroke_width']
    )
    output_file = generate_output_filename(json_file_path, temp_dir=temp_dir)
    
    try:
        video_gen.create_video(slides, output_file)
    except Exception as e:
        print(f"[错误] 生成视频失败: {e}")
        return
    
    # 10. 完成
    print("\n" + "=" * 60)
    print("完成")
    print("=" * 60)
    print(f"\n✅ 视频生成完成！")
    print(f"📁 输出文件: {output_file}")
    print(f"📁 临时文件: {temp_dir}")
    print(f"📁 JSON文件已更新: {json_file_path}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python main.py <json_file_path>")
        print("示例: python main.py input.json")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    
    if not os.path.exists(json_file_path):
        print(f"[错误] 文件不存在: {json_file_path}")
        sys.exit(1)
    
    main(json_file_path)
