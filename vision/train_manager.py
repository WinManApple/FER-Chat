import os
import time

# 导入三个训练脚本的模块
# （管家会调用它们内部的 main 函数）
import train
import train_resnet
import train_efficientnet

def main():
    print("="*50)
    print("🤖 视觉模型自动训练管家 (Train Manager) 启动")
    print("="*50)

    # ==========================================
    # ⚙️ 统一训练参数配置区
    # ==========================================
    BATCH_SIZE = 64
    LEARNING_RATE = 0.001
    NUM_EPOCHS = 30
    
    # 将参数拼接成字符串，用于追加到保存的文件名中
    # 例如：bs64_lr0.001_ep30
    param_suffix = f"bs{BATCH_SIZE}_lr{LEARNING_RATE}_ep{NUM_EPOCHS}"
    
    print(f"📦 当前统一训练参数:")
    print(f"   - Batch Size: {BATCH_SIZE}")
    print(f"   - Learning Rate: {LEARNING_RATE}")
    print(f"   - Epochs: {NUM_EPOCHS}")
    print(f"🏷️ 文件名后缀标识: {param_suffix}\n")

    # ==========================================
    # 📋 定义训练任务队列
    # ==========================================
    training_queue = [
        ("基础版 Custom CNN (train.py)", train.main),
        ("进阶版 ResNet-18 (train_resnet.py)", train_resnet.main),
        ("顶配版 EfficientNet-B0 (train_efficientnet.py)", train_efficientnet.main)
    ]

    # ==========================================
    # 🚀 顺序执行训练任务
    # ==========================================
    total_start_time = time.time()

    for model_name, train_func in training_queue:
        print("-" * 40)
        print(f"▶️ 开始执行任务: {model_name}")
        print("-" * 40)
        
        try:
            # 调用子脚本的 main 函数，并透传参数
            train_func(
                batch_size=BATCH_SIZE,
                learning_rate=LEARNING_RATE,
                num_epochs=NUM_EPOCHS,
                param_suffix=param_suffix
            )
            print(f"\n✅ 任务圆满完成: {model_name}\n")
            
        except Exception as e:
            # 防御性编程：如果某个模型报错（比如显存溢出），不会导致整个管家崩溃
            print(f"\n❌ 任务发生严重错误: {model_name}")
            print(f"错误详情: {e}")
            print("⚠️ 管家已捕获异常，将跳过此模型，继续执行下一个任务...\n")

    # 统计总耗时
    total_time = time.time() - total_start_time
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    
    print("="*50)
    print(f"🎉 所有训练任务执行完毕！")
    print(f"⏱️ 自动化流水线总耗时: {minutes} 分 {seconds} 秒")
    print("="*50)

if __name__ == '__main__':
    main()