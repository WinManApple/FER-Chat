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
        self.setObjectName("StatusPanel")
        self.setStyleSheet("""
            QFrame#StatusPanel {
                background-color: rgba(10, 20, 30, 180);
                border: 1px solid rgba(0, 255, 255, 0.4);
                border-radius: 8px;
            }
        """)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(20)

        # ==========================================
        # 左侧：物理与情绪状态区 (改为纵向堆叠)
        # ==========================================
        status_layout = QVBoxLayout()
        status_layout.setSpacing(8)

        # 标题
        lbl_title = QLabel("⚡ SYNC STATUS")
        lbl_title.setFont(QFont("Consolas", 8, QFont.Bold))
        lbl_title.setStyleSheet("color: rgba(0, 255, 255, 0.7);")
        status_layout.addWidget(lbl_title)

        # 🌟 修改 1：将 QHBoxLayout 改为 QVBoxLayout，让三个标签竖着排
        tags_layout = QVBoxLayout()
        tags_layout.setSpacing(8)

        # 初始化三个状态标签
        self.lbl_mood = self._create_badge("Mood", "待机")
        self.lbl_expr = self._create_badge("Expr", "默认")
        self.lbl_action = self._create_badge("Act", "静止")

        tags_layout.addWidget(self.lbl_mood)
        tags_layout.addWidget(self.lbl_expr)
        tags_layout.addWidget(self.lbl_action)
        tags_layout.addStretch() # 把标签往上顶

        status_layout.addLayout(tags_layout)
        
        # 🌟 修改 2：给左侧布局设置 stretch=4，分配足够的宽度空间
        main_layout.addLayout(status_layout, stretch=4)

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
        lbl_thought_title.setStyleSheet("color: rgba(255, 153, 51, 0.8);") 
        
        self.lbl_thought_content = QLabel("等待神经信号接入...")
        self.lbl_thought_content.setFont(QFont("Microsoft YaHei", 10))
        self.lbl_thought_content.setWordWrap(True)
        self.lbl_thought_content.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.lbl_thought_content.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-style: italic;")

        thought_layout.addWidget(lbl_thought_title)
        thought_layout.addWidget(self.lbl_thought_content, stretch=1)
        
        # 🌟 修改 3：右侧分配 stretch=3 的比例
        main_layout.addLayout(thought_layout, stretch=3) 

    def _create_badge(self, prefix, default_text):
        """创建一个赛博风格的小标签"""
        lbl = QLabel(f"{prefix}: {default_text}")
        lbl.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        
        # 🌟 核心修改 4：开启标签文字的自动换行！！！
        lbl.setWordWrap(True) 
        
        lbl.setStyleSheet("""
            background-color: rgba(0, 150, 255, 0.15);
            color: #00FFFF;
            border: 1px solid rgba(0, 255, 255, 0.3);
            border-radius: 4px;
            padding: 6px 8px; /* 稍微增加一点内边距，让多行文字不拥挤 */
        """)
        return lbl

    def update_status(self, action, expression, mood, thought):
        self.lbl_action.setText(f"Act: {action}")
        self.lbl_expr.setText(f"Expr: {expression}")
        self.lbl_mood.setText(f"Mood: {mood}")
        self.lbl_thought_content.setText(f"「 {thought} 」")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    test_win = QWidget()
    test_win.setStyleSheet("background-color: #111;")
    layout = QVBoxLayout(test_win)
    panel = CharacterStatusPanel()
    layout.addWidget(panel)
    
    # 用极长的小作文测试换行效果
    panel.update_status(
        "兴奋地在原地转了两个圈，马尾辫在空中甩出一道弧线", 
        "眼睛睁得大大的，闪烁着充满好奇与期待的光芒", 
        "超级无敌开心且充满干劲", 
        "哇！管理员居然主动找我聊天了，一定要好好表现！绝对不能搞砸！"
    )
    
    test_win.resize(800, 200)
    test_win.show()
    sys.exit(app.exec_())