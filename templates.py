"""
模板配置模块
从Template文件夹中的JSON文件加载模板配置
"""
import json
import os


def get_template(template_name):
    """
    从JSON文件加载模板配置
    
    参数:
        template_name: 模板名称（对应Template文件夹中的JSON文件名，不含扩展名）
    
    返回:
        dict: 模板配置字典，如果不存在则返回默认模板
    """
    template_dir = "Template"
    template_file = os.path.join(template_dir, f"{template_name}.json")
    
    # 如果文件不存在，尝试使用default模板
    if not os.path.exists(template_file):
        if template_name != "default":
            print(f"[警告] 模板文件 {template_file} 不存在，使用默认模板")
            return get_template("default")
        else:
            raise FileNotFoundError(f"默认模板文件 Template/default.json 不存在")
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            template = json.load(f)
        return template
    except Exception as e:
        print(f"[错误] 加载模板文件 {template_file} 失败: {e}")
        # 如果加载失败且不是默认模板，尝试加载默认模板
        if template_name != "default":
            return get_template("default")
        else:
            raise


def list_templates():
    """
    列出所有可用的模板（扫描Template文件夹）
    
    返回:
        list: 模板名称列表（不含.json扩展名）
    """
    template_dir = "Template"
    templates = []
    
    if not os.path.exists(template_dir):
        return templates
    
    try:
        for filename in os.listdir(template_dir):
            if filename.endswith('.json'):
                template_name = filename[:-5]  # 移除.json扩展名
                templates.append(template_name)
    except Exception as e:
        print(f"[错误] 扫描模板文件夹失败: {e}")
    
    return sorted(templates)

