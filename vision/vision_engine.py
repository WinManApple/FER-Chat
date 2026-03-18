import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms, models
from PIL import Image
import numpy as np
from collections import deque
from PyQt5.QtCore import QThread, pyqtSignal

# 从同级目录导入基础版 CNN 大脑
from .model import FaceEmotionCNN

class VisionEngine(QThread):
    # ==========================================
    # 📡 定义通讯信号 (这是 QThread 与 GUI 沟通的唯一合法桥梁)
    # ==========================================
    # 信号1：向 GUI 发送处理好的画面 (格式为 numpy 数组)
    frame_ready = pyqtSignal(np.ndarray) 
    
    # 信号2：向 GUI 和 LLM 发送 2秒内的情绪统计百分比 (格式为字典)
    # 例如：{"Sad (悲伤)": 0.8, "Neutral (中性)": 0.2}
    emotion_stats_ready = pyqtSignal(dict)
    
    # 信号3：向 GUI 小弹窗发送当前瞬间的识别状态 (情绪文本, 置信度)
    current_status_ready = pyqtSignal(str, float)

    def __init__(self, model_type='resnet', model_path=''):
        super().__init__()
        self.running = True # 线程运行标志位
        self.device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        print(f"[Vision] 后台视觉引擎初始化中，使用设备: {self.device}")

        # --- 情绪标签 ---
        self.emotion_dict = {
            0: 'Angry', 1: 'Disgust', 2: 'Fear', 3: 'Happy', 
            4: 'Neutral', 5: 'Sad', 6: 'Surprise'
        }

        # --- 维护 2秒 情绪历史队列 ---
        # 假设摄像头处理速度约为 10 FPS，2 秒就是 20 帧
        self.emotion_queue = deque(maxlen=20)

        # --- 自动装配大脑 ---
        if model_type == 'raw':
            self.model = FaceEmotionCNN(num_classes=7)
            self.transform = transforms.Compose([
                transforms.Grayscale(num_output_channels=1),
                transforms.Resize((48, 48)),
                transforms.ToTensor(),
                transforms.Normalize((0.5,), (0.5,))
            ])
        else:
            self.model = models.resnet18()
            self.model.fc = nn.Linear(self.model.fc.in_features, 7)
            self.transform = transforms.Compose([
                transforms.Grayscale(num_output_channels=3),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])

        # --- 加载权重 ---
        self.model = self.model.to(self.device)
        try:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
            print("[Vision] ✅ 视觉网络权重装载完毕！")
        except Exception as e:
            print(f"[Vision Error] 权重加载失败: {e}")
            # 即便失败也不要崩溃，只是不进行情绪预测而已

        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def run(self):
        """线程的核心死循环：在后台默默干活"""
        cap = cv2.VideoCapture(0)
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
                
            frame = cv2.flip(frame, 1)
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray_frame, scaleFactor=1.3, minNeighbors=5)
            
            current_emotion = "None"
            confidence = 0.0

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                roi_gray = gray_frame[y:y+h, x:x+w]
                
                # 防错机制：防止框出画面外的无效人脸
                if roi_gray.size == 0:
                    continue

                roi_pil = Image.fromarray(roi_gray)
                roi_tensor = self.transform(roi_pil).unsqueeze(0).to(self.device)
                
                with torch.no_grad():
                    output = self.model(roi_tensor)
                    probabilities = F.softmax(output, dim=1)
                    max_prob, predicted = torch.max(probabilities, 1)
                    
                    emotion_idx = predicted.item()
                    current_emotion = self.emotion_dict[emotion_idx]
                    confidence = max_prob.item() * 100
                    
                # 将当前帧的结果写入 2秒 队列
                self.emotion_queue.append(current_emotion)
                
                # 将信息画在框上
                text = f"{current_emotion} ({confidence:.1f}%)"
                cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # --- 统计 2 秒内的情绪频率 (归一化) ---
            stats_dict = {}
            if len(self.emotion_queue) > 0:
                total_frames = len(self.emotion_queue)
                for emo in set(self.emotion_queue):
                    count = self.emotion_queue.count(emo)
                    # 保留两位小数的百分比
                    stats_dict[emo] = round(count / total_frames, 2)
            
            # --- 通过信号将数据发送给主界面的 UI ---
            # 把 BGR 画面转成 RGB 发给 PyQt
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame_ready.emit(frame_rgb)
            self.current_status_ready.emit(current_emotion, confidence)
            self.emotion_stats_ready.emit(stats_dict)

            # 为了防止后台 CPU 占用过高，强行让线程睡 30 毫秒 (大约限制在 30 FPS)
            QThread.msleep(30)
            
        cap.release()
        print("[Vision] 视觉后台线程已安全终止。")

    def stop(self):
        """提供给外部调用的终止方法"""
        self.running = False
        self.wait() # 阻塞等待线程彻底关停