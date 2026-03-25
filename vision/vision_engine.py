import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms, models
from PIL import Image
import numpy as np
import os
from collections import deque
from PyQt5.QtCore import QThread, pyqtSignal

# 从同级目录导入基础版 CNN 大脑
from .model import FaceEmotionCNN

class VisionEngine(QThread):
    # ==========================================
    # 📡 定义通讯信号
    # ==========================================
    frame_ready = pyqtSignal(np.ndarray) 
    emotion_stats_ready = pyqtSignal(dict)
    current_status_ready = pyqtSignal(str, float)

    def __init__(self, model_type='resnet', model_path='', yunet_path='models/visions/face_detection_yunet_2023mar.onnx'):
        super().__init__()
        self.running = True 
        self.device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        print(f"[Vision] 后台视觉引擎初始化中，使用设备: {self.device}")

        # --- 情绪标签 ---
        self.emotion_dict = {
            0: 'Angry', 1: 'Disgust', 2: 'Fear', 3: 'Happy', 
            4: 'Neutral', 5: 'Sad', 6: 'Surprise'
        }

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
        elif model_type == 'resnet':
            self.model = models.resnet18()
            self.model.fc = nn.Linear(self.model.fc.in_features, 7)
            self.transform = transforms.Compose([
                transforms.Grayscale(num_output_channels=3),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        elif model_type == 'efficientnet':
            self.model = models.efficientnet_b0()
            num_ftrs = self.model.classifier[1].in_features
            self.model.classifier[1] = nn.Linear(num_ftrs, 7)
            self.transform = transforms.Compose([
                transforms.Grayscale(num_output_channels=3),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        else:
            raise ValueError(f"❌ 视觉引擎启动失败：未知的模型类型 '{model_type}'")

        # --- 加载情绪网络权重 ---
        self.model = self.model.to(self.device)
        try:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
            print("[Vision] ✅ 视觉网络权重装载完毕！")
        except Exception as e:
            print(f"[Vision Error] 权重加载失败: {e}")

        # ==========================================
        # 🌟 替换为 YuNet 人脸检测器初始化
        # ==========================================
        if not os.path.exists(yunet_path):
            print(f"[Error] 找不到 YuNet 模型文件！请确认 {yunet_path} 路径正确。")
            self.face_detector = None
        else:
            # 初始化 YuNet，input_size 暂设为占位符，随后在 run() 中动态调整
            self.face_detector = cv2.FaceDetectorYN.create(
                model=yunet_path,
                config="",
                input_size=(320, 320), 
                score_threshold=0.8,  # 置信度阈值，过滤掉把握不大的假脸
                nms_threshold=0.3,
                top_k=5000
            )
            print("[Vision] ✅ YuNet 人脸检测器加载完毕！")

    def run(self):
        cap = cv2.VideoCapture(0)
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
                
            frame = cv2.flip(frame, 1)
            # 注意：YuNet 通常直接接收 BGR 格式的彩色图，不需要转灰度来检测
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # 灰度图保留给情绪网络截图用
            
            current_emotion = "None"
            confidence = 0.0

            # ==========================================
            # 🌟 使用 YuNet 进行人脸推理
            # ==========================================
            if self.face_detector is not None:
                # YuNet 要求每次检测前，必须告诉它当前画面的宽高
                height, width, _ = frame.shape
                self.face_detector.setInputSize((width, height))
                
                # 开始检测：返回的 faces 是一个 numpy 数组
                _, faces = self.face_detector.detect(frame)
                
                if faces is not None:
                    for face in faces:
                        # YuNet 返回的数据前 4 位是 [x, y, w, h]，后面是关键点和置信度
                        box = face[:4].astype(int)
                        x, y, w, h = box
                        
                        # 【关键防错机制】防止 YuNet 框出的坐标超出画面边界，导致 numpy 切片报错
                        x = max(0, x)
                        y = max(0, y)
                        w = min(width - x, w)
                        h = min(height - y, h)
                        
                        # 防错机制：防止框出画面外的无效人脸
                        if w <= 0 or h <= 0:
                            continue

                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                        roi_gray = gray_frame[y:y+h, x:x+w]
                        
                        roi_pil = Image.fromarray(roi_gray)
                        roi_tensor = self.transform(roi_pil).unsqueeze(0).to(self.device)
                        
                        with torch.no_grad():
                            output = self.model(roi_tensor)
                            probabilities = F.softmax(output, dim=1)
                            max_prob, predicted = torch.max(probabilities, 1)
                            
                            emotion_idx = predicted.item()
                            current_emotion = self.emotion_dict[emotion_idx]
                            confidence = max_prob.item() * 100
                            
                        self.emotion_queue.append(current_emotion)
                        
                        text = f"{current_emotion} ({confidence:.1f}%)"
                        cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # --- 统计 2 秒内的情绪频率 (归一化) ---
            stats_dict = {}
            if len(self.emotion_queue) > 0:
                total_frames = len(self.emotion_queue)
                for emo in set(self.emotion_queue):
                    count = self.emotion_queue.count(emo)
                    stats_dict[emo] = round(count / total_frames, 2)
            
            # --- 通过信号将数据发送给主界面的 UI ---
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame_ready.emit(frame_rgb)
            self.current_status_ready.emit(current_emotion, confidence)
            self.emotion_stats_ready.emit(stats_dict)

            QThread.msleep(30)
            
        cap.release()
        print("[Vision] 视觉后台线程已安全终止。")

    def stop(self):
        self.running = False
        self.wait()