import os
import pyautogui
import cv2
import numpy as np
from datetime import datetime
import time

THRESHOLD = 0.8
OUTPUT_DIR = r"D:\Desktop\t\start"
CLICK_DELAY = 1.0

BUTTONS = [
    ("再玩一局", "play_again.png", 100, 0, 1),
    ("返回", "back.png", 0, 0, 2),
    ("restart", "restart.png", 0, 0, 3),
]

def find_button(screenshot, template_path, offset_x=0, offset_y=0):
    """在截图中查找按钮"""
    if not os.path.exists(template_path):
        return None
    
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        return None
    
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= THRESHOLD:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2 + offset_x
        center_y = max_loc[1] + h // 2 + offset_y
        return (center_x, center_y), max_val
    
    return None

def click_buttons(screenshot):
    """按优先级查找并点击按钮"""
    for name, template, offset_x, offset_y, _ in sorted(BUTTONS, key=lambda x: x[4]):
        result = find_button(screenshot, template, offset_x, offset_y)
        if result:
            center, confidence = result
            pyautogui.click(center[0], center[1])
            print(f"✓ 点击{name}，置信度：{confidence:.2f}")
            time.sleep(CLICK_DELAY)
            return center
    return None

def mark_buttons(img):
    """标记所有找到的按钮"""
    for name, template, offset_x, offset_y, _ in BUTTONS:
        result = find_button(img, template, offset_x, offset_y)
        if result:
            center, confidence = result
            w, h = cv2.imread(template).shape[1], cv2.imread(template).shape[0]
            top_left = (int(center[0] - w // 2 - offset_x), int(center[1] - h // 2 - offset_y))
            bottom_right = (top_left[0] + w, top_left[1] + h)
            
            cv2.rectangle(img, top_left, bottom_right, (0, 0, 255), 2)
            cv2.circle(img, center, 8, (0, 255, 0), -1)
            cv2.putText(img, f"{name} ({confidence:.2f})", 
                       (top_left[0], max(top_left[1] - 10, 20)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    return img

def main():
    """主函数"""
    if any(not os.path.exists(t) for _, t, _, _, _ in BUTTONS):
        print("✗ 缺少模板文件")
        return
    
    screenshot = pyautogui.screenshot()
    img_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    clicked = click_buttons(img_cv)
    marked_img = mark_buttons(img_cv.copy())
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    cv2.imwrite(output_path, marked_img)
    
    print(f"✓ 已保存：{output_path}")
    print(f"✓ 操作{'成功' if clicked else '失败'}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"✗ 操作失败：{e}")
