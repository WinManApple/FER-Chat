# 表情识别与LLM互动

本项目（FER-Chat）是一个融合了计算机视觉、语音识别、大语言模型和语音合成的多模态交互桌面端应用。系统通过本地摄像头实时捕捉并分析用户的情绪成分，结合用户的语音/文本输入，驱动虚拟角色做出智能回应。

## 运行环境与依赖框架

本项目主要依赖以下核心框架：
* **深度学习框架**：PyTorch
* **视觉处理**：OpenCV (`opencv-python`)
* **UI 框架**：PyQt5
* **语音识别 (ASR)**：Faster-Whisper
* **语音合成 (TTS)**：GPT-SoVITS

## 训练数据集

* **人脸表情训练集**：[FER-2013 (Kaggle)](https://www.kaggle.com/datasets/msambare/fer2013)
    * 本项目包含一套从零编写的 CNN 架构（适配 48x48 灰度图）及基于 ResNet-18 的迁移学习训练脚本，均使用该数据集进行模型训练。

## 致谢与模型声明

本系统的运行离不开优秀的开源社区和模型作者。特别感谢以下项目的支持：

* **语音识别模型**：使用 [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) 实现高效的本地离线语音转录。
* **语音合成方案**：基于 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 框架。
* **角色音色模型**：
    * **模型来源**：魔搭社区 (ModelScope) - [aihobbyist / Anime_GPT-Sovits_Models](https://www.modelscope.cn/models/aihobbyist/Anime_GPT-Sovits_Models)
    * **模型作者**：aihobbyist

    * **⚠️ 协议与版权声明**：本项目及引用的音色模型仅供技术学习与代码架构交流，**严禁用于任何商业用途**。项目中默认提及的虚拟角色及相关设定、图像、音频等知识产权均归属于原版权方（米哈游 miHoYo）。

## 快速开始

本项目不包含具体的 API Key 及本地模型路径配置。在运行主程序前，请完成以下配置：

1.  **准备大模型配置**：
    在 `llm/` 目录下复制 `config.example.json` 并重命名为 `config.json`，填入你的 API 密钥与大模型接口地址。
2.  **准备语音合成组件**：
    * 将下载好的 GPT-SoVITS 源码解压至项目根目录，并命名为 `GPT-SoVITS`。
    * 在 `audio/` 目录下复制 `config.example.json` 并重命名为 `config.json`，配置角色模型及参考音频的相对路径。
3.  **运行系统**：
    ```bash
    python main.py
    ```