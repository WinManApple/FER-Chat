import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QProgressBar
from PyQt5.QtCore import Qt, QPoint, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QFont

class FloatingWindow(QWidget):
    """
    左上角情绪监控悬浮窗
    功能：实时画面预览 + 当前情绪 + 2秒归一化情绪频率统计
    """
    def __init__(self):
        super().__init__()
        
        # 1. 设置窗口属性：无边框 + 窗口置顶
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground) # 支持透明度
        
        # 2. 窗口拖拽相关变量
        self.drag_position = QPoint()
        
        # 3. 初始化 UI
        self.init_ui()
        self.resize(280, 400) # 固定大小

    def init_ui(self):
        # 全局深色半透明背景样式
        self.main_container = QWidget(self)
        self.main_container.setObjectName("container")
        self.main_container.setStyleSheet("""
            QWidget#container {
                background-color: rgba(30, 30, 30, 200);
                border: 2px solid #555555;
                border-radius: 15px;
            }
            QLabel { color: #00FF00; font-family: 'Consolas'; }
        """)
        
        layout = QVBoxLayout(self.main_container)
        
        # --- A. 标题栏 (用于提示用户可拖动) ---
        title = QLabel("SYSTEM MONITOR - VISION")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Consolas", 9, QFont.Bold))
        layout.addWidget(title)

        # --- B. 实时画面预览区 ---
        self.video_label = QLabel("Waiting for Camera...")
        self.video_label.setFixedSize(240, 180)
        self.video_label.setStyleSheet("background-color: black; border-radius: 5px;")
        self.video_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.video_label, alignment=Qt.AlignCenter)

        # --- C. 当前状态区 ---
        status_layout = QHBoxLayout()
        self.emotion_label = QLabel("Emotion: ---")
        self.conf_label = QLabel("Conf: 0%")
        status_layout.addWidget(self.emotion_label)
        status_layout.addWidget(self.conf_label)
        layout.addLayout(status_layout)

        # --- D. 2秒情绪统计区 (雷达条) ---
        layout.addWidget(QLabel("2S EMOTION ANALYSIS:"))
        self.stat_bars = {}
        # 预设 7 种情绪的进度条
        emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']
        for emo in emotions:
            row = QHBoxLayout()
            name_label = QLabel(f"{emo[:3]}:")
            name_label.setFixedWidth(35)
            
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setFixedHeight(8)
            bar.setStyleSheet("""
                QProgressBar { background-color: #333; border-radius: 4px; }
                QProgressBar::chunk { background-color: #00AAFF; border-radius: 4px; }
            """)
            
            val_label = QLabel("0%")
            val_label.setFixedWidth(35)
            
            row.addWidget(name_label)
            row.addWidget(bar)
            row.addWidget(val_label)
            
            self.stat_bars[emo] = (bar, val_label)
            layout.addLayout(row)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.main_container)

    # ==========================================
    # 🖱️ 实现窗口自由拖拽逻辑
    # ==========================================
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    # ==========================================
    # 📥 信号槽：接收来自 VisionEngine 的数据
    # ==========================================
    @pyqtSlot(np.ndarray)
    def update_frame(self, frame):
        """更新监控画面"""
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(240, 180, Qt.KeepAspectRatio)
        self.video_label.setPixmap(QPixmap.fromImage(p))

    @pyqtSlot(str, float)
    def update_status(self, emotion, conf):
        """更新当前情绪文字"""
        self.emotion_label.setText(f"Emotion: {emotion}")
        self.conf_label.setText(f"Conf: {conf:.1f}%")

    @pyqtSlot(dict)
    def update_stats(self, stats_dict):
        """更新 2秒 频率统计条"""
        # stats_dict 格式如: {"Happy": 0.6, "Neutral": 0.4}
        for emo, (bar, label) in self.stat_bars.items():
            percentage = stats_dict.get(emo, 0) * 100
            bar.setValue(int(percentage))
            label.setText(f"{int(percentage)}%")

# ==========================================
# 测试代码
# ==========================================
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = FloatingWindow()
    win.show()
    sys.exit(app.exec_())