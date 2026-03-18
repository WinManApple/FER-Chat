import os
import json
import time
from openai import OpenAI
import sys

# 尝试导入提示词 (兼容直接运行和被主程序调用两种路径情况)
try:
    from .prompt import SYSTEM_PROMPT
except ImportError:
    from prompt import SYSTEM_PROMPT

# ==========================================
# ⚙️ LLM 配置总控台 (动态读取 config.json)
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR, "config.json")

# 检查并加载配置
if not os.path.exists(CONFIG_PATH):
    print(f"❌ [LLM Error] 找不到配置文件！请在 {CURRENT_DIR} 目录下创建 config.json。")
    print("格式参考: {\"API_KEY\": \"...\", \"BASE_URL\": \"...\", \"MODEL_NAME\": \"...\"}")
    sys.exit(1)

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config_data = json.load(f)

API_KEY = config_data.get("API_KEY")
BASE_URL = config_data.get("BASE_URL")
MODEL_NAME = config_data.get("MODEL_NAME") 

# 记忆存储设置 (使用绝对路径实现彻底解耦)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CHAT_DATA_DIR = os.path.join(CURRENT_DIR, "chat_data")
CHAT_DATA_FILE = os.path.join(CHAT_DATA_DIR, "chat_data.json")

class ModularLLM:
    """模块化 LLM 引擎，支持情绪感知、多频道隔离与持久化记忆"""
    
    def __init__(self):
        # 1. 初始化客户端
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        
        # 2. 确保存储目录存在
        if not os.path.exists(CHAT_DATA_DIR):
            os.makedirs(CHAT_DATA_DIR)
            
        # 3. 初始化多频道状态与加载历史记忆
        self.current_channel = "默认频道"
        self.history = self._load_history()

    def _load_history(self):
        """从 JSON 文件加载历史对话，自动兼容旧版的单列表数据结构"""
        if os.path.exists(CHAT_DATA_FILE):
            try:
                with open(CHAT_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 【数据结构升级兼容】如果读出来是旧版的 list，自动装进 dict 里
                    if isinstance(data, list):
                        return {self.current_channel: data}
                    return data
            except Exception as e:
                print(f"[LLM Error] 加载记忆文件失败: {e}")
                return {self.current_channel: []}
        return {self.current_channel: []}

    def _save_to_json(self, user_text, emotion_data, llm_reply, audio_path=None):
        """将当前频道的对话持久化到 JSON 文件"""
        new_entry = {
            "user": user_text,
            "emotion": emotion_data,
            "return": llm_reply,
            "audio_path": audio_path, # 🌟 绑定生成的语音路径
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S") 
        }
        
        if self.current_channel not in self.history:
            self.history[self.current_channel] = []
            
        self.history[self.current_channel].append(new_entry)
        
        self._write_disk()

    def update_last_audio_path(self, audio_path):
        """当 TTS 模块生成完语音后，回填更新最新一条记忆的音频路径"""
        if self.current_channel in self.history and self.history[self.current_channel]:
            self.history[self.current_channel][-1]["audio_path"] = audio_path
            self._write_disk()

    def _write_disk(self):
        """统一下盘写入方法"""
        try:
            with open(CHAT_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[LLM Error] 写入记忆文件失败: {e}")

    def get_channels(self):
        """获取所有已有的频道名称"""
        return list(self.history.keys())

    def switch_channel(self, channel_name):
        """切换到指定频道，如果没有则初始化为空"""
        self.current_channel = channel_name
        if channel_name not in self.history:
            self.history[channel_name] = []

    def _format_context(self):
        """将【当前频道】的历史记忆转换为 OpenAI 格式的上下文"""
        context = [{"role": "system", "content": SYSTEM_PROMPT}]
        channel_history = self.history.get(self.current_channel, [])
        
        # 截取最近 5 轮对话防止上下文过载
        for entry in channel_history[-5:]:
            context.append({"role": "user", "content": entry["user"]})
            context.append({"role": "assistant", "content": entry["return"]})
        return context

    def ask(self, text, emotion_data):
        """核心请求接口"""
        print(f"\n[LLM] 频道: {self.current_channel} | 收到输入: '{text}' | 当前情绪: {emotion_data}")
        
        # 1. 构造增强型 Prompt (注入情绪)
        emotion_str = ", ".join([f"{k}:{v}" for k, v in emotion_data.items()])
        full_user_input = f"【主人当前情绪成分: {emotion_str}】\n用户的输入: {text}"
        
        # 2. 获取包含历史的上下文
        messages = self._format_context()
        messages.append({"role": "user", "content": full_user_input})
        
        try:
            # 3. 调用 API
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.7 
            )
            
            reply = response.choices[0].message.content
            
            # 4. 持久化保存 (此时音频还没生成，传 None，稍后由主线程调用 update_last_audio_path 回填)
            self._save_to_json(text, emotion_data, reply, audio_path=None)
            
            return reply

        except Exception as e:
            error_msg = f"哎呀，大脑出错了哒！错误信息：{e}"
            print(f"[LLM Error] API 请求失败: {e}")
            return error_msg

# ==========================================
# 交互测试区
# ==========================================
if __name__ == "__main__":
    llm = ModularLLM()
    
    # 测试频道切换功能
    print(f"当前存在的频道: {llm.get_channels()}")
    llm.switch_channel("测试频道_01")
    
    test_emotion = {"sad": "85%", "neutral": "10%"} 
    test_text = "可莉，我今天感觉有点累..."
    
    response = llm.ask(test_text, test_emotion)
    print(f"\n[当前频道 - {llm.current_channel}] 可莉的回应: {response}")
    
    # 模拟生成了语音并回填
    llm.update_last_audio_path("mock/path/to/audio.wav")
    print("\n✅ 测试完成，你可以检查 chat_data.json 看是否生成了多频道字典结构。")