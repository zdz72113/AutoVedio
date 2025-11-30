# Azure Speech Service: https://learn.microsoft.com/azure/ai-services/speech-service/

import os
import azure.cognitiveservices.speech as speechsdk
from config import Config


def text_to_speech(text, output_file, voice_name=None):
    """
    使用Azure语音服务将文本转换为语音并保存到文件
    
    参数:
        text: 要转换的文本
        output_file: 输出的音频文件路径
        voice_name: 使用的语音名称，默认为配置中的AZURE_SPEECH_VOICE
    
    返回:
        output_file: 保存的音频文件路径
    """
    if not Config.AZURE_SPEECH_KEY or not Config.AZURE_SPEECH_REGION:
        raise ValueError("Azure语音服务配置不完整，请检查.env文件中的AZURE_SPEECH_KEY和AZURE_SPEECH_REGION")
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    
    # 配置Azure语音服务
    speech_config = speechsdk.SpeechConfig(
        subscription=Config.AZURE_SPEECH_KEY,
        region=Config.AZURE_SPEECH_REGION
    )
    
    # 设置语音名称
    if voice_name is None:
        voice_name = Config.AZURE_SPEECH_VOICE
    speech_config.speech_synthesis_voice_name = voice_name
    
    # 配置音频输出
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
    
    # 创建语音合成器
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config
    )
    
    # 执行语音合成
    result = synthesizer.speak_text_async(text).get()
    
    # 检查结果
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f'[Azure TTS] 音频已保存到: {output_file}')
        return output_file
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speechsdk.CancellationDetails(result)
        error_msg = f"语音合成被取消: {cancellation_details.reason}"
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            error_msg += f"\n错误详情: {cancellation_details.error_details}"
        raise Exception(error_msg)
    else:
        raise Exception(f"语音合成失败: {result.reason}")


def generate_audio_for_items(items, voice_name, audio_dir):
    """
    为items生成语音，基于subtitle字段
    
    参数:
        items: 项目列表，每个项目包含 subtitle 字段
        voice_name: 语音名称（从input配置中获取）
        audio_dir: 音频文件保存目录
    """
    for i, item in enumerate(items):
        # 如果已有audio，跳过
        if item.get('audio'):
            print(f"[语音生成] 第 {i+1}/{len(items)} 项已有音频，跳过")
            continue
        
        subtitle = item.get('subtitle', '') or ''
        
        if not subtitle:
            print(f"[警告] 第 {i+1} 项缺少subtitle，跳过语音生成")
            continue
        
        audio_file = os.path.join(audio_dir, f"audio_{i+1}.mp3")
        
        try:
            # 生成语音
            text_to_speech(subtitle, audio_file, voice_name=voice_name)
            item['audio'] = audio_file
            print(f"[语音生成] 第 {i+1}/{len(items)} 段语音已生成")
        except Exception as e:
            print(f"[错误] 生成第 {i+1} 段语音失败: {e}")
            continue


if __name__ == "__main__":
    # 测试代码
    text_to_speech("今天天气怎么样？", "output.mp3")
