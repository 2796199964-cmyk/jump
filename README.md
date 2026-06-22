# 🎮 WeChat-Jump-Auto (微信跳一跳全自动运行脚本)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/OpenCV-4.x-green?logo=opencv" alt="OpenCV">
  <img src="https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows" alt="Windows">
</p>

## 📖 项目简介

**WeChat-Jump-Auto** 是一款专为 **PC 端微信“跳一跳”** 小游戏设计的全自动挂机脚本。

与市面上常见的 ADB 手机投屏方案或简单的颜色识别不同，本项目采用**纯计算机视觉（CV）方案**。通过全屏截图、HSV 色彩空间边缘检测、复杂的几何轮廓相交计算，精准识别棋子与目标方块的中心点。系统根据两点间的像素距离，动态计算鼠标按压时长，实现无限循环的自动跳跃。

## ✨ 核心特性

- 👁️ **纯视觉无损识别**：不修改内存、不依赖 ADB，纯靠 `PyAutoGUI` 截图与 `OpenCV` 图像分析，安全防封。
- 📐 **硬核几何定位算法**： `pho_cycle.py` 
  - 摒弃简单的模板匹配，采用 **HSV 多通道 Canny 边缘检测** 提取目标轮廓。
  - 构建**方向射线**，计算射线与目标 3D 轮廓的交点。
  - 智能识别目标块的“开口向下角点”或“椭圆弧顶”，并通过**直角三角形几何投影**精准修正目标中心点。
- ⏱️ **动态按压映射**：建立像素距离与鼠标 `mouseDown` 时长的线性物理模型（`duration = (distance - 50) / 520`），完美适配不同距离的跳跃。
- 🔄 **全自动无限循环**：
  -  `start.py` **守护进程**，主脚本崩溃或卡死时 10 秒自动重启。
  -  `do.py` **状态机**，自动识别游戏结束界面并点击“再玩一局”、“返回”或“Restart”，实现 24 小时无人值守。
- 🛡️ **防重复与防抖动**：
  - 截图**相似度比对**（>99% 跳过分析），避免画面未更新时重复起跳。
  - 跳跃后**区域稳定性检测**，等待画面完全静止后再进行下一次计算。

## 🛠️ 技术栈

| 技术/库 | 用途说明 |
| --- | --- |
| **Python 3.x** | 核心开发语言 |
| **OpenCV (`cv2`)** | 模板匹配、HSV 色彩转换、Canny 边缘检测、轮廓提取 (`findContours`)、凸包与椭圆拟合 |
| **PyAutoGUI** | 屏幕截图、鼠标移动、精准控制 `mouseDown/mouseUp` 按压时长 |
| **NumPy** | 矩阵运算、向量交点计算、图像差异比对 |

## 📦 环境准备与安装

### 1. 克隆仓库
```bash
git clone https://github.com/your-username/WeChat-Jump-Auto.git
cd WeChat-Jump-Auto
