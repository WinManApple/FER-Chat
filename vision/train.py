import os
import datetime
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
import pandas as pd

from model import FaceEmotionCNN

# ==========================================
# ⚙️ 炼丹总控台：全局参数
# ==========================================
BATCH_SIZE = 64
LEARNING_RATE = 0.001
NUM_EPOCHS = 30
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")

# ==========================================
# ⚙️ 动态寻址：指向 raw 目录
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)

TRAIN_DIR = os.path.join(ROOT_DIR, 'datasets', 'archive', 'train')
TEST_DIR = os.path.join(ROOT_DIR, 'datasets', 'archive', 'test')

SAVE_DIR = os.path.join(ROOT_DIR, 'models', 'visions')
os.makedirs(SAVE_DIR, exist_ok=True)
current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# 修改点：命名改为 models_raw_trained_
MODEL_SAVE_PATH = os.path.join(SAVE_DIR, f'models_raw_trained_{current_time}.pth') 
# 修改点：路径改为 train_data/raw
DATA_SAVE_DIR = os.path.join(ROOT_DIR, 'train_data', 'raw')
os.makedirs(DATA_SAVE_DIR, exist_ok=True)

def main():
    print(f"--- 炼丹炉点火！当前使用设备: {DEVICE} ---")

    train_transforms = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((48, 48)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])
    test_transforms = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((48, 48)),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])

    train_dataset = datasets.ImageFolder(root=TRAIN_DIR, transform=train_transforms)
    test_dataset = datasets.ImageFolder(root=TEST_DIR, transform=test_transforms)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    model = FaceEmotionCNN(num_classes=7).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    best_test_acc = 0.0
    
    # 用于记录数据的列表
    history_epochs = []
    history_train_loss = []
    history_train_acc = []
    history_test_acc = []

    for epoch in range(NUM_EPOCHS):
        model.train() 
        running_loss = 0.0
        correct_train = 0
        total_train = 0

        for images, labels in train_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)

            optimizer.zero_grad()       
            outputs = model(images)     
            loss = criterion(outputs, labels) 
            loss.backward()             
            optimizer.step()            

            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1) 
            total_train += labels.size(0)
            correct_train += (predicted == labels).sum().item()

        train_acc = 100 * correct_train / total_train
        avg_train_loss = running_loss / len(train_loader)

        model.eval() 
        correct_test = 0
        total_test = 0
        
        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(DEVICE), labels.to(DEVICE)
                outputs = model(images)
                _, predicted = torch.max(outputs.data, 1)
                total_test += labels.size(0)
                correct_test += (predicted == labels).sum().item()

        test_acc = 100 * correct_test / total_test

        # 记录本轮数据
        history_epochs.append(epoch + 1)
        history_train_loss.append(avg_train_loss)
        history_train_acc.append(train_acc)
        history_test_acc.append(test_acc)

        print(f"Epoch [{epoch+1:02d}/{NUM_EPOCHS}] "
              f"Train Loss: {avg_train_loss:.4f} | "
              f"Train Acc: {train_acc:.2f}% | "
              f"Test Acc: {test_acc:.2f}%")

        if test_acc > best_test_acc:
            print(f"   ⭐️ 破纪录！准确率提升至 {test_acc:.2f}%，正在保存...")
            best_test_acc = test_acc
            torch.save(model.state_dict(), MODEL_SAVE_PATH)

    # ==========================================
    # 📊 训练结束，绘制并保存数据曲线
    # ==========================================
    print(f"\n🎉 炼丹结束！正在保存训练数据曲线至 {DATA_SAVE_DIR} ...")
    
    # 1. 保存为 CSV 表格
    df = pd.DataFrame({
        'Epoch': history_epochs,
        'Train_Loss': history_train_loss,
        'Train_Acc': history_train_acc,
        'Test_Acc': history_test_acc
    })
    df.to_csv(os.path.join(DATA_SAVE_DIR, f'metrics_{current_time}.csv'), index=False)
    
    # 2. 绘制并保存 Loss 曲线图
    plt.figure(figsize=(10, 5))
    plt.plot(history_epochs, history_train_loss, label='Train Loss', color='red', marker='o')
    plt.title('Training Loss Curve (Raw CNN)')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(DATA_SAVE_DIR, f'loss_curve_{current_time}.png'))
    plt.close()

    # 3. 绘制并保存 Accuracy 曲线图
    plt.figure(figsize=(10, 5))
    plt.plot(history_epochs, history_train_acc, label='Train Accuracy', color='blue', marker='o')
    plt.plot(history_epochs, history_test_acc, label='Test Accuracy', color='green', marker='s')
    plt.title('Accuracy Curve (Raw CNN)')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(DATA_SAVE_DIR, f'acc_curve_{current_time}.png'))
    plt.close()

    print(f"✅ 曲线与权重保存完成！最终权重路径: {MODEL_SAVE_PATH}")

if __name__ == '__main__':
    main()