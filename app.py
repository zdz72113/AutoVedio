"""
Streamlit Web应用
自动化视频生成工具 - 交互式界面
"""
import streamlit as st
import os
import json
from config import Config
from prompt_generator import PromptGenerator
from image_generator import ImageGenerator
from voice_generator import generate_audio_for_items
from video_generator import VideoGenerator
from utils import (
    create_temp_dir,
    save_items_to_json,
    load_items_from_json,
    generate_slide_list_from_items,
    generate_output_filename,
    calculate_audio_duration
)
from prompt_templates import STYLE_DESCRIPTIONS
import time


# 页面配置
st.set_page_config(
    page_title="自动视频生成工具",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化 session_state
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'config' not in st.session_state:
    st.session_state.config = {}
if 'video_items' not in st.session_state:
    st.session_state.video_items = []
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = None
if 'output_file' not in st.session_state:
    st.session_state.output_file = None


def validate_config():
    """验证API配置"""
    try:
        Config.validate()
        return True, None
    except ValueError as e:
        return False, str(e)


def init_project():
    """初始化项目目录"""
    if st.session_state.config.get('name'):
        temp_dir = create_temp_dir(st.session_state.config['name'])
        st.session_state.temp_dir = temp_dir
        os.makedirs(os.path.join(temp_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, "audio"), exist_ok=True)
        return temp_dir
    return None


def get_available_voices():
    """获取可用的语音列表（示例，实际需要根据Azure配置）"""
    return [
        "zh-CN-XiaoxiaoNeural",
        "zh-CN-YunxiNeural",
        "zh-CN-YunyangNeural",
        "zh-CN-XiaoyiNeural",
        "zh-CN-YunjianNeural",
        "zh-CN-XiaohanNeural",
        "zh-CN-XiaomengNeural",
        "zh-CN-XiaomoNeural",
        "zh-CN-XiaoqiuNeural",
        "zh-CN-XiaoruiNeural",
        "zh-CN-XiaoshuangNeural",
        "zh-CN-XiaoxuanNeural",
        "zh-CN-XiaoyanNeural",
        "zh-CN-XiaoyouNeural",
        "zh-CN-XiaozhenNeural"
    ]


# 主标题
st.title("🎬 自动视频生成工具")
st.markdown("---")

# 侧边栏 - 步骤导航
with st.sidebar:
    st.header("📋 步骤导航")
    steps = [
        ("1️⃣", "输入配置", 1),
        ("2️⃣", "生成脚本", 2),
        ("3️⃣", "生成素材", 3),
        ("4️⃣", "生成视频", 4)
    ]
    
    for icon, name, step_num in steps:
        if st.session_state.step == step_num:
            st.markdown(f"**{icon} {name}** ✅")
        else:
            st.markdown(f"{icon} {name}")
    
    st.markdown("---")
    
    # 配置验证
    config_valid, config_error = validate_config()
    if config_valid:
        st.success("✅ API配置正常")
    else:
        st.error(f"❌ 配置错误：{config_error}")
        st.info("请检查 .env 文件中的API密钥配置")


# ==================== 第一步：输入配置 ====================
if st.session_state.step == 1:
    st.header("第一步：输入文字和选择配置")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 输入文字
        text = st.text_area(
            "输入文字内容",
            value=st.session_state.config.get('text', ''),
            height=200,
            help="输入要生成视频的文字内容"
        )
        
        # 项目名称
        project_name = st.text_input(
            "项目名称",
            value=st.session_state.config.get('name', ''),
            help="用于保存临时文件和输出文件"
        )
    
    with col2:
        # 图片数量
        num_images = st.number_input(
            "图片数量",
            min_value=1,
            max_value=20,
            value=st.session_state.config.get('images', 3),
            help="需要生成的内容段数（不包括封面）"
        )
        
        # 视频尺寸
        video_size_options = {
            "竖屏 (1080x1920)": [1080, 1920],
            "横屏 (1920x1080)": [1920, 1080],
            "方形 (1080x1080)": [1080, 1080]
        }
        video_size_label = st.selectbox(
            "视频尺寸",
            options=list(video_size_options.keys()),
            index=0,
            help="选择视频输出尺寸"
        )
        video_size = video_size_options[video_size_label]
        
        # 图片风格
        style = st.selectbox(
            "图片风格",
            options=list(STYLE_DESCRIPTIONS.keys()),
            index=0,
            help="选择图片生成风格"
        )
        st.caption(STYLE_DESCRIPTIONS[style])
        
        # 语音选择
        voice = st.selectbox(
            "语音",
            options=get_available_voices(),
            index=0,
            help="选择语音合成音色"
        )
    
    # 高级配置（可折叠）
    with st.expander("高级配置"):
        col3, col4, col5 = st.columns(3)
        
        with col3:
            font_path = st.text_input(
                "字体路径",
                value=st.session_state.config.get('font', './resource/AlibabaPuHuiTi-3-75-SemiBold.ttf'),
                help="字体文件路径"
            )
        
        with col4:
            font_size = st.number_input(
                "字体大小",
                min_value=20,
                max_value=100,
                value=st.session_state.config.get('font_size', 50),
                help="字幕字体大小"
            )
        
        with col5:
            font_color = st.color_picker(
                "字体颜色",
                value=st.session_state.config.get('font_color', '#FFFFFF'),
                help="字幕字体颜色"
            )
    
    # 保存配置并进入下一步
    if st.button("下一步：生成脚本", type="primary", use_container_width=True):
        if not text.strip():
            st.error("请输入文字内容")
        elif not project_name.strip():
            st.error("请输入项目名称")
        else:
            st.session_state.config = {
                'text': text,
                'name': project_name,
                'images': num_images,
                'video_size': video_size,
                'style': style,
                'voice': voice,
                'font': font_path,
                'font_size': font_size,
                'font_color': font_color
            }
            st.session_state.temp_dir = init_project()
            st.session_state.step = 2
            st.rerun()


# ==================== 第二步：生成脚本 ====================
elif st.session_state.step == 2:
    st.header("第二步：生成 Title, Subtitle, Prompt")
    
    if not st.session_state.config:
        st.error("请先完成第一步配置")
        if st.button("返回第一步"):
            st.session_state.step = 1
            st.rerun()
    else:
        # 显示配置摘要
        with st.expander("📋 配置摘要", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**项目名称：**", st.session_state.config['name'])
                st.write("**图片数量：**", st.session_state.config['images'])
            with col2:
                st.write("**视频尺寸：**", st.session_state.config['video_size'])
                st.write("**图片风格：**", st.session_state.config['style'])
            with col3:
                st.write("**语音：**", st.session_state.config['voice'])
        
        # 生成脚本按钮
        if not st.session_state.video_items:
            if st.button("🚀 生成脚本和提示词", type="primary", use_container_width=True):
                with st.spinner("正在生成脚本和提示词，请稍候..."):
                    try:
                        prompt_gen = PromptGenerator()
                        
                        # 生成视频脚本
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        status_text.text("正在生成视频脚本...")
                        progress_bar.progress(20)
                        items = prompt_gen.generate_video_script(
                            st.session_state.config['text'],
                            st.session_state.config['images']
                        )
                        
                        status_text.text("正在生成图片提示词...")
                        progress_bar.progress(60)
                        prompt_gen.generate_image_prompts(
                            items,
                            text=st.session_state.config.get('text'),
                            style=st.session_state.config.get('style', '动画')
                        )
                        
                        progress_bar.progress(100)
                        status_text.text("生成完成！")
                        
                        st.session_state.video_items = items
                        
                        # 保存到文件
                        if st.session_state.temp_dir:
                            output_json_path = os.path.join(
                                st.session_state.temp_dir,
                                f"{st.session_state.config['name']}.json"
                            )
                            save_items_to_json(items, output_json_path)
                        
                        time.sleep(0.5)
                        st.success("✅ 脚本和提示词生成成功！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"生成失败：{str(e)}")
        else:
            items = st.session_state.video_items
            st.success(f"✅ 已生成 {len(items)} 段内容（1个封面 + {len(items)-1} 段内容）")
            
            # 编辑和重新生成选项
            for i, item in enumerate(items):
                with st.expander(f"📝 第 {i+1} 段 {'(封面)' if i == 0 else ''}", expanded=(i == 0)):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # 编辑 Title
                        title = st.text_input(
                            f"Title {i+1}",
                            value=item.get('title', ''),
                            key=f"title_{i}"
                        )
                        
                        # 编辑 Subtitle
                        subtitle = st.text_area(
                            f"Subtitle {i+1}",
                            value=item.get('subtitle', ''),
                            height=100,
                            key=f"subtitle_{i}"
                        )
                        
                        # 编辑 Prompt
                        prompt = st.text_area(
                            f"Prompt {i+1}",
                            value=item.get('Prompt', ''),
                            height=150,
                            key=f"prompt_{i}",
                            help="图片生成提示词"
                        )
                    
                    with col2:
                        st.write("")  # 占位
                        if st.button("🔄 重新生成", key=f"regenerate_{i}", use_container_width=True):
                            with st.spinner("正在重新生成..."):
                                try:
                                    prompt_gen = PromptGenerator()
                                    if i == 0:
                                        # 重新生成封面
                                        cover_prompt = f"""请基于以下文本内容，生成一个视频封面场景的数据。封面需要包含：
1. title: 整个视频的标题（要吸引人，概括视频主题，长度不超过15个字）
2. subtitle: 引导观众观看的字幕内容（用于语音合成，要能引起观众兴趣，引导他们继续观看）

要求：
- title要简洁有力，能够概括整个视频的核心主题
- subtitle要具有引导性，能够引起观众的好奇心和观看欲望
- subtitle要适合语音朗读，长度适中（建议20-40字）

文本内容：
{st.session_state.config['text']}

请以JSON对象格式返回，包含title和subtitle字段。格式如下：
{{"title": "视频标题", "subtitle": "引导性字幕内容"}}

只返回JSON对象，不要包含其他文字说明。"""
                                        
                                        response = prompt_gen.client.chat.completions.create(
                                            model="deepseek-chat",
                                            messages=[{"role": "user", "content": cover_prompt}],
                                            temperature=0.7
                                        )
                                        response_text = response.choices[0].message.content.strip()
                                        if "```json" in response_text:
                                            response_text = response_text.split("```json")[1].split("```")[0].strip()
                                        elif "```" in response_text:
                                            response_text = response_text.split("```")[1].split("```")[0].strip()
                                        
                                        new_item = json.loads(response_text)
                                        item['title'] = new_item.get('title', item.get('title', ''))
                                        item['subtitle'] = new_item.get('subtitle', item.get('subtitle', ''))
                                    else:
                                        # 重新生成内容段
                                        script_prompt = f"""请基于以下文本内容，生成一段视频脚本内容。需要包含：
1. title: 该段的标题（简短，作为字幕显示）
2. subtitle: 该段的字幕内容（用于语音合成）

要求：
- title要简洁有力，长度不超过10个字
- subtitle要适合语音朗读，长度适中

文本内容：
{st.session_state.config['text']}

请以JSON对象格式返回，包含title和subtitle字段。格式如下：
{{"title": "标题", "subtitle": "字幕内容"}}

只返回JSON对象，不要包含其他文字说明。"""
                                        
                                        response = prompt_gen.client.chat.completions.create(
                                            model="deepseek-chat",
                                            messages=[{"role": "user", "content": script_prompt}],
                                            temperature=0.7
                                        )
                                        response_text = response.choices[0].message.content.strip()
                                        if "```json" in response_text:
                                            response_text = response_text.split("```json")[1].split("```")[0].strip()
                                        elif "```" in response_text:
                                            response_text = response_text.split("```")[1].split("```")[0].strip()
                                        
                                        new_item = json.loads(response_text)
                                        item['title'] = new_item.get('title', item.get('title', ''))
                                        item['subtitle'] = new_item.get('subtitle', item.get('subtitle', ''))
                                    
                                    # 重新生成提示词
                                    style = st.session_state.config.get('style', '动画')
                                    style_desc = STYLE_DESCRIPTIONS.get(style, STYLE_DESCRIPTIONS["动画"])
                                    
                                    if i == 0:
                                        from prompt_templates import get_cover_image_prompt_template
                                        prompt_request = get_cover_image_prompt_template(
                                            item['title'], item['subtitle'], style_desc
                                        )
                                    else:
                                        from prompt_templates import get_content_image_prompt_template
                                        prompt_request = get_content_image_prompt_template(
                                            item['title'], item['subtitle'], style_desc
                                        )
                                    
                                    response = prompt_gen.client.chat.completions.create(
                                        model="deepseek-chat",
                                        messages=[{"role": "user", "content": prompt_request}],
                                        temperature=0.7
                                    )
                                    content_prompt = response.choices[0].message.content.strip()
                                    
                                    # 生成统一风格提示词
                                    unified_prompt = prompt_gen.generate_unified_style_prompt(
                                        st.session_state.config.get('text', ''),
                                        style
                                    )
                                    item['Prompt'] = f"{content_prompt}{unified_prompt}"
                                    
                                    st.session_state.video_items[i] = item
                                    st.success(f"✅ 第 {i+1} 段重新生成成功！")
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"重新生成失败：{str(e)}")
                    
                    # 更新 item
                    item['title'] = title
                    item['subtitle'] = subtitle
                    item['Prompt'] = prompt
                    st.session_state.video_items[i] = item
            
            # 保存按钮
            if st.button("💾 保存修改", use_container_width=True):
                if st.session_state.temp_dir:
                    output_json_path = os.path.join(
                        st.session_state.temp_dir,
                        f"{st.session_state.config['name']}.json"
                    )
                    save_items_to_json(st.session_state.video_items, output_json_path)
                    st.success("✅ 修改已保存")
            
            # 导航按钮
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("⬅️ 返回上一步", use_container_width=True):
                    st.session_state.step = 1
                    st.rerun()
            with col2:
                if st.button("下一步：生成素材 ➡️", type="primary", use_container_width=True):
                    st.session_state.step = 3
                    st.rerun()


# ==================== 第三步：生成素材 ====================
elif st.session_state.step == 3:
    st.header("第三步：生成图片和语音")
    
    if not st.session_state.video_items:
        st.error("请先完成第二步生成脚本")
        if st.button("返回第二步"):
            st.session_state.step = 2
            st.rerun()
    else:
        image_dir = os.path.join(st.session_state.temp_dir, "images") if st.session_state.temp_dir else "images"
        audio_dir = os.path.join(st.session_state.temp_dir, "audio") if st.session_state.temp_dir else "audio"
        os.makedirs(image_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)
        
        # 批量生成按钮
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🖼️ 批量生成所有图片", type="primary", use_container_width=True):
                with st.spinner("正在生成图片，这可能需要一些时间..."):
                    try:
                        image_gen = ImageGenerator()
                        video_size = st.session_state.config['video_size']
                        image_size = f"{video_size[0]}x{video_size[1]}"
                        
                        progress_bar = st.progress(0)
                        for i, item in enumerate(st.session_state.video_items):
                            if not item.get('Image'):
                                status_text = st.empty()
                                status_text.text(f"正在生成第 {i+1}/{len(st.session_state.video_items)} 张图片...")
                                image_gen.generate_images_batch([item], image_dir, image_size=image_size)
                                progress_bar.progress((i + 1) / len(st.session_state.video_items))
                                time.sleep(0.5)
                        
                        # 保存
                        if st.session_state.temp_dir:
                            output_json_path = os.path.join(
                                st.session_state.temp_dir,
                                f"{st.session_state.config['name']}.json"
                            )
                            save_items_to_json(st.session_state.video_items, output_json_path)
                        
                        st.success("✅ 所有图片生成完成！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"生成图片失败：{str(e)}")
        
        with col2:
            if st.button("🔊 批量生成所有语音", type="primary", use_container_width=True):
                with st.spinner("正在生成语音，请稍候..."):
                    try:
                        progress_bar = st.progress(0)
                        for i, item in enumerate(st.session_state.video_items):
                            if not item.get('audio'):
                                status_text = st.empty()
                                status_text.text(f"正在生成第 {i+1}/{len(st.session_state.video_items)} 段语音...")
                                generate_audio_for_items(
                                    [item],
                                    st.session_state.config['voice'],
                                    audio_dir
                                )
                                progress_bar.progress((i + 1) / len(st.session_state.video_items))
                                time.sleep(0.5)
                        
                        # 保存
                        if st.session_state.temp_dir:
                            output_json_path = os.path.join(
                                st.session_state.temp_dir,
                                f"{st.session_state.config['name']}.json"
                            )
                            save_items_to_json(st.session_state.video_items, output_json_path)
                        
                        st.success("✅ 所有语音生成完成！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"生成语音失败：{str(e)}")
        
        st.markdown("---")
        
        # 逐项显示和编辑
        for i, item in enumerate(st.session_state.video_items):
            with st.expander(f"📦 第 {i+1} 段 {'(封面)' if i == 0 else ''}", expanded=(i == 0)):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Title:** {item.get('title', '')}")
                    st.write(f"**Subtitle:** {item.get('subtitle', '')}")
                    
                    # 图片部分
                    st.subheader("🖼️ 图片")
                    if item.get('Image') and os.path.exists(item['Image']):
                        st.image(item['Image'], use_container_width=True)
                        st.caption(f"图片路径: {item['Image']}")
                    else:
                        st.info("尚未生成图片")
                    
                    # 图片上传/重新生成
                    col_img1, col_img2 = st.columns(2)
                    with col_img1:
                        uploaded_image = st.file_uploader(
                            f"上传图片替换 {i+1}",
                            type=['jpg', 'jpeg', 'png'],
                            key=f"upload_img_{i}"
                        )
                        if uploaded_image:
                            image_path = os.path.join(image_dir, f"image_{i+1}.jpg")
                            with open(image_path, "wb") as f:
                                f.write(uploaded_image.getbuffer())
                            item['Image'] = image_path
                            st.session_state.video_items[i] = item
                            st.success("✅ 图片已上传")
                            st.rerun()
                    
                    with col_img2:
                        if st.button(f"🔄 重新生成图片 {i+1}", key=f"regenerate_img_{i}", use_container_width=True):
                            with st.spinner("正在生成图片..."):
                                try:
                                    image_gen = ImageGenerator()
                                    video_size = st.session_state.config['video_size']
                                    image_size = f"{video_size[0]}x{video_size[1]}"
                                    output_path = os.path.join(image_dir, f"image_{i+1}.jpg")
                                    
                                    if item.get('Prompt'):
                                        result = image_gen.generate_image(item['Prompt'], output_path, size=image_size)
                                        if result:
                                            item['Image'] = result
                                            st.session_state.video_items[i] = item
                                            
                                            # 保存
                                            if st.session_state.temp_dir:
                                                output_json_path = os.path.join(
                                                    st.session_state.temp_dir,
                                                    f"{st.session_state.config['name']}.json"
                                                )
                                                save_items_to_json(st.session_state.video_items, output_json_path)
                                            
                                            st.success("✅ 图片生成成功！")
                                            st.rerun()
                                        else:
                                            st.error("图片生成失败")
                                    else:
                                        st.error("缺少提示词，请先完成第二步")
                                except Exception as e:
                                    st.error(f"生成失败：{str(e)}")
                
                with col2:
                    # 语音部分
                    st.subheader("🔊 语音")
                    if item.get('audio') and os.path.exists(item['audio']):
                        st.audio(item['audio'])
                        st.caption(f"音频路径: {item['audio']}")
                        
                        # 计算时长
                        if not item.get('duration'):
                            try:
                                duration = calculate_audio_duration(item['audio'])
                                if duration > 0:
                                    item['duration'] = duration
                                    st.session_state.video_items[i] = item
                            except:
                                pass
                        
                        if item.get('duration'):
                            st.caption(f"时长: {item['duration']:.2f} 秒")
                    else:
                        st.info("尚未生成语音")
                    
                    # 重新生成语音
                    if st.button(f"🔄 重新生成语音 {i+1}", key=f"regenerate_audio_{i}", use_container_width=True):
                        with st.spinner("正在生成语音..."):
                            try:
                                audio_file = os.path.join(audio_dir, f"audio_{i+1}.mp3")
                                if item.get('subtitle'):
                                    from voice_generator import text_to_speech
                                    text_to_speech(
                                        item['subtitle'],
                                        audio_file,
                                        voice_name=st.session_state.config['voice']
                                    )
                                    item['audio'] = audio_file
                                    
                                    # 计算时长
                                    duration = calculate_audio_duration(audio_file)
                                    if duration > 0:
                                        item['duration'] = duration
                                    
                                    st.session_state.video_items[i] = item
                                    
                                    # 保存
                                    if st.session_state.temp_dir:
                                        output_json_path = os.path.join(
                                            st.session_state.temp_dir,
                                            f"{st.session_state.config['name']}.json"
                                        )
                                        save_items_to_json(st.session_state.video_items, output_json_path)
                                    
                                    st.success("✅ 语音生成成功！")
                                    st.rerun()
                                else:
                                    st.error("缺少字幕内容")
                            except Exception as e:
                                st.error(f"生成失败：{str(e)}")
        
        # 检查是否所有素材都已生成
        all_images_ready = all(item.get('Image') and os.path.exists(item['Image']) for item in st.session_state.video_items)
        all_audio_ready = all(item.get('audio') and os.path.exists(item['audio']) for item in st.session_state.video_items)
        
        if all_images_ready and all_audio_ready:
            st.success("✅ 所有素材已准备完成，可以进入下一步生成视频！")
        
        # 导航按钮
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅️ 返回上一步", use_container_width=True):
                st.session_state.step = 2
                st.rerun()
        with col2:
            if st.button("下一步：生成视频 ➡️", type="primary", use_container_width=True, disabled=not (all_images_ready and all_audio_ready)):
                st.session_state.step = 4
                st.rerun()


# ==================== 第四步：生成视频 ====================
elif st.session_state.step == 4:
    st.header("第四步：合并生成视频")
    
    if not st.session_state.video_items:
        st.error("请先完成前面的步骤")
        if st.button("返回"):
            st.session_state.step = 3
            st.rerun()
    else:
        # 检查素材完整性
        missing_images = [i+1 for i, item in enumerate(st.session_state.video_items) if not item.get('Image') or not os.path.exists(item['Image'])]
        missing_audio = [i+1 for i, item in enumerate(st.session_state.video_items) if not item.get('audio') or not os.path.exists(item['audio'])]
        
        if missing_images or missing_audio:
            if missing_images:
                st.warning(f"⚠️ 缺少图片：第 {', '.join(map(str, missing_images))} 段")
            if missing_audio:
                st.warning(f"⚠️ 缺少语音：第 {', '.join(map(str, missing_audio))} 段")
            if st.button("返回上一步补充素材"):
                st.session_state.step = 3
                st.rerun()
        else:
            # 生成视频按钮
            if not st.session_state.output_file or not os.path.exists(st.session_state.output_file):
                if st.button("🎬 生成视频", type="primary", use_container_width=True):
                    with st.spinner("正在生成视频，这可能需要较长时间，请耐心等待..."):
                        try:
                            # 确保所有时长都已计算
                            for item in st.session_state.video_items:
                                if not item.get('duration') or item.get('duration') == 0:
                                    if item.get('audio'):
                                        duration = calculate_audio_duration(item['audio'])
                                        if duration > 0:
                                            item['duration'] = duration
                                        else:
                                            item['duration'] = 3.0
                                    else:
                                        item['duration'] = 3.0
                            
                            # 生成幻灯片列表
                            slides = generate_slide_list_from_items(st.session_state.video_items)
                            
                            if not slides:
                                st.error("无法生成幻灯片列表")
                            else:
                                # 创建视频生成器
                                video_size = st.session_state.config['video_size']
                                if isinstance(video_size, list):
                                    video_size = tuple(video_size)
                                else:
                                    video_size = (1080, 1920)
                                
                                video_gen = VideoGenerator(
                                    font_path=st.session_state.config['font'],
                                    video_size=video_size,
                                    font_size=st.session_state.config['font_size']
                                )
                                
                                # 生成输出文件名
                                output_file = generate_output_filename(
                                    st.session_state.config['name'],
                                    st.session_state.temp_dir
                                )
                                
                                # 生成视频
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                status_text.text("正在合成视频...")
                                progress_bar.progress(50)
                                
                                video_gen.create_video(slides, output_file)
                                
                                progress_bar.progress(100)
                                status_text.text("视频生成完成！")
                                
                                st.session_state.output_file = output_file
                                
                                # 保存最终状态
                                if st.session_state.temp_dir:
                                    output_json_path = os.path.join(
                                        st.session_state.temp_dir,
                                        f"{st.session_state.config['name']}.json"
                                    )
                                    save_items_to_json(st.session_state.video_items, output_json_path)
                                
                                st.success("✅ 视频生成成功！")
                                st.rerun()
                        except Exception as e:
                            st.error(f"生成视频失败：{str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
            
            # 显示视频预览和下载
            if st.session_state.output_file and os.path.exists(st.session_state.output_file):
                st.success("✅ 视频已生成！")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("📹 视频预览")
                    # Streamlit 支持直接显示视频
                    video_file = open(st.session_state.output_file, 'rb')
                    video_bytes = video_file.read()
                    st.video(video_bytes)
                    video_file.close()
                
                with col2:
                    st.subheader("📥 下载视频")
                    st.info(f"**文件路径：**\n{st.session_state.output_file}")
                    
                    # 文件大小
                    file_size = os.path.getsize(st.session_state.output_file) / (1024 * 1024)  # MB
                    st.caption(f"文件大小: {file_size:.2f} MB")
                    
                    # 下载按钮
                    with open(st.session_state.output_file, 'rb') as f:
                        st.download_button(
                            label="⬇️ 下载视频",
                            data=f.read(),
                            file_name=os.path.basename(st.session_state.output_file),
                            mime="video/mp4",
                            use_container_width=True,
                            type="primary"
                        )
                    
                    # 重新生成按钮
                    if st.button("🔄 重新生成视频", use_container_width=True):
                        old_file = st.session_state.output_file
                        st.session_state.output_file = None
                        if old_file and os.path.exists(old_file):
                            try:
                                os.remove(old_file)
                            except:
                                pass
                        st.rerun()
                
                # 项目信息
                with st.expander("📋 项目信息"):
                    st.write(f"**项目名称：** {st.session_state.config['name']}")
                    st.write(f"**视频尺寸：** {st.session_state.config['video_size']}")
                    st.write(f"**图片数量：** {len(st.session_state.video_items)}")
                    st.write(f"**临时目录：** {st.session_state.temp_dir}")
                    st.write(f"**输出文件：** {st.session_state.output_file}")
            
            # 导航按钮
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("⬅️ 返回上一步", use_container_width=True):
                    st.session_state.step = 3
                    st.rerun()
            with col2:
                if st.button("🔄 重新开始", use_container_width=True):
                    st.session_state.step = 1
                    st.session_state.config = {}
                    st.session_state.video_items = []
                    st.session_state.temp_dir = None
                    st.session_state.output_file = None
                    st.rerun()

# 页脚
st.markdown("---")
st.caption("🎬 自动视频生成工具 | 使用 Streamlit 构建")

