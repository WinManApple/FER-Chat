import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QProgressBar, QFrame
from PyQt5.QtCore import Qt, QPoint, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor

class FloatingWindow(QWidget):
    """
    左上角情绪监控悬浮窗 - 爆改为现代化 Cyber-HUD 风格
    """
    def __init__(self):
        super().__init__()
        
        # 1. 设置窗口属性：无边框 + 窗口置顶 + Tool属性(不在任务栏显示)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground) # 必须开启透明度支持
        
        # 2. 窗口拖拽相关变量
        self.drag_position = QPoint()
        
        # 3. 初始化 UI
        self.init_ui()
        # 🌟 修改：适当微调尺寸，让布局更有呼吸感
        self.resize(320, 450)

    def init_ui(self):
        # 🌟 全面爆改 QSS 全局样式 (毛玻璃质感 & 科幻青配色)
        self.main_container = QWidget(self)
        self.main_container.setObjectName("container")
        self.main_container.setStyleSheet("""
            QWidget#container {
                /* 深色半透明背景，比MainWindow深一些，突出悬浮感 */
                background-color: rgba(10, 15, 20, 190); 
                /* 极细的、带有微光的亮青色边框 */
                border: 1px solid rgba(0, 255, 255, 0.3); 
                border-radius: 12px;
            }
            /* 全局文字：现代科幻青色，柔和不刺眼 */
            QLabel { 
                color: rgba(0, 255, 255, 0.9); 
                font-family: 'Microsoft YaHei'; 
            }
            /* 数据类文字：保持 Monospace 增加专业监控感 */
            QLabel#ValueLabel {
                font-family: 'Consolas', monospace;
                font-weight: bold;
                color: #FFFFFF;
            }
        """)
        
        layout = QVBoxLayout(self.main_container)
        layout.setContentsMargins(15, 12, 15, 15) # 调整内边距
        layout.setSpacing(10) # 调整组件间距
        
        # --- A. 标题栏 (用于提示用户可拖动，居中且现代) ---
        title = QLabel("👁️ SYSTEM VISION HUD")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        # 标题栏下方加一条极淡的分隔线
        title_line = QFrame()
        title_line.setFrameShape(QFrame.HLine)
        title_line.setFrameShadow(QFrame.Plain)
        title_line.setStyleSheet("background-color: rgba(0, 255, 255, 0.15); max-height: 1px;")
        
        layout.addWidget(title)
        layout.addWidget(title_line)

        # --- B. 实时画面预览区 (精致圆角嵌入) ---
        self.video_label = QLabel("Camera Offline")
        self.video_label.setFixedSize(240, 180)
        # 去掉原本死板的纯黑，改用极深青色，加上圆角和微光边框
        self.video_label.setStyleSheet("""
            background-color: rgba(0, 5, 10, 1); 
            border-radius: 6px; 
            border: 1px solid rgba(0, 255, 255, 0.1);
            color: rgba(0, 255, 255, 0.4);
        """)
        self.video_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.video_label, alignment=Qt.AlignCenter)

        # --- C. 当前状态区 (水平整齐排列，数据亮白) ---
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame { background: rgba(0, 0, 0, 0.2); border-radius: 4px; padding: 2px; }
            QLabel { background: transparent; }
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(5, 2, 5, 2)
        
        emo_tag = QLabel("Emotion:")
        self.emotion_label = QLabel("---")
        self.emotion_label.setObjectName("ValueLabel")
        
        conf_tag = QLabel("Conf:")
        self.conf_label = QLabel("0%")
        self.conf_label.setObjectName("ValueLabel")
        
        status_layout.addWidget(emo_tag)
        status_layout.addWidget(self.emotion_label)
        status_layout.addStretch() # 中间放弹簧，推开两边
        status_layout.addWidget(conf_tag)
        status_layout.addWidget(self.conf_label)
        
        layout.addWidget(status_frame)

        # --- D. 2秒情绪统计区 (雷达条爆改) ---
        stats_header = QLabel("2S EMOTION ANALYSIS")
        stats_header.setFont(QFont("Microsoft YaHei", 8, QFont.Bold))
        stats_header.setStyleSheet("color: rgba(255, 255, 255, 0.6); margin-top: 5px;")
        layout.addWidget(stats_header)
        
        self.stat_bars = {}
        # 预设 7 种情绪
        emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']
        
        # 为统计区创建一个容器
        stats_container = QWidget()
        stats_layout = QVBoxLayout(stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(6)
        
        for emo in emotions:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            
            # 🌟 修改 1：情绪名称标签的宽度从 40 增加到 45
            name_label = QLabel(f"{emo[:3].upper()}:")
            name_label.setFont(QFont("Consolas", 9))
            name_label.setFixedWidth(45) 
            
            # 🌟 核心：爆改进度条为极细渐变科技感样式 (这部分代码保持不变)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setFixedHeight(6) # 极细
            bar.setStyleSheet("""
                QProgressBar { 
                    background-color: rgba(255, 255, 255, 0.05); /* 淡灰色底轨道 */
                    border-radius: 3px; 
                    border: none;
                }
                QProgressBar::chunk { 
                    border-radius: 3px; 
                    /* 赛博风格渐变：深蓝 -> 亮青 */
                    background-color: qlineargradient(spread:pad, x1:0, y1:0.5, x2:1, y2:0.5, 
                        stop:0 rgba(0, 51, 102, 255), 
                        stop:1 rgba(0, 255, 255, 255));
                }
            """)
            
            # 🌟 修改 2：频率数值的宽度从 35 增加到 45，确保 100% 能完全显示
            val_label = QLabel("0%")
            val_label.setObjectName("ValueLabel")
            val_label.setFont(QFont("Consolas", 9, QFont.Bold))
            val_label.setFixedWidth(45) 
            val_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            row.addWidget(name_label)
            row.addWidget(bar, stretch=1) # 进度条拉伸
            row.addWidget(val_label)
            
            self.stat_bars[emo] = (bar, val_label)
            stats_layout.addLayout(row)
            
        layout.addWidget(stats_container)

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().addWidget(self.main_container)

    # ==========================================
    # 🖱️ 实现窗口自由拖拽逻辑 (保持不变)
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
    # 📥 信号槽：逻辑保持不变，确保功能一致
    # ==========================================
    @pyqtSlot(np.ndarray)
    def update_frame(self, frame):
        """更新监控画面"""
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        # 🌟 修改：使用 KeepAspectRatioByExpanding 或 SmoothTransformation 稍微优化显示质量
        p = convert_to_Qt_format.scaled(240, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(QPixmap.fromImage(p))

    @pyqtSlot(str, float)
    def update_status(self, emotion, conf):
        """更新当前情绪文字"""
        # 🌟 优化：情緒文字统一大写，增加科技感
        self.emotion_label.setText(emotion.upper())
        self.conf_label.setText(f"{conf:.1f}%")

    @pyqtSlot(dict)
    def update_stats(self, stats_dict):
        """更新 2秒 频率统计条"""
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
    win.video_label.setText("[ TEST MODE ]")
    win.show()
    # 移动到屏幕左上角方便查看
    win.move(50, 50) 
    sys.exit(app.exec_())