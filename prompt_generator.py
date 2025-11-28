"""
提示词生成模块
使用DeepSeek模型生成视频脚本和图片生成提示词
"""
from openai import OpenAI
from config import Config
import json


class PromptGenerator:
    """提示词生成器"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url=Config.DEEPSEEK_BASE_URL
        )
    
    def generate_video_script(self, text, num_segments):
        """
        基于文本生成视频脚本，包含N段内容，每段包含title和subtitle
        
        参数:
            text: 输入文本
            num_segments: 需要生成的段数（图片个数）
        
        返回:
            list: 项目列表，每个项目包含 title, subtitle 字段
        """
        script_prompt = f"""请基于以下文本内容，生成一个包含{num_segments}段内容的视频脚本。每段内容需要包含：
1. title: 该段的标题（简短，作为字幕显示）
2. subtitle: 该段的字幕内容（用于语音合成）

要求：
- 每段内容应该逻辑连贯，围绕主题展开
- title要简洁有力，适合作为视频字幕
- subtitle要适合语音朗读，长度适中
- 总共生成{num_segments}段内容

文本内容：
{text}

请以JSON数组格式返回，每个元素包含title和subtitle字段。格式如下：
[
  {{"title": "标题1", "subtitle": "字幕内容1"}},
  {{"title": "标题2", "subtitle": "字幕内容2"}},
  ...
]

只返回JSON数组，不要包含其他文字说明。"""
        
        try:
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
            items = json.loads(response_text)
            
            if not isinstance(items, list):
                raise ValueError("返回的不是数组格式")
            
            if len(items) != num_segments:
                print(f"[警告] 期望生成{num_segments}段，实际生成{len(items)}段")
            
            print(f"[脚本生成] 成功生成{len(items)}段视频脚本")
            return items
            
        except Exception as e:
            print(f"[脚本生成] 生成视频脚本失败: {e}")
            # 如果生成失败，使用简单分割方式
            print("[脚本生成] 使用备用方案：简单分割文本")
            return self._fallback_script_generation(text, num_segments)
    
    def _fallback_script_generation(self, text, num_segments):
        """备用方案：简单分割文本"""
        items = []
        words_per_segment = max(10, len(text) // num_segments)
        
        for i in range(num_segments):
            start_idx = i * words_per_segment
            end_idx = (i + 1) * words_per_segment if i < num_segments - 1 else len(text)
            segment_text = text[start_idx:end_idx].strip()
            
            if segment_text:
                items.append({
                    "title": f"第{i+1}段",
                    "subtitle": segment_text
                })
        
        return items
    
    def generate_image_prompts(self, items):
        """
        为每段内容生成对应的图片生成提示词，并更新到items中
        
        参数:
            items: 项目列表，每个项目包含 title, subtitle 等字段
        """
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
            
            # 生成图片提示词
            prompt_request = f"""请为以下视频内容生成一个详细的图片生成提示词（英文）。

标题：{title}
字幕：{subtitle}

要求：
- 提示词要详细描述画面内容
- 适合9:16竖屏比例
- 风格要统一，适合视频内容
- 使用英文描述

只返回提示词内容，不要包含其他说明。"""
            
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "user", "content": prompt_request}
                    ],
                    temperature=0.7
                )
                full_prompt = response.choices[0].message.content.strip()
                
                item['Prompt'] = full_prompt
                print(f"[提示词生成] 第 {i+1}/{len(items)} 段的图片提示词已生成")
            except Exception as e:
                print(f"[提示词生成] 生成第 {i+1} 段提示词失败: {e}")
                # 使用默认提示词
                item['Prompt'] = f"9:16 vertical illustration, {subtitle}, detailed, high quality"
