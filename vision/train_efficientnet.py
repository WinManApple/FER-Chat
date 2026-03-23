import os
import datetime
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import confusion_matrix

# ==========================================
# ⚙️ 动态寻址：指向项目根目录
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)

TRAIN_DIR = os.path.join(ROOT_DIR, 'datasets', 'archive', 'train')
TEST_DIR = os.path.join(ROOT_DIR, 'datasets', 'archive', 'test')

# 基础输出目录
SAVE_DIR = os.path.join(ROOT_DIR, 'models', 'visions')
os.makedirs(SAVE_DIR, exist_ok=True)

DATA_SAVE_DIR = os.path.join(ROOT_DIR, 'train_data', 'efficientnet')
os.makedirs(DATA_SAVE_DIR, exist_ok=True)


# 🌟 核心修改：接收管家传来的超参数
def main(batch_size=64, learning_rate=0.001, num_epochs=30, param_suffix="default"):
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    print(f"\n--- 🚀 顶配版炼丹炉 (EfficientNet-B0) 点火！当前使用设备: {device} ---")

    # 生成包含参数和时间的唯一标识
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_identifier = f"{param_suffix}_{current_time}"
    
    # 动态生成带参数后缀的保存路径
    MODEL_SAVE_PATH = os.path.join(SAVE_DIR, f'models_efficientnet_{file_identifier}.pth') 

    # ==========================================
    # 📦 数据加载
    # ==========================================
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
    
    class_names = train_dataset.classes

    # 使用外部传入的 batch_size
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=2)

    # ==========================================
    # 🧠 模型与优化器初始化
    # ==========================================
    print("🧠 正在加载 EfficientNet-B0 预训练模型...")
    model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
    
    num_ftrs = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_ftrs, 7) 
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    
    # 使用外部传入的 learning_rate 和 num_epochs
    optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)

    best_test_acc = 0.0
    
    history_epochs = []
    history_train_loss = []
    history_test_loss = [] 
    history_train_acc = []
    history_test_acc = []
    history_lr = []

    for epoch in range(num_epochs):
        current_lr = scheduler.get_last_lr()[0]
        
        # ----------- 训练阶段 -----------
        model.train() 
        running_train_loss = 0.0
        correct_train = 0
        total_train = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()       
            outputs = model(images)     
            loss = criterion(outputs, labels) 
            loss.backward()             
            optimizer.step()            

            running_train_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total_train += labels.size(0)
            correct_train += (predicted == labels).sum().item()

        train_acc = 100 * correct_train / total_train
        avg_train_loss = running_train_loss / len(train_loader)

        # ----------- 测试阶段 -----------
        model.eval() 
        running_test_loss = 0.0 
        correct_test = 0
        total_test = 0
        
        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                
                loss = criterion(outputs, labels)
                running_test_loss += loss.item()

                _, predicted = torch.max(outputs.data, 1)
                total_test += labels.size(0)
                correct_test += (predicted == labels).sum().item()

        test_acc = 100 * correct_test / total_test
        avg_test_loss = running_test_loss / len(test_loader) 

        # 记录数据
        history_epochs.append(epoch + 1)
        history_train_loss.append(avg_train_loss)
        history_test_loss.append(avg_test_loss) 
        history_train_acc.append(train_acc)
        history_test_acc.append(test_acc)
        history_lr.append(current_lr)

        print(f"Epoch [{epoch+1:02d}/{num_epochs}] "
              f"LR: {current_lr:.6f} | "
              f"Train Loss: {avg_train_loss:.4f} | "
              f"Test Loss: {avg_test_loss:.4f} | "
              f"Train Acc: {train_acc:.2f}% | "
              f"Test Acc: {test_acc:.2f}%")

        scheduler.step()

        if test_acc > best_test_acc:
            print(f"   ⭐️ 破纪录！准确率提升至 {test_acc:.2f}%，保存权重...")
            best_test_acc = test_acc
            torch.save(model.state_dict(), MODEL_SAVE_PATH)

    # ==========================================
    # 📊 训练结束，保存各种图表 (带标识)
    # ==========================================
    print(f"\n🎉 炼丹结束！正在生成数据报告至 {DATA_SAVE_DIR} ...")
    
    df = pd.DataFrame({
        'Epoch': history_epochs,
        'Learning_Rate': history_lr,
        'Train_Loss': history_train_loss,
        'Test_Loss': history_test_loss, 
        'Train_Acc': history_train_acc,
        'Test_Acc': history_test_acc
    })
    df.to_csv(os.path.join(DATA_SAVE_DIR, f'metrics_{file_identifier}.csv'), index=False)
    
    # Loss 图
    plt.figure(figsize=(10, 5))
    plt.plot(history_epochs, history_train_loss, label='Train Loss', color='red', marker='o')
    plt.plot(history_epochs, history_test_loss, label='Test Loss', color='orange', marker='x')
    plt.title(f'Loss Curve (EfficientNet-B0) - {param_suffix}')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(DATA_SAVE_DIR, f'loss_curve_{file_identifier}.png'))
    plt.close()

    # Accuracy 图
    plt.figure(figsize=(10, 5))
    plt.plot(history_epochs, history_train_acc, label='Train Accuracy', color='blue', marker='o')
    plt.plot(history_epochs, history_test_acc, label='Test Accuracy', color='green', marker='s')
    plt.title(f'Accuracy Curve (EfficientNet-B0) - {param_suffix}')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(DATA_SAVE_DIR, f'acc_curve_{file_identifier}.png'))
    plt.close()

    # ==========================================
    # 🕵️ 绘制最佳权重的混淆矩阵
    # ==========================================
    print("🕵️ 正在加载最佳权重，生成终极混淆矩阵...")
    model.load_state_dict(torch.load(MODEL_SAVE_PATH))
    model.eval()
    
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    cm = confusion_matrix(all_labels, all_preds)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names, yticklabels=class_names)
    plt.title(f'Confusion Matrix (EfficientNet-B0 Best) - {param_suffix}')
    plt.ylabel('True Emotion')
    plt.xlabel('Predicted Emotion')
    
    plt.tight_layout() 
    plt.savefig(os.path.join(DATA_SAVE_DIR, f'confusion_matrix_{file_identifier}.png'))
    plt.close()

    print(f"✅ EfficientNet-B0 训练与评估完成！最终权重路径: {MODEL_SAVE_PATH}")

if __name__ == '__main__':
    # 支持单独运行
    main()