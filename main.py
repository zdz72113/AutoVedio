"""
主程序入口
自动化生成视频流程：输入配置 -> 生成脚本 -> 生成提示词 -> 生成图片 -> 生成语音 -> 生成视频
"""
import sys
import os
from config import Config
from prompt_generator import PromptGenerator
from image_generator import ImageGenerator
from voice_generator import generate_audio_for_items
from utils import (
    load_input_config,
    load_items_from_json,
    save_items_to_json,
    create_temp_dir,
    generate_slide_list_from_items,
    generate_output_filename,
    calculate_audio_duration,
    split_item_if_needed,
    clean_items_for_first_json
)
from video_generator import VideoGenerator


def main(json_file_path):
    """
    主流程函数
    
    参数:
        json_file_path: JSON输入文件路径（包含video_size, images, voice, font等配置）
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
    
    # 2. 加载输入配置
    try:
        config = load_input_config(json_file_path)
        print(f"[配置] 项目名称: {config['name']}")
        print(f"[配置] 图片数量: {config['images']}")
        print(f"[配置] 视频尺寸: {config['video_size']}")
    except Exception as e:
        print(f"[错误] 加载输入配置失败: {e}")
        return
    
    # 3. 创建临时目录（基于name字段）
    temp_dir = create_temp_dir(config['name'])
    image_dir = os.path.join(temp_dir, "images")
    audio_dir = os.path.join(temp_dir, "audio")
    output_json_path = os.path.join(temp_dir, f"{config['name']}.json")
    
    # 4. 生成视频脚本（包含title和subtitle）
    print("\n" + "=" * 60)
    print("步骤 1/8: 生成视频脚本")
    print("=" * 60)
    prompt_gen = PromptGenerator()
    
    # 检查是否已有生成的JSON文件
    items = []
    if os.path.exists(output_json_path):
        try:
            items = load_items_from_json(output_json_path)
            print(f"[脚本] 从已有JSON文件加载了 {len(items)} 个项目")
        except:
            pass
    
    # 如果没有已有数据，生成新的脚本
    # 注意：generate_video_script 会生成 1个封面 + config['images'] 个内容段
    expected_total = config['images'] + 1  # 封面 + 内容段
    if not items or len(items) != expected_total:
        items = prompt_gen.generate_video_script(config['text'], config['images'])
        # 保存初始脚本
        save_items_to_json(items, output_json_path)
    
    # 5. 生成图片提示词
    print("\n" + "=" * 60)
    print("步骤 2/8: 生成图片提示词")
    print("=" * 60)
    prompt_gen.generate_image_prompts(items, text=config.get('text'), style=config['style'])
    save_items_to_json(items, output_json_path)
    
    # 6. 生成图片
    print("\n" + "=" * 60)
    print("步骤 3/8: 生成图片")
    print("=" * 60)
    image_gen = ImageGenerator()
    
    # 准备视频尺寸用于图片生成
    video_size = config['video_size']
    if isinstance(video_size, list):
        image_size = f"{video_size[0]}x{video_size[1]}"
    else:
        image_size = "1080x1920"
    
    image_gen.generate_images_batch(items, image_dir, image_size=image_size)
    
    # 6.5. 保存第一个JSON文件（只包含title, subtitle, Prompt, Image）
    print("\n" + "=" * 60)
    print("步骤 4/8: 保存第一个JSON文件")
    print("=" * 60)
    cleaned_items = clean_items_for_first_json(items)
    save_items_to_json(cleaned_items, output_json_path)
    print(f"[保存] 第一个JSON文件已保存到: {output_json_path}（只包含title, subtitle, Prompt, Image）")
    
    # 7. 拆分过长的subtitle（基于第一个JSON文件）
    print("\n" + "=" * 60)
    print("步骤 5/8: 拆分过长的内容")
    print("=" * 60)
    split_items = []
    for i, item in enumerate(cleaned_items):
        split_result = split_item_if_needed(item, max_chars=50)
        if len(split_result) > 1:
            print(f"[拆分] 第 {i+1} 项拆分为 {len(split_result)} 段")
        split_items.extend(split_result)
    
    # 保存拆分后的JSON到新文件
    split_json_path = os.path.join(temp_dir, f"{config['name']}_split.json")
    save_items_to_json(split_items, split_json_path)
    print(f"[保存] 拆分后的JSON已保存到: {split_json_path}")
    
    # 8. 为拆分后的新items生成语音
    print("\n" + "=" * 60)
    print("步骤 6/8: 为拆分后的内容生成语音")
    print("=" * 60)
    generate_audio_for_items(split_items, config['voice'], audio_dir)
    save_items_to_json(split_items, split_json_path)
    
    # 9. 计算时长并更新到split_items中
    print("\n" + "=" * 60)
    print("步骤 7/8: 计算时长")
    print("=" * 60)
    for i, item in enumerate(split_items):
        if item.get('audio') and (not item.get('duration') or item.get('duration') == 0):
            duration = calculate_audio_duration(item['audio'])
            if duration > 0:
                item['duration'] = duration
                print(f"[时长计算] 第 {i+1} 项：{duration:.2f} 秒")
            else:
                item['duration'] = 3.0  # 默认时长
                print(f"[时长计算] 第 {i+1} 项：使用默认时长 3.0 秒")
    
    save_items_to_json(split_items, split_json_path)
    
    # 10. 生成幻灯片列表（基于拆分后的JSON文件）
    print("\n" + "=" * 60)
    print("步骤 8/8: 生成视频")
    print("=" * 60)
    try:
        slides = generate_slide_list_from_items(split_items)
        if not slides:
            print("[错误] 没有有效的幻灯片")
            return
    except Exception as e:
        print(f"[错误] 生成幻灯片列表失败: {e}")
        return
    
    # 11. 生成视频
    video_size = config['video_size']
    if isinstance(video_size, list):
        video_size = tuple(video_size)
    else:
        video_size = (1080, 1920)
    
    video_gen = VideoGenerator(
        font_path=config['font'],
        video_size=video_size,
        font_size=config['font_size']
    )
    output_file = generate_output_filename(config['name'], temp_dir)
    
    try:
        video_gen.create_video(slides, output_file)
    except Exception as e:
        print(f"[错误] 生成视频失败: {e}")
        return
    
    # 11. 完成
    print("\n" + "=" * 60)
    print("完成")
    print("=" * 60)
    print(f"\n✅ 视频生成完成！")
    print(f"📁 输出文件: {output_file}")
    print(f"📁 临时文件: {temp_dir}")
    print(f"📁 第一个JSON文件: {output_json_path}")
    print(f"📁 拆分后的JSON文件: {split_json_path}")
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
