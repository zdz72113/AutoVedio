"""
提示词生成模块
使用DeepSeek模型生成图片生成提示词
"""
from openai import OpenAI
from config import Config


class PromptGenerator:
    """提示词生成器"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url=Config.DEEPSEEK_BASE_URL
        )
    
    def generate_image_prompts(self, items, template):
        """
        为每段文字生成对应的图片生成提示词，并更新到items中
        
        参数:
            items: 项目列表，每个项目包含 TextTop, TextBottom, Prompt 等字段
            template: 模板配置字典，包含 prompt_template
        """
        prompt_template = template.get('prompt_template', '')
        if not prompt_template:
            raise ValueError("模板中缺少 prompt_template 字段")
        
        for i, item in enumerate(items):
            # 如果已有Prompt，跳过
            if item.get('Prompt'):
                print(f"[提示词生成] 第 {i+1}/{len(items)} 段文本已有提示词，跳过")
                continue
            
            text_top = item.get('TextTop', '') or ''
            text_bottom = item.get('TextBottom', '') or ''
            
            if not text_top and not text_bottom:
                print(f"[警告] 第 {i+1} 项缺少TextTop和TextBottom，跳过")
                continue
            
            # 获取角色描述（PromptTop和PromptBottom）
            prompt_top = item.get('PromptTop', '') or ''
            prompt_bottom = item.get('PromptBottom', '') or ''
            
            if not prompt_top or not prompt_bottom:
                print(f"[警告] 第 {i+1} 项缺少PromptTop或PromptBottom，跳过")
                continue
            
            # 使用模板生成提示词请求，整合PromptTop、PromptBottom、text_top、text_bottom
            prompt_request = prompt_template.format(
                text_top=text_top,
                text_bottom=text_bottom,
                prompt_top=prompt_top,
                prompt_bottom=prompt_bottom
            )
            
            try:
                # 调用DeepSeek生成提示词
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "user", "content": prompt_request}
                    ],
                    temperature=0.7
                )
                full_prompt = response.choices[0].message.content.strip()
                
                item['Prompt'] = full_prompt
                print(f"[提示词生成] 第 {i+1}/{len(items)} 段文本的提示词已生成")
            except Exception as e:
                print(f"[提示词生成] 生成第 {i+1} 段提示词失败: {e}")
                # 使用默认提示词
                item['Prompt'] = f"9:16 vertical illustration, warm healing children's book style. Upper section: {text_top}. Lower section: {text_bottom}. Minimal background with ample white space."
