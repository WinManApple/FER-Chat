import os
import sys
import json
import numpy as np
import soundfile as sf

# 强制禁用垃圾 GPU，全程使用 CPU 推理
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

class ModularTTS:
    """模块化 TTS 引擎，完全解耦调用逻辑与底层框架"""
    
    def __init__(self):
        # 获取当前 audio 目录和项目根目录
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(self.current_dir)
        
        # 定位底层的 GPT-SoVITS 框架目录
        self.gpt_sovits_root = os.path.join(self.base_dir, "GPT-SoVITS")
        self.gpt_sovits_inner = os.path.join(self.gpt_sovits_root, "GPT_SoVITS")
        
        print("[System] 正在挂载 TTS 底层环境...")
        # 1. 注入绝对路径，解决导入冲突
        if self.gpt_sovits_inner not in sys.path:
            sys.path.insert(0, self.gpt_sovits_inner)
        if self.gpt_sovits_root not in sys.path:
            sys.path.insert(0, self.gpt_sovits_root)
            
    def setup_character(self, char_name):
        """配置并加载特定角色的声线 (从 config.json 动态读取)"""
        print(f"\n[System] 正在初始化 {char_name} 的模型 (CPU加载可能需要几秒钟)...")
        
        # 2. 动态读取外部配置文件，保护隐私并方便开源
        config_path = os.path.join(self.current_dir, "config.json")
        
        if not os.path.exists(config_path):
            print(f"❌ [TTS Error] 找不到配置文件！")
            print(f"请在 {self.current_dir} 目录下创建 config.json，并配置角色模型路径。")
            sys.exit(1)
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            print(f"❌ [TTS Error] 解析 config.json 失败: {e}")
            sys.exit(1)
            
        # 3. 提取对应角色的配置信息
        char_config = config.get("characters", {}).get(char_name)
        if not char_config:
            raise ValueError(f"❌ config.json 中未找到角色 [{char_name}] 的配置项！")

        # 将相对路径转换为基于项目根目录的绝对路径
        gpt_path = os.path.join(self.base_dir, char_config["gpt_model_path"])
        sovits_path = os.path.join(self.base_dir, char_config["sovits_model_path"])
        
        self.ref_audio = os.path.join(self.base_dir, char_config["ref_audio_path"])
        self.ref_text = char_config["ref_text"]
        self.ref_lang = char_config["ref_lang"]

        # 4. 核心魔法：在导入前，通过环境变量把路径塞给 WebUI，防止它启动时去读空字符串崩溃
        os.environ["gpt_path"] = gpt_path
        os.environ["sovits_path"] = sovits_path

        # 5. 强行切入框架目录，导入 API
        original_cwd = os.getcwd()
        os.chdir(self.gpt_sovits_root)
        
        try:
            from GPT_SoVITS.inference_webui import get_tts_wav, change_gpt_weights, change_sovits_weights
            
            # 6. 确保权重被正确切换
            change_gpt_weights(gpt_path)
            change_sovits_weights(sovits_path)
            self.get_tts_wav = get_tts_wav
            print(f"[System] {char_name} 声带接入完毕！")
            
        except ImportError as e:
            print(f"❌ [TTS Error] 导入 GPT-SoVITS 核心模块失败。请确保 GPT-SoVITS 已正确下载到根目录！\n错误信息: {e}")
            sys.exit(1)
        finally:
            # 7. 必定切回原工作目录
            os.chdir(original_cwd)


    def speak(self, text, output_filename="output.wav"):
        """对外暴露的极简生成接口"""
        print(f"\n[TTS] 准备生成语句: '{text}'")
        
        # 【核心修复 1】：将输出路径转换为绝对路径
        output_abs_path = os.path.abspath(output_filename)
        
        # 【核心修复 2】：记住主程序目录，然后强行跳入底层框架的“沙盒”目录
        original_cwd = os.getcwd()
        os.chdir(self.gpt_sovits_root)
        
        try:
            # 调用底层生成器
            generator = self.get_tts_wav(
                ref_wav_path=self.ref_audio, 
                prompt_text=self.ref_text, 
                prompt_language=self.ref_lang, 
                text=text, 
                text_language="中文" # 目标语言是中文
            )
            
            audio_data = []
            sample_rate = 32000
            
            # 逐步拉取生成的音频块
            for chunk in generator:
                sr, audio_chunk = chunk
                sample_rate = sr
                audio_data.append(audio_chunk)
                
            if audio_data:
                # 拼接所有块
                audio_concat = np.concatenate(audio_data, axis=0)
                
                # ==========================================
                # 🌟 核心修复：生成 0.8 秒的绝对静音垫片，防止蓝牙吞字
                # ==========================================
                silence_duration = 0.8  # 垫入 0.8 秒
                silence_samples = int(sample_rate * silence_duration)
                # 生成与原音频数据类型一致的全 0 数组
                silence_array = np.zeros(silence_samples, dtype=audio_concat.dtype)
                
                # 将静音拼接到真实语音的最前面！
                audio_concat = np.concatenate([silence_array, audio_concat], axis=0)
                # ==========================================

                # 使用绝对路径保存，确保音频文件回到你的工作目录
                sf.write(output_abs_path, audio_concat, sample_rate)
                print(f"[Success] 🎉 语音已保存至: {output_abs_path}")
            else:
                print("[Error] 生成失败，没有返回音频数据。")
                
        except Exception as e:
            print(f"[Error] 推理过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # 【核心修复 3】：无论成功还是报错，最后必定切回主工程目录，实现完美隔离！
            os.chdir(original_cwd)

# ==========================================
# 交互测试区
# ==========================================
if __name__ == "__main__":
    # 1. 实例化我们的模块化引擎
    tts_engine = ModularTTS()
    
    # 2. 切换为可莉的声线
    try:
        tts_engine.setup_character("chengqianyu")
        # 3. 输入你想要她说的台词
        target_text = "管理员你好！我是小陈～今天超开心能当你的向导！来来来，让我们一起测试情绪识别模块吧！"
        # 4. 执行生成
        tts_engine.speak(target_text, output_filename="chengqianyu_test.wav")
    except Exception as e:
        print(e)