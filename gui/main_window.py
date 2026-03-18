import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QScrollArea, QLabel, QPushButton, QTextEdit, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtMultimedia import QSound

# ==========================================
# ⌨️ 自定义输入框组件 (接管键盘事件)
# ==========================================
class ChatInputBox(QTextEdit):
    # 定义自定义信号，当用户按下单独的 Enter 键时触发
    return_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedHeight(60) # 固定输入框高度
        self.setPlaceholderText("想和可莉说什么呢... (Enter 发送，Shift+Enter 换行)")
        self.setFont(QFont("Microsoft YaHei", 11))
        self.setStyleSheet("""
            padding: 8px; 
            border-radius: 5px; 
            background: rgba(255, 255, 255, 0.9);
        """)

    def keyPressEvent(self, event):
        """核心拦截逻辑：判断是换行还是发送"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() & Qt.ShiftModifier:
                # 组合键 Shift+Enter：调用父类原生方法，实现换行
                super().keyPressEvent(event)
            else:
                # 单独的 Enter：拦截默认换行行为，发射发送信号
                self.return_pressed.emit()
                event.accept()
        else:
            super().keyPressEvent(event)


# ==========================================
# 💬 自定义富文本聊天气泡组件 (支持语音播放)
# ==========================================
class ChatBubble(QWidget):
    def __init__(self, text, sender="user", audio_path=None):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 气泡的文字标签
        self.label = QLabel(text)
        self.label.setWordWrap(True) # 允许长文本自动换行
        self.label.setFont(QFont("Microsoft YaHei", 12))
        
        if sender == "user":
            # 用户的气泡：绿色，靠右对齐
            self.label.setStyleSheet("""
                background-color: #95EC69;
                border-radius: 10px;
                padding: 10px;
                color: black;
            """)
            layout.addStretch()         # 左边放弹簧，把气泡挤到右边
            layout.addWidget(self.label)
            
        elif sender == "llm":
            # LLM(可莉)的气泡：白色，靠左对齐
            self.label.setStyleSheet("""
                background-color: #FFFFFF;
                border-radius: 10px;
                padding: 10px;
                color: black;
            """)
            layout.addWidget(self.label)
            
            # 🌟 扩展功能：如果传入了语音路径且文件真实存在，则挂载播放按钮
            if audio_path and os.path.exists(audio_path):
                self.btn_play = QPushButton("▶️")
                self.btn_play.setFixedSize(36, 36)
                self.btn_play.setStyleSheet("""
                    border-radius: 18px; 
                    background-color: #E0E0E0; 
                    font-size: 16px;
                """)
                self.audio_path = audio_path
                self.btn_play.clicked.connect(self._play_audio)
                layout.addWidget(self.btn_play)
                
            layout.addStretch()         # 右边放弹簧，把气泡挤到左边
            
        else:
            # System(系统提示)的气泡：灰色，居中，无背景
            self.label.setStyleSheet("color: #AAAAAA; font-size: 14px; font-style: italic;")
            self.label.setAlignment(Qt.AlignCenter)
            layout.addStretch()
            layout.addWidget(self.label)
            layout.addStretch()
            
        self.setLayout(layout)

    def _play_audio(self):
        """点击按钮时播放绑定的独立语音"""
        if hasattr(self, 'audio_path'):
            QSound.play(self.audio_path)


# ==========================================
# 🖥️ 主聊天窗口布局
# ==========================================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("可莉的互动聊天室")
        self.resize(800, 600)
        
        # 1. 设置自适应的全局背景图
        self._set_background()
        
        # 2. 初始化核心 UI 布局
        self.init_ui()

    def _set_background(self):
        """加载背景图片并使用 StyleSheet 实现自适应拉伸"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        bg_path = os.path.join(root_dir, 'datasets', 'pictures', 'background.png')
        
        # 统一为 QSS 认识的正斜杠
        bg_path = bg_path.replace('\\', '/')
        
        # 强制顶级 QWidget 渲染 QSS 样式
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("MainChatWindow")
        
        # 给 url 加上单引号，防止路径内有空格导致解析失败
        self.setStyleSheet(f"""
            QWidget#MainChatWindow {{
                border-image: url('{bg_path}') 0 0 0 0 stretch stretch;
            }}
        """)

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # ==================================
        # 顶部：聊天频道控制区
        # ==================================
        top_layout = QHBoxLayout()
        
        channel_label = QLabel("当前记忆频道: ")
        channel_label.setStyleSheet("color: #333333; font-weight: bold; background: rgba(255,255,255,0.7); padding: 4px; border-radius: 4px;")
        
        self.channel_selector = QComboBox()
        self.channel_selector.setStyleSheet("padding: 5px; font-weight: bold; background-color: white;")
        
        self.btn_new_channel = QPushButton("➕ 新建频道")
        self.btn_new_channel.setStyleSheet("padding: 5px 10px; background-color: #FFA500; color: white; border-radius: 3px; font-weight: bold;")
        
        top_layout.addWidget(channel_label)
        top_layout.addWidget(self.channel_selector, 1) # 拉伸因子为1，填满剩余空间
        top_layout.addWidget(self.btn_new_channel)
        
        main_layout.addLayout(top_layout)
        
        # ==================================
        # 中部：聊天记录滚动区
        # ==================================
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # 将滚动区域本身和视口背景设置为全透明，透出后面的背景图
        self.scroll_area.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QWidget#scroll_content { background: transparent; }
        """)
        
        # 容纳所有气泡的容器
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scroll_content")
        self.chat_layout = QVBoxLayout(self.scroll_content)
        self.chat_layout.setAlignment(Qt.AlignTop) # 气泡从上往下排
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        
        # ==================================
        # 底部：输入与操作区 (引入模块化 InputBox)
        # ==================================
        bottom_layout = QHBoxLayout()
        
        self.input_box = ChatInputBox()
        
        btn_layout = QVBoxLayout()
        self.btn_send = QPushButton("发送文字")
        self.btn_send.setStyleSheet("padding: 8px; background-color: #0078D7; color: white; border-radius: 5px; font-weight: bold;")
        
        self.btn_voice = QPushButton("🎤 语音输入")
        self.btn_voice.setStyleSheet("padding: 8px; background-color: #F25022; color: white; border-radius: 5px; font-weight: bold;")
        
        btn_layout.addWidget(self.btn_send)
        btn_layout.addWidget(self.btn_voice)
        
        bottom_layout.addWidget(self.input_box, stretch=1)
        bottom_layout.addLayout(btn_layout)
        
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def add_message(self, text, sender="user", audio_path=None):
        """向聊天面板添加一条气泡消息，透传可选的音频路径"""
        bubble = ChatBubble(text, sender, audio_path)
        self.chat_layout.addWidget(bubble)
        
        # 自动滚动到最底部
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

# ==========================================
# 仅供测试 UI 效果使用
# ==========================================
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # 塞几条测试假数据进去看看效果
    window.add_message("可莉，你今天想去哪里玩呀？", sender="user")
    # 模拟一个带音频的气泡 (确保路径不存在时不会报错，而是单纯不显示播放按钮)
    window.add_message("想去星落湖炸鱼！主人要一起去吗？嘿嘿哒~", sender="llm", audio_path="fake_audio_path.wav")
    window.add_message("好呀，但是要注意别被琴团长发现了哦。", sender="user")
    
    window.show()
    sys.exit(app.exec_())