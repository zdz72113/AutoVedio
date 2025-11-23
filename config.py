"""
配置管理模块
从.env文件读取API密钥
"""
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


class Config:
    """配置类，管理所有API密钥"""
    
    # DeepSeek配置
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    
    # 火山引擎配置
    ARK_API_KEY = os.getenv('ARK_API_KEY', '')
    
    # 阿里云DashScope配置
    DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', '')
    
    # Azure语音服务配置
    AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY', '')
    AZURE_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION', '')
    AZURE_SPEECH_VOICE = os.getenv('AZURE_SPEECH_VOICE', 'zh-CN-XiaoxiaoNeural')  # 默认中文语音
    
    @classmethod
    def validate(cls):
        """验证必需的配置是否存在"""
        missing = []
        if not cls.DEEPSEEK_API_KEY:
            missing.append('DEEPSEEK_API_KEY')
        if not cls.ARK_API_KEY:
            missing.append('ARK_API_KEY')
        # Azure和DashScope至少需要一个
        if not cls.DASHSCOPE_API_KEY and not cls.AZURE_SPEECH_KEY:
            missing.append('DASHSCOPE_API_KEY 或 AZURE_SPEECH_KEY（至少需要一个）')
        if cls.AZURE_SPEECH_KEY and not cls.AZURE_SPEECH_REGION:
            missing.append('AZURE_SPEECH_REGION（使用Azure时需要）')
        
        if missing:
            raise ValueError(f"缺少必需的配置项: {', '.join(missing)}。请检查.env文件。")
        
        return True

