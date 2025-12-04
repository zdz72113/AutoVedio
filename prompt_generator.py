"""
提示词生成模块
使用DeepSeek模型生成视频脚本和图片生成提示词
"""
from openai import OpenAI
from config import Config
import json
from prompt_templates import (
    STYLE_DESCRIPTIONS,
    DEFAULT_COVER,
    get_cover_prompt_template,
    get_script_prompt_template,
    get_unified_style_prompt_template,
    get_default_unified_prompt,
    get_cover_image_prompt_template,
    get_content_image_prompt_template
)


class PromptGenerator:
    """提示词生成器"""
    
    # 从模板文件导入风格描述
    STYLE_DESCRIPTIONS = STYLE_DESCRIPTIONS
    
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url=Config.DEEPSEEK_BASE_URL
        )
    
    @classmethod
    def get_available_styles(cls):
        """
        获取所有可用的风格列表
        
        返回:
            list: 风格名称列表
        """
        return list(cls.STYLE_DESCRIPTIONS.keys())
    
    @classmethod
    def is_valid_style(cls, style):
        """
        检查风格是否有效
        
        参数:
            style: 风格名称
        
        返回:
            bool: 是否为有效风格
        """
        return style in cls.STYLE_DESCRIPTIONS
    
    def generate_video_script(self, text, num_segments):
        """
        基于文本生成视频脚本，包含封面+N段内容，每段包含title和subtitle
        
        参数:
            text: 输入文本
            num_segments: 需要生成的内容段数（不包括封面，图片总数为num_segments+1）
        
        返回:
            list: 项目列表，第一个是封面，后面是内容段，每个项目包含 title, subtitle 字段
        """
        items = []
        
        # 1. 先生成封面数据
        try:
            print(f"[脚本生成] 正在生成封面数据...")
            cover_prompt = get_cover_prompt_template(text)
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "user", "content": cover_prompt}
                ],
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # 尝试提取JSON（可能包含markdown代码块）
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # 解析JSON
            cover_item = json.loads(response_text)
            
            if not isinstance(cover_item, dict):
                raise ValueError("封面返回的不是对象格式")
            
            if 'title' not in cover_item or 'subtitle' not in cover_item:
                raise ValueError("封面缺少title或subtitle字段")
            
            items.append(cover_item)
            print(f"[脚本生成] 封面数据生成成功：{cover_item.get('title', '')}")
            
        except Exception as e:
            print(f"[脚本生成] 生成封面数据失败: {e}")
            # 如果封面生成失败，使用默认封面
            items.append(DEFAULT_COVER.copy())
            print(f"[脚本生成] 使用默认封面数据")
        
        # 2. 生成内容段
        try:
            script_prompt = get_script_prompt_template(text, num_segments)
            
            print(f"[脚本生成] 正在生成{num_segments}段视频脚本...")
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "user", "content": script_prompt}
                ],
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # 尝试提取JSON（可能包含markdown代码块）
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # 解析JSON
            content_items = json.loads(response_text)
            
            if not isinstance(content_items, list):
                raise ValueError("返回的不是数组格式")
            
            if len(content_items) != num_segments:
                print(f"[警告] 期望生成{num_segments}段，实际生成{len(content_items)}段")
            
            # 将内容段添加到列表中
            items.extend(content_items)
            print(f"[脚本生成] 成功生成{len(content_items)}段视频脚本")
            
        except Exception as e:
            print(f"[脚本生成] 生成视频脚本失败: {e}")
        
        print(f"[脚本生成] 总共生成 {len(items)} 段（1个封面 + {len(items)-1} 段内容）")
        return items

    def generate_unified_style_prompt(self, text, style="动画"):
        """
        基于文本内容生成统一的风格提示词，用于保持所有图片的风格及角色一致
        
        参数:
            text: 输入文本内容
            style: 风格类型，默认为"动画"
        
        返回:
            str: 统一的风格提示词
        """
        # 验证风格有效性
        if not self.is_valid_style(style):
            print(f"[警告] 风格 '{style}' 无效，使用默认风格 '动画'")
            style = "动画"
        
        # 获取风格描述
        style_desc = self.STYLE_DESCRIPTIONS.get(style, self.STYLE_DESCRIPTIONS["动画"])
        
        # 截取文本的前500字用于生成统一风格（避免提示词过长）
        text_preview = text[:500] if len(text) > 500 else text
        if len(text) > 500:
            text_preview += "..."
        
        unified_prompt_request = get_unified_style_prompt_template(text_preview, style_desc)
        
        try:
            print(f"[统一风格] 正在生成统一风格提示词（风格：{style}）...")
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "user", "content": unified_prompt_request}
                ],
                temperature=0.5  # 使用较低的温度以确保风格一致性
            )
            unified_prompt = response.choices[0].message.content.strip()
            
            # 确保统一提示词以逗号开头（用于合并）
            if not unified_prompt.startswith('，') and not unified_prompt.startswith(','):
                unified_prompt = '，' + unified_prompt
            
            print(f"[统一风格] 统一风格提示词已生成（长度：{len(unified_prompt)} 字）")
            return unified_prompt
        except Exception as e:
            print(f"[统一风格] 生成统一风格提示词失败: {e}")
            # 返回默认的统一风格提示词
            return get_default_unified_prompt(style_desc)
    
    def generate_image_prompts(self, items, text=None, style="动画", unified_prompt=None):
        """
        为每段内容生成对应的图片生成提示词，并更新到items中
        
        参数:
            items: 项目列表，每个项目包含 title, subtitle 等字段
            text: 输入文本内容，用于生成统一风格提示词
            style: 风格类型，默认为"动画"
            unified_prompt: 可选的统一风格提示词，如果不提供则自动生成
        """
        # 验证风格有效性
        if not self.is_valid_style(style):
            print(f"[警告] 风格 '{style}' 无效，使用默认风格 '动画'")
            style = "动画"
        
        # 如果没有提供统一提示词，则生成一个
        if unified_prompt is None and text:
            unified_prompt = self.generate_unified_style_prompt(text, style)
        elif unified_prompt is None:
            # 如果没有文本，使用默认的统一提示词
            style_desc = self.STYLE_DESCRIPTIONS.get(style, self.STYLE_DESCRIPTIONS["动画"])
            unified_prompt = get_default_unified_prompt(style_desc)
        
        # 获取风格描述
        style_desc = self.STYLE_DESCRIPTIONS.get(style, self.STYLE_DESCRIPTIONS["动画"])
        
        print(f"[提示词生成] 开始为 {len(items)} 段内容生成图片提示词（风格：{style}）")
        
        for i, item in enumerate(items):
            # 如果已有Prompt，跳过
            if item.get('Prompt'):
                print(f"[提示词生成] 第 {i+1}/{len(items)} 段已有提示词，跳过")
                continue
            
            title = item.get('title', '')
            subtitle = item.get('subtitle', '')
            
            if not title and not subtitle:
                print(f"[警告] 第 {i+1} 项缺少title和subtitle，跳过")
                continue
            
            # 判断是否为封面（第一项）
            is_cover = (i == 0)
            
            # 生成图片提示词
            if is_cover:
                # 封面提示词要求更注重视觉吸引力
                prompt_request = get_cover_image_prompt_template(title, subtitle, style_desc)
            else:
                # 内容段提示词
                prompt_request = get_content_image_prompt_template(title, subtitle, style_desc)
            
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "user", "content": prompt_request}
                    ],
                    temperature=0.7
                )
                content_prompt = response.choices[0].message.content.strip()
                
                # 合并内容提示词和统一风格提示词
                full_prompt = f"{content_prompt}{unified_prompt}"
                
                item['Prompt'] = full_prompt
                print(f"[提示词生成] 第 {i+1}/{len(items)} 段的图片提示词已生成（总长度：{len(full_prompt)} 字）")
            except Exception as e:
                print(f"[提示词生成] 生成第 {i+1} 段提示词失败: {e}")
        
        print(f"[提示词生成] 完成！共生成 {len([item for item in items if item.get('Prompt')])} 个提示词")
