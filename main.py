import sys
import os
import wave
import datetime

# 🌟 【核心修复】：强行让 PyTorch 第一个加载，霸占内存！
import torch 

# 然后导入我们的 AI 模块（它们内部也用到了 torch）
from vision.vision_engine import VisionEngine
from audio.asr_module import ModularInput
from audio.tts_module import ModularTTS
from llm.llm_module import ModularLLM

# 最后再导入 PyQt5 相关的模块
from PyQt5.QtWidgets import QApplication, QInputDialog 
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtMultimedia import QSound
from gui.main_window import MainWindow, ChatBubble
from gui.floating_window import FloatingWindow

# ==========================================
# ⚙️ 总控台：请在这里填入你训练好的权重路径！
# ==========================================
VISION_MODEL_PATH = 'models/visions/models_raw_trained_1111.pth' 
VISION_MODEL_TYPE = 'raw' 

class InteractionWorker(QThread):
    """
    交互工作线程：在后台处理 ASR -> LLM -> TTS 的耗时操作，绝对不卡 GUI
    """
    # 定义与 GUI 沟通的信号
    chat_append_signal = pyqtSignal(str, str)     # 发送者, 完整文本 (系统提示和用户输入)
    stream_start_signal = pyqtSignal(str, str)    # 发送者, 音频路径 (新建气泡并绑定语音)
    stream_char_signal = pyqtSignal(str)          # 单个字符 (追加到气泡)
    finished_signal = pyqtSignal()                # 交互完成，重新激活按钮
    
    # 🌟 新增：专门用于更新角色状态面板的信号 (action, expression, mood, thought)
    status_update_signal = pyqtSignal(str, str, str, str) 

    def __init__(self, mode, input_text, current_emotions, asr_engine, llm_engine, tts_engine):
        super().__init__()
        self.mode = mode                     
        self.input_text = input_text
        self.emotions = current_emotions     
        self.asr = asr_engine
        self.llm = llm_engine
        self.tts = tts_engine

    def run(self):
        try:
            # --- 1. 获取输入 (ASR 听觉) ---
            if self.mode == 'voice':
                self.chat_append_signal.emit("🎙️ 正在倾听... (请对麦克风说话)", "system")
                user_text = self.asr.get_voice_input()
                if not user_text:
                    self.chat_append_signal.emit("⚠️ 未检测到有效声音，交互取消。", "system")
                    self.finished_signal.emit()
                    return
            else:
                user_text = self.input_text
            
            # 显示用户输入
            self.chat_append_signal.emit(user_text, "user")

            # --- 2. 思考回复 (LLM 大脑) ---
            self.chat_append_signal.emit("🧠 正在思考...", "system")
            
            # 🌟 修改：接收 LLM 返回的 JSON 字典数据
            llm_response = self.llm.ask(user_text, self.emotions)
            
            # 🌟 新增：多模态数据解包
            if isinstance(llm_response, dict):
                spoken_text = llm_response.get("reply", "我好像有点短路了")
                action = llm_response.get("action", "待机")
                expression = llm_response.get("expression", "默认")
                mood = llm_response.get("mood", "平静")
                thought = llm_response.get("thought", "...")
            else:
                # 兜底防错：如果意外返回了纯文本
                spoken_text = str(llm_response)
                action, expression, mood, thought = "待机", "默认", "平静", "..."

            # 🌟 新增：立刻把状态发给 GUI，让面板先亮起来！
            self.status_update_signal.emit(action, expression, mood, thought)

            # --- 3. 生成声音 (TTS 嘴巴) ---
            self.chat_append_signal.emit("🎵 正在生成语音...", "system")
            
            audio_rep_dir = os.path.join(os.getcwd(), "audio", "chat_rep")
            os.makedirs(audio_rep_dir, exist_ok=True) 
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            wav_path = os.path.join(audio_rep_dir, f"rep_{timestamp}.wav")
            
            # 🌟 修改：这里只把纯文本的 spoken_text 交给 TTS，彻底告别 dict 报错！
            self.tts.speak(spoken_text, wav_path)

            # 生成完毕后，通知大脑回填这条记忆的音频路径
            self.llm.update_last_audio_path(wav_path)

            # --- 4. 视听同步输出 (计算打字速度) ---
            with wave.open(wav_path, 'rb') as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
            
            # 🌟 修改：以 spoken_text 的长度来计算打字延迟
            char_delay = duration / len(spoken_text) if len(spoken_text) > 0 else 0
            
            # 通知 GUI 新建一个 LLM 气泡，并透传音频路径
            self.stream_start_signal.emit("llm", wav_path)
            
            # 🌟 修改：按照音频节奏，逐字发送 spoken_text 给 GUI
            for char in spoken_text:
                self.stream_char_signal.emit(char)
                QThread.msleep(int(char_delay * 1000)) 

        except Exception as e:
            self.chat_append_signal.emit(f"❌ 交互发生错误: {e}", "system")
        
        finally:
            self.finished_signal.emit()


