import os
import datetime
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
import pandas as pd

# ==========================================
# ⚙️ 炼丹总控台：全局参数 (确保这部分在路径定义之前)
# ==========================================
BATCH_SIZE = 64
LEARNING_RATE = 0.001
NUM_EPOCHS = 30
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")

# ==========================================
# ⚙️ 动态寻址：指向 net 目录
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)

TRAIN_DIR = os.path.join(ROOT_DIR, 'datasets', 'archive', 'train')
TEST_DIR = os.path.join(ROOT_DIR, 'datasets', 'archive', 'test')

SAVE_DIR = os.path.join(ROOT_DIR, 'models', 'visions')
os.makedirs(SAVE_DIR, exist_ok=True)
current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# 确认命名为 models_net_trained_
MODEL_SAVE_PATH = os.path.join(SAVE_DIR, f'models_net_trained_{current_time}.pth') 
# 确认路径为 train_data/net
DATA_SAVE_DIR = os.path.join(ROOT_DIR, 'train_data', 'net')
os.makedirs(DATA_SAVE_DIR, exist_ok=True)


def main():
    print(f"--- 🚀 进阶版炼丹炉点火！当前使用设备: {DEVICE} ---")

    train_transforms = transforms.Compose([
        transforms.Grayscale(num_output_channels=3), 
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    test_transforms = transforms.Compose([
        transforms.Grayscale(num_output_channels=3),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_dataset = datasets.ImageFolder(root=TRAIN_DIR, transform=train_transforms)
    test_dataset = datasets.ImageFolder(root=TEST_DIR, transform=test_transforms)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    print("🧠 正在加载 ResNet-18 大脑...")
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, 7)
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS)

    best_test_acc = 0.0
    
    # 记录数据的列表
    history_epochs = []
    history_train_loss = []
    history_train_acc = []
    history_test_acc = []
    history_lr = []

    for epoch in range(NUM_EPOCHS):
        current_lr = scheduler.get_last_lr()[0]
        
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

        # 记录数据
        history_epochs.append(epoch + 1)
        history_train_loss.append(avg_train_loss)
        history_train_acc.append(train_acc)
        history_test_acc.append(test_acc)
        history_lr.append(current_lr)

        print(f"Epoch [{epoch+1:02d}/{NUM_EPOCHS}] "
              f"LR: {current_lr:.6f} | "
              f"Train Loss: {avg_train_loss:.4f} | "
              f"Train Acc: {train_acc:.2f}% | "
              f"Test Acc: {test_acc:.2f}%")

        scheduler.step()

        if test_acc > best_test_acc:
            print(f"   ⭐️ 破纪录！准确率提升至 {test_acc:.2f}%，保存权重...")
            best_test_acc = test_acc
            torch.save(model.state_dict(), MODEL_SAVE_PATH)

    # ==========================================
    # 📊 保存训练数据曲线
    # ==========================================
    print(f"\n🎉 炼丹结束！正在保存曲线数据至 {DATA_SAVE_DIR} ...")
    
    df = pd.DataFrame({
        'Epoch': history_epochs,
        'Learning_Rate': history_lr,
        'Train_Loss': history_train_loss,
        'Train_Acc': history_train_acc,
        'Test_Acc': history_test_acc
    })
    df.to_csv(os.path.join(DATA_SAVE_DIR, f'metrics_{current_time}.csv'), index=False)
    
    # Loss 图
    plt.figure(figsize=(10, 5))
    plt.plot(history_epochs, history_train_loss, label='Train Loss', color='red', marker='o')
    plt.title('Training Loss Curve (ResNet-18)')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(DATA_SAVE_DIR, f'loss_curve_{current_time}.png'))
    plt.close()

    # Accuracy 图
    plt.figure(figsize=(10, 5))
    plt.plot(history_epochs, history_train_acc, label='Train Accuracy', color='blue', marker='o')
    plt.plot(history_epochs, history_test_acc, label='Test Accuracy', color='green', marker='s')
    plt.title('Accuracy Curve (ResNet-18)')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(DATA_SAVE_DIR, f'acc_curve_{current_time}.png'))
    plt.close()

    print(f"✅ 完成！最终权重路径: {MODEL_SAVE_PATH}")

if __name__ == '__main__':
    main()