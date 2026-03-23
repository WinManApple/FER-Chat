import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QScrollArea, QLabel, QPushButton, QTextEdit, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtMultimedia import QSound

# ==========================================
# ⌨️ 自定义输入框组件 (现代化毛玻璃风格)
# ==========================================
class ChatInputBox(QTextEdit):
    return_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedHeight(70) # 稍微调高一点，增加呼吸感
        self.setPlaceholderText("想和可莉说什么呢... (Enter 发送，Shift+Enter 换行)")
        self.setFont(QFont("Microsoft YaHei", 11))
        # 现代化样式：半透明背景、圆角、柔和边框
        self.setStyleSheet("""
            QTextEdit {
                padding: 10px; 
                border: 1px solid rgba(255, 255, 255, 0.6); 
                border-radius: 12px; 
                background: rgba(255, 255, 255, 0.85);
                color: #333333;
            }
            QTextEdit:focus {
                border: 1px solid rgba(0, 170, 255, 0.8);
                background: rgba(255, 255, 255, 0.95);
            }
        """)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.return_pressed.emit()
                event.accept()
        else:
            super().keyPressEvent(event)


# ==========================================
# 💬 自定义富文本聊天气泡组件 (精美圆角排版)
# ==========================================
class ChatBubble(QWidget):
    def __init__(self, text, sender="user", audio_path=None):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5) # 增加气泡外部间距
        
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setFont(QFont("Microsoft YaHei", 11))
        
        # 限制气泡最大宽度，防止单行过长影响阅读体验
        self.label.setMaximumWidth(600) 
        
        if sender == "user":
            # 用户的气泡：柔和的薄荷绿，微透明
            self.label.setStyleSheet("""
                background-color: rgba(149, 236, 105, 0.9);
                border-radius: 12px;
                padding: 12px 16px;
                color: #111111;
            """)
            layout.addStretch()
            layout.addWidget(self.label)
            
        elif sender == "llm":
            # LLM的气泡：纯净的珍珠白，微透明
            self.label.setStyleSheet("""
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                padding: 12px 16px;
                color: #222222;
            """)
            layout.addWidget(self.label)
            
            # 语音播放按钮现代化
            if audio_path and os.path.exists(audio_path):
                self.btn_play = QPushButton("▶️")
                self.btn_play.setFixedSize(32, 32)
                self.btn_play.setCursor(QCursor(Qt.PointingHandCursor))
                self.btn_play.setStyleSheet("""
                    QPushButton {
                        border-radius: 16px; 
                        background-color: rgba(240, 240, 240, 0.8); 
                        font-size: 14px;
                        border: 1px solid rgba(200, 200, 200, 0.5);
                    }
                    QPushButton:hover { background-color: rgba(220, 220, 220, 1); }
                    QPushButton:pressed { background-color: rgba(200, 200, 200, 1); }
                """)
                self.audio_path = audio_path
                self.btn_play.clicked.connect(self._play_audio)
                layout.addWidget(self.btn_play)
                
            layout.addStretch()
            
        else:
            # System(系统提示)的气泡：胶囊样式，居中
            self.label.setStyleSheet("""
                background-color: rgba(0, 0, 0, 0.25);
                color: #FFFFFF; 
                font-size: 12px; 
                border-radius: 10px;
                padding: 4px 12px;
            """)
            self.label.setAlignment(Qt.AlignCenter)
            layout.addStretch()
            layout.addWidget(self.label)
            layout.addStretch()
            
        self.setLayout(layout)

    def _play_audio(self):
        if hasattr(self, 'audio_path'):
            QSound.play(self.audio_path)


