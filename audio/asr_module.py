import os
import shutil
import atexit
import traceback
import speech_recognition as sr
from faster_whisper import WhisperModel

class ModularInput:
    """模块化输入引擎：支持键盘文本输入 & 麦克风语音识别"""
    
    def __init__(self, use_voice=True, model_size="base"):
        self.use_voice = use_voice
        
        # 🌟 修改 1：定义独立的临时文件夹和文件路径
        self.temp_dir = "user_input_tem"
        self.temp_audio_file = os.path.join(self.temp_dir, "temp_record.wav")
        
        # 确保初始化时文件夹存在
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # 🌟 修改 2：向 Python 解释器注册“临终遗言”（清理函数）
        # 无论程序是正常运行结束，还是因为报错崩溃，atexit 都会尽量保证在解释器关闭前执行此函数
        atexit.register(self._cleanup_temp_files)
        
        if self.use_voice:
            print(f"[System] 正在加载 Faster-Whisper ({model_size}) 语音识别模型...")
            try:
                self.asr_model = WhisperModel(model_size, device="auto", compute_type="default")
                self.recognizer = sr.Recognizer()
                print("[System] 🎤 麦克风与语音识别模型就绪！")
            except Exception as e:
                print(f"[ASR Fatal Init Error] 模型初始化失败！报错: {e}")
                traceback.print_exc()

    def _cleanup_temp_files(self):
        """🌟 核心清理逻辑：强制删除整个临时文件夹及内部的音频"""
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                print(f"\n[System] 🧹 战场打扫完毕：已清理临时语音录音文件夹 '{self.temp_dir}'")
            except Exception as e:
                print(f"\n[Warning] ⚠️ 无法清理临时文件夹，可能文件正被占用: {e}")

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

        print("\n[DEBUG-ASR 🛠️] 1. 准备调用系统麦克风资源 (sr.Microphone)...")
        try:
            with sr.Microphone() as source:
                print("[DEBUG-ASR 🛠️] 2. 麦克风成功打开！准备自适应环境底噪...")
                print("\n" + "="*40)
                print("🎛️ 正在适应环境底噪，请稍等...")
                
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                print("[DEBUG-ASR 🛠️] 3. 底噪自适应完毕！准备开启录音监听...")
                print("🎙️ 正在听！请说话 (不说话会自动停止录音)...")
                
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=15)
                    print("[DEBUG-ASR 🛠️] 4. 录音阶段结束！成功拿到声音数据，准备写入硬盘...")
                    
                    # 🌟 防御性编程：每次写入前再次确认文件夹还在（防止运行中途被用户手动删了）
                    os.makedirs(self.temp_dir, exist_ok=True)
                    
                    # 存入专属的 user_input_tem/ 目录下
                    with open(self.temp_audio_file, "wb") as f:
                        f.write(audio.get_wav_data())
                    print(f"[DEBUG-ASR 🛠️] 5. 临时音频文件写入成功，交由 Whisper 模型识别...")
                    
                    print("⏳ 正在识别...")
                    segments, info = self.asr_model.transcribe(self.temp_audio_file, beam_size=5, language="zh")
                    print("[DEBUG-ASR 🛠️] 6. Whisper 推理完成！准备解析文本内容...")
                    
                    recognized_text = "".join([segment.text for segment in segments])
                    print(f"🗣️ 识别结果: '{recognized_text}'")
                    print("[DEBUG-ASR 🛠️] 7. 语音识别模块安全退出，将返回文字。")
                    
                    return recognized_text.strip()
                    
                except sr.WaitTimeoutError:
                    print("⚠️ 等太久啦，没听到声音呢。")
                    return ""
                except Exception as e:
                    print(f"[ASR Error] 🚨 录音或识别阶段遭遇异常！")
                    print(f"异常详情: {e}")
                    traceback.print_exc()
                    return ""
                    
        except OSError as e:
            print(f"[ASR FATAL 🚨] 无法连接到麦克风设备，可能是 PyAudio 驱动异常或无默认麦克风！")
            print(f"异常详情: {e}")
            traceback.print_exc()
            return ""
        except Exception as e:
            print(f"[ASR FATAL 🚨] 未知致命错误发生在打开麦克风时！")
            print(f"异常详情: {e}")
            traceback.print_exc()
            return ""

    def get_user_input(self, mode="text"):
        if mode == "voice":
            return self.get_voice_input()
        else:
            return self.get_text_input()

# ==========================================
# 独立测试排查入口
# ==========================================
if __name__ == "__main__":
    print("========================================")
    print("🔍 麦克风带清理机制测试启动！")
    print("========================================")
    
    input_engine = ModularInput(use_voice=True, model_size="base")
    print("\n--- 准备进行第一次语音测试 ---")
    text = input_engine.get_voice_input()
    print(f"✅ 最终返回的文本: {text}")
    print("\n[System] 主程序逻辑执行完毕，准备退出，请观察下方是否出现清扫提示...")