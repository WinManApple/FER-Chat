from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class CharacterStatusPanel(QFrame):
    """
    角色实时状态监控面板 (Cyber-HUD 风格)
    用于展示 LLM JSON 模式下生成的 action, expression, mood, thought
    """
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 面板全局样式：半透明深色玻璃，带微光边框
        self.setObjectName("StatusPanel")
        self.setStyleSheet("""
            QFrame#StatusPanel {
                background-color: rgba(10, 20, 30, 180);
                border: 1px solid rgba(0, 255, 255, 0.4);
                border-radius: 8px;
            }
        """)
        # 整体采用水平布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(20)

        # ==========================================
        # 左侧：物理与情绪状态区 (Badge 标签风格)
        # ==========================================
        status_layout = QVBoxLayout()
        status_layout.setSpacing(5)

        # 标题
        lbl_title = QLabel("⚡ SYNC STATUS")
        lbl_title.setFont(QFont("Consolas", 8, QFont.Bold))
        lbl_title.setStyleSheet("color: rgba(0, 255, 255, 0.7);")
        status_layout.addWidget(lbl_title)

        # 标签容器
        tags_layout = QHBoxLayout()
        tags_layout.setSpacing(8)

        # 初始化三个状态标签
        self.lbl_mood = self._create_badge("Mood", "待机")
        self.lbl_expr = self._create_badge("Expr", "默认")
        self.lbl_action = self._create_badge("Act", "静止")

        tags_layout.addWidget(self.lbl_mood)
        tags_layout.addWidget(self.lbl_expr)
        tags_layout.addWidget(self.lbl_action)
        tags_layout.addStretch()

        status_layout.addLayout(tags_layout)
        main_layout.addLayout(status_layout)

        # 添加一条垂直分割线
        vline = QFrame()
        vline.setFrameShape(QFrame.VLine)
        vline.setStyleSheet("color: rgba(0, 255, 255, 0.2);")
        main_layout.addWidget(vline)

        # ==========================================
        # 右侧：内心想法读取区 (Thought)
        # ==========================================
        thought_layout = QVBoxLayout()
        thought_layout.setSpacing(2)

        lbl_thought_title = QLabel("🧠 NEURAL THOUGHT INTERCEPT:")
        lbl_thought_title.setFont(QFont("Consolas", 8, QFont.Bold))
        lbl_thought_title.setStyleSheet("color: rgba(255, 153, 51, 0.8);") # 橙色警示感
        
        self.lbl_thought_content = QLabel("等待神经信号接入...")
        self.lbl_thought_content.setFont(QFont("Microsoft YaHei", 10))
        self.lbl_thought_content.setWordWrap(True)
        self.lbl_thought_content.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-style: italic;")

        thought_layout.addWidget(lbl_thought_title)
        thought_layout.addWidget(self.lbl_thought_content)
        
        # 让想法区占据更多空间
        main_layout.addLayout(thought_layout, stretch=1) 

    def _create_badge(self, prefix, default_text):
        """创建一个赛博风格的小标签"""
        lbl = QLabel(f"{prefix}: {default_text}")
        lbl.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        lbl.setStyleSheet("""
            background-color: rgba(0, 150, 255, 0.15);
            color: #00FFFF;
            border: 1px solid rgba(0, 255, 255, 0.3);
            border-radius: 4px;
            padding: 3px 8px;
        """)
        return lbl

    def update_status(self, action, expression, mood, thought):
        """
        供外部调用的更新接口，接收解析好的 JSON 字段
        """
        self.lbl_action.setText(f"Act: {action}")
        self.lbl_expr.setText(f"Expr: {expression}")
        self.lbl_mood.setText(f"Mood: {mood}")
        self.lbl_thought_content.setText(f"「 {thought} 」")

# ==========================================
# 独立测试模块
# ==========================================
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    # 创建一个黑色背景的窗口来测试效果
    test_win = QWidget()
    test_win.setStyleSheet("background-color: #111;")
    layout = QVBoxLayout(test_win)
    
    panel = CharacterStatusPanel()
    layout.addWidget(panel)
    
    # 模拟输入测试数据
    panel.update_status("兴奋地蹦跳", "眼睛放光", "超级开心", "哇！管理员居然主动找我聊天了，一定要好好表现！")
    
    test_win.resize(600, 150)
    test_win.show()
    sys.exit(app.exec_())