class UltimateApp(MainWindow):
    """
    终极应用管理器：继承自我们写好的 MainWindow，并在此基础上融合所有 AI 模块
    """
    def __init__(self):
        super().__init__()
        print("\n" + "="*50)
        print("🚀 正在预热所有 AI 引擎，请稍候...")
        print("="*50)
        
        # 1. 预热 AI 引擎
        self.asr_engine = ModularInput(use_voice=True, model_size="base")
        self.llm_engine = ModularLLM()
        self.tts_engine = ModularTTS()
        # 注意这里的名称，确保和你的 config.json 里对应
        self.tts_engine.setup_character("chengqianyu") 

        # 2. 状态存储
        self.latest_emotions = {"Neutral": 1.0} 
        self.current_stream_bubble = None       

        # 3. 启动后台视觉守护线程
        self.vision_thread = VisionEngine(model_type=VISION_MODEL_TYPE, model_path=VISION_MODEL_PATH)
        self.vision_thread.emotion_stats_ready.connect(self._update_internal_emotions)
        self.vision_thread.start()

        # 4. 启动左上角悬浮窗
        self.floating_monitor = FloatingWindow()
        self.vision_thread.frame_ready.connect(self.floating_monitor.update_frame)
        self.vision_thread.current_status_ready.connect(self.floating_monitor.update_status)
        self.vision_thread.emotion_stats_ready.connect(self.floating_monitor.update_stats)
        self.floating_monitor.show() 

        # 5. 绑定 GUI 交互事件
        self.btn_send.clicked.connect(self._on_send_text)
        self.btn_voice.clicked.connect(self._on_send_voice)
        self.input_box.return_pressed.connect(self._on_send_text)
        
        # 初始化频道 UI 并加载对应历史
        self._init_channel_ui()
        
        self.add_message("系统初始化完成！可以开始聊天啦~", sender="system")

    # ==========================================
    # 🌟 频道控制流
    # ==========================================
    def _init_channel_ui(self):
        """同步 LLM 里的频道到 UI 下拉框"""
        self.channel_selector.blockSignals(True) 
        self.channel_selector.clear()
        self.channel_selector.addItems(self.llm_engine.get_channels())
        self.channel_selector.setCurrentText(self.llm_engine.current_channel)
        self.channel_selector.blockSignals(False)
        
        self.channel_selector.currentTextChanged.connect(self._on_channel_changed)
        self.btn_new_channel.clicked.connect(self._on_new_channel)
        
        # 首次启动加载当前频道的历史记忆
        self._load_chat_history()

    def _on_channel_changed(self, channel_name):
        """用户在下拉框切换频道"""
        if channel_name:
            self.llm_engine.switch_channel(channel_name)
            self._load_chat_history()
            self.add_message(f"已切换至记忆频道：【{channel_name}】", sender="system")

    def _on_new_channel(self):
        """点击新建频道的弹窗操作"""
        text, ok = QInputDialog.getText(self, '新建频道', '请输入新的聊天频道名称:')
        if ok and text.strip():
            new_channel = text.strip()
            self.llm_engine.switch_channel(new_channel)
            self._init_channel_ui() 
            self.add_message(f"开启全新话题：【{new_channel}】", sender="system")

    def _load_chat_history(self):
        """核心解耦：物理清空当前界面，并重新渲染目标频道的历史聊天气泡"""
        # 1. 强行销毁布局内的所有旧气泡组件
        while self.chat_layout.count():
            child = self.chat_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # 2. 从 LLM 大脑拉取当前频道数据进行重绘
        history = self.llm_engine.history.get(self.llm_engine.current_channel, [])
        for i, msg in enumerate(history):
            self.add_message(msg["user"], "user")
            
            # 🌟 修复历史记录加载：处理 JSON 字典格式的历史数据
            reply_data = msg["return"]
            if isinstance(reply_data, dict):
                chat_text = reply_data.get("reply", "")
                
                # 如果是最后一条消息，顺便恢复一下状态面板的内容！
                if i == len(history) - 1:
                    self.update_character_status(
                        action=reply_data.get("action", ""),
                        expression=reply_data.get("expression", ""),
                        mood=reply_data.get("mood", ""),
                        thought=reply_data.get("thought", "")
                    )
            else:
                # 兼容老版本的纯字符串历史记录
                chat_text = str(reply_data)
                
            self.add_message(chat_text, "llm", audio_path=msg.get("audio_path"))
            
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    # ==========================================
    # 👆 UI 事件与 交互线程 的调度
    # ==========================================
    def _update_internal_emotions(self, stats_dict):
        self.latest_emotions = stats_dict

    def _on_send_text(self):
        text = self.input_box.toPlainText().strip()
        if not text:
            return
        self.input_box.clear()
        self._start_interaction(mode='text', input_text=text)

    def _on_send_voice(self):
        self._start_interaction(mode='voice', input_text="")

    def _start_interaction(self, mode, input_text):
        """冻结界面，触发后台交互线程"""
        self.btn_send.setEnabled(False)
        self.btn_voice.setEnabled(False)
        self.input_box.setEnabled(False)
        
        self.worker = InteractionWorker(
            mode=mode, 
            input_text=input_text, 
            current_emotions=self.latest_emotions,
            asr_engine=self.asr_engine,
            llm_engine=self.llm_engine,
            tts_engine=self.tts_engine
        )
        
        self.worker.chat_append_signal.connect(self.add_message)
        self.worker.stream_start_signal.connect(self._start_stream_bubble)
        self.worker.stream_char_signal.connect(self._append_stream_char)
        self.worker.finished_signal.connect(self._on_interaction_finished)
        
        # 🌟 新增：将线程发出的状态更新信号，连接到 MainWindow 预留的更新接口
        self.worker.status_update_signal.connect(self.update_character_status)
        
        self.worker.start()

    # ==========================================
    # 🖨️ 流式打字机效果实现
    # ==========================================
    def _start_stream_bubble(self, sender, audio_path):
        self.current_stream_bubble = ChatBubble("", sender, audio_path)
        self.chat_layout.addWidget(self.current_stream_bubble)
        
        if audio_path and os.path.exists(audio_path):
            QSound.play(audio_path)

    def _append_stream_char(self, char):
        if self.current_stream_bubble:
            current_text = self.current_stream_bubble.label.text()
            self.current_stream_bubble.label.setText(current_text + char)
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            )

    def _on_interaction_finished(self):
        self.btn_send.setEnabled(True)
        self.btn_voice.setEnabled(True)
        self.input_box.setEnabled(True)
        self.input_box.setFocus()

    def closeEvent(self, event):
        print("\n正在关闭系统，清理后台线程...")
        self.vision_thread.stop()
        self.floating_monitor.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_app = UltimateApp()
    main_app.show()
    sys.exit(app.exec_())