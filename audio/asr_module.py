import os
import speech_recognition as sr
from faster_whisper import WhisperModel

class ModularInput:
    """模块化输入引擎：支持键盘文本输入 & 麦克风语音识别"""
    
    def __init__(self, use_voice=True, model_size="base"):
        """
        :param use_voice: 是否开启语音识别功能
        :param model_size: whisper模型大小 ("tiny", "base", "small")。"base"性价比最高。
        """
        self.use_voice = use_voice
        self.temp_audio_file = "temp_record.wav"
        
        if self.use_voice:
            print(f"[System] 正在加载 Faster-Whisper ({model_size}) 语音识别模型...")
            # device="auto" 会自动寻找 GPU，找不到就用 CPU
            # compute_type="default" 保证最高兼容性
            self.asr_model = WhisperModel(model_size, device="auto", compute_type="default")
            self.recognizer = sr.Recognizer()
            print("[System] 🎤 麦克风与语音识别模块就绪！")

    def get_text_input(self):
        """纯文本打字输入方法"""
        print("\n" + "="*40)
        user_text = input("✍️ 请输入你想对可莉说的话 (输入 'q' 退出): ")
        return user_text.strip()

    def get_voice_input(self):
        """麦克风录音并识别为文本的方法"""
        if not self.use_voice:
            print("[Error] 语音模块未开启，请在初始化时设置 use_voice=True")
            return ""

        with sr.Microphone() as source:
            print("\n" + "="*40)
            print("🎛️ 正在适应环境底噪，请稍等...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            print("🎙️ 可莉正在听！请说话 (不说话会自动停止录音)...")
            
            try:
                # listen 会自动检测你是不是说完了（停顿超过0.8秒自动结束）
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                
                # 将录音保存为临时 wav 文件
                with open(self.temp_audio_file, "wb") as f:
                    f.write(audio.get_wav_data())
                
                print("⏳ 正在识别...")
                # 调用 faster-whisper 进行极速识别
                segments, info = self.asr_model.transcribe(self.temp_audio_file, beam_size=5, language="zh")
                
                # 拼接识别结果
                recognized_text = "".join([segment.text for segment in segments])
                print(f"🗣️ 识别结果: '{recognized_text}'")
                
                return recognized_text.strip()
                
            except sr.WaitTimeoutError:
                print("⚠️ 等太久啦，没听到声音呢。")
                return ""
            except Exception as e:
                print(f"[ASR Error] 识别出错了: {e}")
                return ""

    def get_user_input(self, mode="text"):
        """
        统一接口：根据 mode 决定是用键盘还是用麦克风
        :param mode: "text" 或 "voice"
        """
        if mode == "voice":
            return self.get_voice_input()
        else:
            return self.get_text_input()

# ==========================================
# 交互测试区
# ==========================================
if __name__ == "__main__":
    # 测试模式，你可以把 use_voice 改成 False 试试纯打字
    input_engine = ModularInput(use_voice=True, model_size="base")
    
    # 你可以更改这里为 "text" 来测试纯打字输入
    test_mode = "voice" 
    
    while True:
        text = input_engine.get_user_input(mode=test_mode)
        
        if text.lower() == 'q':
            print("👋 退出输入测试。")
            break
            
        if text:
            print(f"✅ 成功获取到输入内容: {text}")