# 跳一跳自动点击脚本

这是一个基于屏幕截图、OpenCV 模板匹配和 `pyautogui` 鼠标控制实现的电脑版微信跳一跳自动点击脚本。

## 文件

| 文件 | 说明 |
| --- | --- |
| `do.py` | 循环运行 `pho_cycle.py` |
| `pho_cycle.py` | 跳一跳主识别与点击逻辑，读取 `top.png`、`main.png`、`point.png` |
| `start.py` | 识别并点击“再玩一局”“返回”“restart”等按钮，读取 `play_again.png`、`back.png`、`restart.png` |
| `play_again.png` | “再玩一局”按钮模板 |
| `back.png` | “返回”按钮模板 |
| `restart.png` | 重启按钮模板 |
| `top.png` | 顶部区域模板 |
| `main.png` | 主区域模板 |
| `point.png` | 目标点模板 |

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

在项目根目录运行：

```bash
python do.py
```

也可以单独运行：

```bash
python pho_cycle.py
python start.py
```

注意：这些脚本使用相对路径读取图片模板，请在项目根目录执行命令。
