import torch
import torch.nn as nn

class FaceEmotionCNN(nn.Module):
    def __init__(self, num_classes=7):
        super(FaceEmotionCNN, self).__init__()
        
        # 车间一：提取边缘和浅层特征
        # 输入: [Batch, 1, 48, 48] -> 输出: [Batch, 32, 24, 24]
        self.block1 = nn.Sequential(
            nn.Conv2d(in_channels=1, out_channels=32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32), # 稳压器：加速收敛
            nn.ReLU(),          # 激活函数：只保留有用信号
            nn.MaxPool2d(kernel_size=2, stride=2) # 池化：尺寸缩小一半
        )
        
        # 车间二：提取局部面部轮廓（眼睛、嘴巴）
        # 输入: [Batch, 32, 24, 24] -> 输出: [Batch, 64, 12, 12]
        self.block2 = nn.Sequential(
            nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        # 车间三：提取高级表情特征（皱眉、上扬）
        # 输入: [Batch, 64, 12, 12] -> 输出: [Batch, 128, 6, 6]
        self.block3 = nn.Sequential(
            nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        # 车间四：终极特征融合
        # 输入: [Batch, 128, 6, 6] -> 输出: [Batch, 256, 3, 3]
        self.block4 = nn.Sequential(
            nn.Conv2d(in_channels=128, out_channels=256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        
        # 最终决策室：全连接层分类
        # 展平后的特征数量 = 256个通道 * 3 * 3 = 2304
        self.classifier = nn.Sequential(
            nn.Flatten(),                     # 把立体的特征图拍扁成一维长条
            nn.Linear(256 * 3 * 3, 512),      # 神经元综合打分
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.5),                  # 防过拟合：随机让50%的神经元休眠，防止死记硬背
            nn.Linear(512, num_classes)       # 输出 7 种情绪的得分
        )

    def forward(self, x):
        # 规定数据流向流水线的顺序
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)
        x = self.classifier(x)
        return x

# ==========================================
# 快速测试一下我们的大脑是否运转正常
# ==========================================
if __name__ == '__main__':
    # 实例化模型
    model = FaceEmotionCNN(num_classes=7)
    
    # 模拟生成一批数据：假设抓取了 64 张 48x48 的单通道灰度图
    dummy_input = torch.randn(64, 1, 48, 48)
    
    # 把假数据喂给模型
    output = model(dummy_input)
    
    print("模型大脑创建成功！")
    print(f"输入数据形状: {dummy_input.shape}")
    print(f"输出数据形状: {output.shape}") 
    # 期望输出形状是 [64, 7]，代表 64 张图片，每张图都有 7 个情绪类别的得分