# ==========================================
# 🖥️ 主聊天窗口布局 (宽屏视野 & 沉浸式 UI)
# ==========================================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("互动聊天室 - 终端连线系统")
        # 🌟 修改：扩大默认启动尺寸
        self.resize(1024, 768) 
        self.setMinimumSize(800, 600) # 设置最小尺寸限制
        
        self._set_background()
        self.init_ui()

    def _set_background(self):
        """完全弃用本地图片，使用纯代码(QSS)绘制现代感渐变背景"""
        # 强制顶级 QWidget 渲染 QSS 样式
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("MainChatWindow")
        
        # 使用线性渐变 (qlineargradient) 手搓深邃的“科技/工业”风格背景
        # 从左上角 (x1:0, y1:0) 到右下角 (x2:1, y2:1) 的平滑色带过渡
        self.setStyleSheet("""
            QWidget#MainChatWindow {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #0F2027,     /* 左上角：深空暗蓝 */
                    stop:0.5 #203A43,   /* 中间过渡：工业深青 */
                    stop:1 #2C5364      /* 右下角：终端灰蓝 */
                );
            }
        """)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20) # 增加全局外边距，避免贴边
        main_layout.setSpacing(15) # 增加组件间距
        
        # ==================================
        # 顶部：聊天频道控制区 (现代化玻璃面板)
        # ==================================
        top_layout = QHBoxLayout()
        
        channel_label = QLabel(" 频道节点:")
        channel_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        channel_label.setStyleSheet("""
            color: #333333; 
            background: rgba(255,255,255,0.8); 
            padding: 6px; 
            border-top-left-radius: 6px;
            border-bottom-left-radius: 6px;
        """)
        
        self.channel_selector = QComboBox()
        self.channel_selector.setCursor(QCursor(Qt.PointingHandCursor))
        self.channel_selector.setStyleSheet("""
            QComboBox {
                padding: 5px 10px; 
                font-family: 'Microsoft YaHei';
                font-weight: bold; 
                background: rgba(255,255,255,0.8);
                border: none;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                color: #333;
            }
            QComboBox::drop-down { border: none; }
        """)
        
        self.btn_new_channel = QPushButton("➕ 新建链路")
        self.btn_new_channel.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_new_channel.setStyleSheet("""
            QPushButton {
                padding: 6px 15px; 
                background-color: rgba(255, 153, 51, 0.9); 
                color: white; 
                border-radius: 6px; 
                font-family: 'Microsoft YaHei';
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover { background-color: rgba(255, 170, 80, 1); }
            QPushButton:pressed { background-color: rgba(230, 130, 30, 1); }
        """)
        
        top_layout.addWidget(channel_label)
        top_layout.addWidget(self.channel_selector)
        top_layout.addStretch() # 把新建按钮推到右边
        top_layout.addWidget(self.btn_new_channel)
        
        main_layout.addLayout(top_layout)
        
        # ==================================
        # 中部：聊天记录滚动区 (隐形滚动条)
        # ==================================
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # 🌟 重点：定制现代化的精细滚动条
        self.scroll_area.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QWidget#scroll_content { background: transparent; }
            
            QScrollBar:vertical {
                border: none;
                background: rgba(0, 0, 0, 0.05);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.2);
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 0, 0, 0.4);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px; 
            }
        """)
        
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scroll_content")
        self.chat_layout = QVBoxLayout(self.scroll_content)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(10) # 气泡之间的间距
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        
        # ==================================
        # 底部：输入与操作区 (平滑阴影交互)
        # ==================================
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)
        
        self.input_box = ChatInputBox()
        
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)
        
        self.btn_send = QPushButton("✉️ 发送消息")
        self.btn_send.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_send.setFixedHeight(35)
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 120, 215, 0.85); 
                color: white; 
                border-radius: 8px; 
                font-family: 'Microsoft YaHei';
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton:hover { background-color: rgba(0, 140, 240, 1); }
            QPushButton:pressed { background-color: rgba(0, 100, 190, 1); }
        """)
        
        self.btn_voice = QPushButton("🎤 语音输入")
        self.btn_voice.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_voice.setFixedHeight(35)
        self.btn_voice.setStyleSheet("""
            QPushButton {
                background-color: rgba(235, 80, 60, 0.85); 
                color: white; 
                border-radius: 8px; 
                font-family: 'Microsoft YaHei';
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton:hover { background-color: rgba(250, 100, 80, 1); }
            QPushButton:pressed { background-color: rgba(210, 60, 40, 1); }
        """)
        
        btn_layout.addWidget(self.btn_send)
        btn_layout.addWidget(self.btn_voice)
        
        bottom_layout.addWidget(self.input_box, stretch=1)
        bottom_layout.addLayout(btn_layout)
        
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def add_message(self, text, sender="user", audio_path=None):
        bubble = ChatBubble(text, sender, audio_path)
        self.chat_layout.addWidget(bubble)
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

# ==========================================
# 测试 UI
# ==========================================
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.add_message("系统初始化完成！可以开始聊天啦~", sender="system")
    window.add_message("千语，今天工业区的设备运转正常吗？", sender="user")
    window.add_message("一切正常哦管理员！刚才我还去检查了三号能源管线，没有任何问题。你要过来看看吗？", sender="llm", audio_path="fake_path.wav")
    
    window.show()
    sys.exit(app.exec_())