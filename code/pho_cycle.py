import os
import cv2
import numpy as np
import pyautogui
import math
import time
import subprocess
from datetime import datetime

# 预加载模板图片（全局变量）
TEMPLATES = {
    'top': None,
    'main': None,
    'point': None
}

def load_templates():
    """预加载所有模板图片"""
    TEMPLATES['top'] = cv2.imread('top.png', cv2.IMREAD_COLOR)
    TEMPLATES['main'] = cv2.imread('main.png', cv2.IMREAD_COLOR)
    TEMPLATES['point'] = cv2.imread('point.png', cv2.IMREAD_COLOR)
    
    if TEMPLATES['top'] is None:
        raise ValueError("top.png 加载失败")
    if TEMPLATES['main'] is None:
        raise ValueError("main.png 加载失败")

def run_start_script():
    """运行 start.py 脚本"""
    try:
        subprocess.Popen(['python', 'start.py'])
        time.sleep(3)
        return True
    except Exception as e:
        print(f"启动 start.py 失败: {str(e)}")
        return False

def save_original_screenshot(output_dir, cycle_count, timestamp):
    """保存原始截图到指定目录"""
    y_dir = os.path.join(output_dir, "y")
    original_path = os.path.join(y_dir, f"original_{timestamp}_{cycle_count - 1}.png")

    try:
        os.makedirs(y_dir, exist_ok=True)
        screenshot = pyautogui.screenshot()

        # 检查 y 目录是否已有图片
        similarity = 0
        if os.path.exists(y_dir) and os.listdir(y_dir):
            # 获取 y 目录中所有图片文件
            image_files = [f for f in os.listdir(y_dir)
                           if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]

            if image_files:
                # 按修改时间排序，获取最新的图片
                image_files.sort(key=lambda x: os.path.getmtime(os.path.join(y_dir, x)))
                latest_image_path = os.path.join(y_dir, image_files[-1])

                # 读取最新的图片
                latest_img = cv2.imread(latest_image_path)
                if latest_img is not None:
                    # 将 PIL 截图转换为 OpenCV 格式
                    current_img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

                    # 调整图片尺寸使其相同
                    if current_img.shape != latest_img.shape:
                        current_img = cv2.resize(current_img, (latest_img.shape[1], latest_img.shape[0]))

                    # 使用简单的像素差异计算相似度
                    diff = cv2.absdiff(current_img, latest_img)
                    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

                    # 计算差异比例
                    total_pixels = gray_diff.shape[0] * gray_diff.shape[1]
                    diff_pixels = np.count_nonzero(gray_diff > 10)  # 阈值 10，忽略微小差异

                    similarity = 100 * (1 - diff_pixels / total_pixels)

                    print(f"截图相似度: {similarity:.2f}%")

                    # 如果相似度超过 99%，不保存新截图
                    if similarity >= 99.0:
                        return None, similarity

        # 保存截图
        screenshot.save(original_path)
        return original_path, similarity

    except Exception as e:
        print(f"保存原始截图失败: {str(e)}")
        return None, 0

def save_marked_image(output_dir, marked_img, cycle_count, timestamp):
    """保存标记后的图像到指定目录"""
    marked_path = os.path.join(output_dir, f"bj/bj_{timestamp}_{cycle_count}.png")

    try:
        os.makedirs(os.path.join(output_dir, "bj"), exist_ok=True)
        cv2.imwrite(marked_path, marked_img)
        return marked_path
    except Exception as e:
        print(f"保存标记截图失败: {str(e)}")
        return None

def find_line_contour_intersections(contour, line_start, line_end):
    """计算轮廓与直线的所有交点"""
    intersections = []
    line_vec = np.array(line_end) - np.array(line_start)
    line_len = np.linalg.norm(line_vec)

    if line_len == 0:
        return intersections

    line_dir = line_vec / line_len

    for i in range(len(contour)):
        pt1 = contour[i][0]
        pt2 = contour[(i + 1) % len(contour)][0]
        edge_vec = np.array(pt2) - np.array(pt1)

        denom = np.cross(line_dir, edge_vec)
        if abs(denom) < 1e-5:
            continue

        t = np.cross(np.array(pt1) - np.array(line_start), edge_vec) / denom
        u = np.cross(np.array(line_start) - np.array(pt1), line_dir) / -denom

        if 0 <= t <= line_len and 0 <= u <= 1:
            intersect = np.array(line_start) + t * line_dir
            intersections.append(tuple(intersect.astype(int)))

    return intersections

def calculate_farthest_point_to_main(points, main_center):
    """计算点集中到 main 中心点最远的点"""
    if not points:
        return None, 0

    max_distance = 0
    farthest_point = None

    for pt in points:
        dist = math.sqrt((pt[0] - main_center[0]) ** 2 + (pt[1] - main_center[1]) ** 2)
        if dist > max_distance:
            max_distance = dist
            farthest_point = pt

    return farthest_point, max_distance

def calculate_point_at_distance(start_point, end_point, distance):
    """计算从 start_point 到 end_point 方向上指定距离的点"""
    vec = np.array(end_point) - np.array(start_point)
    vec_len = np.linalg.norm(vec)

    if vec_len == 0:
        return start_point

    unit_vec = vec / vec_len
    target_point = np.array(start_point) + unit_vec * distance
    return tuple(target_point.astype(int))

def find_downward_angle_or_ellipse_top(contour, line_start, line_end):
    """在与方向线相交的轮廓里查找开口向下的角的顶点或椭圆的弧的上半部分"""
    intersections = find_line_contour_intersections(contour, line_start, line_end)
    if not intersections:
        return None, None
 
    # 计算轮廓的凸包
    hull = cv2.convexHull(contour)

    # 检查是否是近似椭圆
    center = None
    if len(contour) >= 5:
        try:
            ellipse = cv2.fitEllipse(contour)
            center, axes, angle = ellipse
        except:
            center = None

    # 计算轮廓的矩
    M = cv2.moments(contour)
    if M['m00'] == 0:
        return None, None

    # 查找轮廓的最低点
    lowest_point = None
    min_y = float('inf')
    for point in contour:
        y = point[0][1]
        if y < min_y:
            min_y = y
            lowest_point = tuple(point[0])

    # 检查最低点是否在轮廓的凸包上
    is_on_hull = any(tuple(point[0]) == lowest_point for point in hull)

    # 如果是凸包上的最低点，可能是开口向下的角
    if is_on_hull:
        return lowest_point, "corner"

    # 如果不是，则检查是否是椭圆的上半部分
    if center is not None:
        top_points = []
        for point in contour:
            x, y = point[0]
            if y < center[1]:  # 在椭圆中心上方
                top_points.append((x, y))

        if top_points:
            top_points.sort(key=lambda p: p[1])
            return top_points[0], "ellipse"

    return None, None

def find_farthest_point(points, center):
    """找到点集中距离中心点最远的点"""
    if not points:
        return None

    max_dist = 0
    farthest_point = None

    for pt in points:
        dist = np.linalg.norm(np.array(pt) - np.array(center))
        if dist > max_dist:
            max_dist = dist
            farthest_point = pt

    return farthest_point

def find_vertical_intersection(point, line_start, line_end):
    """找到点沿着竖直方向与直线的交点"""
    line_vec = np.array(line_end) - np.array(line_start)

    if line_vec[0] == 0:  # 垂直线，无交点或重合
        return None

    # 计算交点参数 t
    t = (point[0] - line_start[0]) / line_vec[0]

    if 0 <= t <= 1:
        intersect_y = line_start[1] + t * line_vec[1]
        return (point[0], int(intersect_y))

    return None

def adjust_special_point(contour, special_point):
    """如果轮廓中有与特殊点同一 y 坐标的线段，则更新特殊点为该线段的中点"""
    same_y_points = []

    for i in range(len(contour)):
        pt = contour[i][0]
        if abs(pt[1] - special_point[1]) < 1:  # 允许 1 像素的误差
            same_y_points.append(pt)

    if len(same_y_points) >= 2:
        min_x = min(pt[0] for pt in same_y_points)
        max_x = max(pt[0] for pt in same_y_points)
        mid_x = (min_x + max_x) // 2
        return (mid_x, special_point[1])

    return special_point

def find_nearest_vertical_segment_top(contour, special_point):
    """在轮廓中查找距离特殊点最近的竖直线段的上顶点"""
    vertical_threshold = 2
    min_segment_length = 3

    nearest_top_point = None
    min_y_distance = float('inf')

    for i in range(len(contour)):
        pt1 = tuple(contour[i][0])
        pt2 = tuple(contour[(i + 1) % len(contour)][0])

        dx = abs(pt2[0] - pt1[0])
        dy = abs(pt2[1] - pt1[1])
        segment_length = math.sqrt(dx ** 2 + dy ** 2)

        if dx < vertical_threshold and segment_length > min_segment_length:
            top_point = pt1 if pt1[1] < pt2[1] else pt2
            # 计算 y 坐标的差值（垂直距离）
            y_distance = abs(top_point[1] - special_point[1])

            if y_distance < min_y_distance:
                min_y_distance = y_distance
                nearest_top_point = top_point

    return nearest_top_point

def analyze_and_mark_screen(output_dir, cycle_count, timestamp):
    """全屏截图并执行智能标记"""
    # 保存原始截图
    original_path, similarity = save_original_screenshot(output_dir, cycle_count, timestamp)

    # 如果相似度超过 99%，不保存截图
    if original_path is None and similarity >= 99.0:
        print(f"截图与最新图片高度相似（{similarity:.2f}%），跳过本次分析")

        # 先截取当前屏幕
        screenshot = pyautogui.screenshot()
        screen_img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # 尝试定位 main.png
        main_template = cv2.imread('main.png', cv2.IMREAD_COLOR)
        if main_template is not None:
            # 在整个屏幕上搜索 main.png
            main_res = cv2.matchTemplate(screen_img, main_template, cv2.TM_CCOEFF_NORMED)
            _, main_val, _, _ = cv2.minMaxLoc(main_res)

            print(f"main.png 匹配置信度：{main_val:.2f}")

            # 如果没有找到 main.png（置信度低于 0.9）
            if main_val < 0.9:
                print("当前截图与最新图片高度相似，且没有找到 main.png，等待 5 秒...")
                time.sleep(5)
                
                # 清理内存
                del main_template, screen_img, screenshot
                return None
            else:
                print("找到了 main.png，继续分析...")
        else:
            print("main.png 加载失败，等待 5 秒...")
            time.sleep(5)
            
            # 清理内存
            del screenshot, screen_img
            return None

    # 如果 original_path 是 None 但 similarity 小于 99%，说明保存失败
    if original_path is None:
        print("截图保存失败，跳过本次分析")
        return None

    # 读取截图
    screen_img = cv2.imread(original_path)
    if screen_img is None:
        raise ValueError("无法读取原始截图")

    marked_img = screen_img.copy()
    screen_height, screen_width = screen_img.shape[:2]

    # 1. 定位 top.png
    top_template = cv2.imread('top.png', cv2.IMREAD_COLOR)
    if top_template is None:
        raise ValueError("top.png 加载失败")

    top_h, top_w = top_template.shape[:2]
    top_res = cv2.matchTemplate(screen_img, top_template, cv2.TM_CCOEFF_NORMED)
    _, top_val, _, top_loc = cv2.minMaxLoc(top_res)

    if top_val < 0.9:
        raise RuntimeError(f"top.png 匹配失败 (置信度：{top_val:.2f})")

    top_bottom = top_loc[1] + top_h
    cv2.rectangle(marked_img, top_loc, (top_loc[0] + top_w, top_loc[1] + top_h), (0, 0, 255), 2)  # BGR(0,0,255)=红色矩形框

    # 2. 定义主界面区域
    main_ui_top = top_bottom
    main_ui_bottom = min(main_ui_top + 1300, screen_height)
    main_ui_left = top_loc[0]
    main_ui_right = top_loc[0] + top_w
    main_ui_center_x = (main_ui_left + main_ui_right) // 2

    # 绘制主界面区域
    overlay = marked_img.copy()
    cv2.addWeighted(overlay, 0.15, marked_img, 0.85, 0, marked_img)

    # 3. 定位 main.png
    main_template = cv2.imread('main.png', cv2.IMREAD_COLOR)
    if main_template is None:
        raise ValueError("main.png 加载失败")

    main_h, main_w = main_template.shape[:2]
    main_ui_region = screen_img[main_ui_top:main_ui_bottom, main_ui_left:main_ui_right]
    main_res = cv2.matchTemplate(main_ui_region, main_template, cv2.TM_CCOEFF_NORMED)
    _, main_val, _, main_loc = cv2.minMaxLoc(main_res)

    if main_val < 0.9:
        # 如果截图与最新图片相似度≥99% 且 没有找到 main.png，等待 5 秒
        if similarity >= 99.0:
            print(f"截图与最新图片高度相似（{similarity:.2f}%），且没有找到 main.png，等待 5 秒...")
            time.sleep(5)
            
            # 清理内存
            del top_template, main_template, screen_img, marked_img, overlay
            return None
        else:
            raise RuntimeError(f"main.png 匹配失败 (置信度：{main_val:.2f})")

    main_x = main_ui_left + main_loc[0]
    main_y = main_ui_top + main_loc[1]
    main_bottom = main_y + main_h
    main_center_x = main_x + main_w // 2
    main_center = (main_center_x, main_bottom)

    # 标记 main 区域
    cv2.rectangle(marked_img, (main_x, main_y), (main_x + main_w, main_bottom), (0, 255, 0), 2)  # BGR(0,255,0)=绿色矩形框
    cv2.circle(marked_img, main_center, 8, (255, 0, 0), -1)  # BGR(255,0,0)=红色圆点

    # 4. 根据方向线角度确定裁剪区域和绘制方向线
    if main_center_x > main_ui_center_x:  # 右半区
        angle = -150
        line_color = (255, 0, 0)
        crop_left = main_ui_left
        crop_right = main_x - 10
    else:  # 左半区
        angle = -30
        line_color = (0, 0, 255)
        crop_left = main_x + main_w + 10
        crop_right = main_ui_right

    crop_top = main_ui_top
    crop_bottom = main_bottom

    # 确保裁剪区域有效
    if crop_left >= crop_right or crop_top >= crop_bottom:
        raise RuntimeError("裁剪区域无效")

    rad = math.radians(angle)
    
    # 计算方向线与裁剪区域的交点
    # 计算从 main_center 到裁剪区域顶部的距离
    if angle == -150:  # 右半区，向左上
        # 方向线方程：x = main_center_x + t * cos(-150°), y = main_bottom + t * sin(-150°)
        # 与 crop_top 相交：y = crop_top
        t = (crop_top - main_bottom) / math.sin(rad)
        end_x = int(main_center_x + t * math.cos(rad))
        end_y = crop_top
        
        # 检查是否在裁剪区域内
        if end_x < crop_left:
            # 与左边相交
            t = (crop_left - main_center_x) / math.cos(rad)
            end_x = crop_left
            end_y = int(main_bottom + t * math.sin(rad))
        elif end_x > crop_right:
            # 与右边相交（不应该发生）
            t = (crop_right - main_center_x) / math.cos(rad)
            end_x = crop_right
            end_y = int(main_bottom + t * math.sin(rad))
    else:  # 左半区，向右上
        t = (crop_top - main_bottom) / math.sin(rad)
        end_x = int(main_center_x + t * math.cos(rad))
        end_y = crop_top
        
        # 检查是否在裁剪区域内
        if end_x < crop_left:
            # 与左边相交
            t = (crop_left - main_center_x) / math.cos(rad)
            end_x = crop_left
            end_y = int(main_bottom + t * math.sin(rad))
        elif end_x > crop_right:
            # 与右边相交
            t = (crop_right - main_center_x) / math.cos(rad)
            end_x = crop_right
            end_y = int(main_bottom + t * math.sin(rad))
    
    # 确保终点在有效范围内
    end_x = max(crop_left, min(end_x, crop_right))
    end_y = max(crop_top, min(end_y, crop_bottom))
    
    # 计算实际长度并减去 5 像素
    full_length = math.sqrt((end_x - main_center_x) ** 2 + (end_y - main_bottom) ** 2)
    line_length = full_length - 5
    
    # 重新计算端点坐标（缩短 5 像素）
    end_x = int(main_center_x + line_length * math.cos(rad))
    end_y = int(main_bottom + line_length * math.sin(rad))

    cv2.arrowedLine(marked_img, main_center, (end_x, end_y), line_color, 10, tipLength=0.15)  # BGR(255,0,0)=红色箭头 或 BGR(0,0,255)=蓝色箭头

    crop_region = screen_img[crop_top:crop_bottom, crop_left:crop_right]
    cv2.rectangle(marked_img, (crop_left, crop_top), (crop_right, crop_bottom), (255, 255, 0), 2)  # BGR(0,255,255)=青色矩形框

    # 6. 在裁剪区域内匹配 point.png
    point_found = False
    point_center = None
    max_val = 0

    # 7. 在裁剪区域内查找与方向线相交的轮廓
    hsv = cv2.cvtColor(crop_region, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    h_edges = cv2.Canny(h, 50, 150)
    s_edges = cv2.Canny(s, 50, 150)
    v_edges = cv2.Canny(v, 50, 150)
    edges = cv2.bitwise_or(h_edges, s_edges)
    edges = cv2.bitwise_or(edges, v_edges)

    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    edges = cv2.erode(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [cnt + np.array([[crop_left, crop_top]]) for cnt in contours]

    # 方向线参数
    line_start = main_center
    line_end = (end_x, end_y)

    # 创建加宽的方向线掩模
    line_mask = np.zeros_like(marked_img[:, :, 0])
    cv2.line(line_mask, line_start, line_end, 255, 10)  # 白色掩模线

    # 查找所有相交轮廓和特殊点
    intersecting_contours = []
    special_points = []

    point_types = []
    contour_dict = {}

    for cnt in contours:
        contour_mask = np.zeros_like(line_mask)
        cv2.drawContours(contour_mask, [cnt], -1, 255, -1)  # 白色填充轮廓

        intersection = cv2.bitwise_and(contour_mask, line_mask)
        if cv2.countNonZero(intersection) > 0:
            special_point, point_type = find_downward_angle_or_ellipse_top(cnt, line_start, line_end)

            if special_point:
                adjusted_point = adjust_special_point(cnt, special_point)
                if adjusted_point:
                    special_point = adjusted_point

                intersecting_contours.append(cnt)
                special_points.append(special_point)
                point_types.append(point_type)
                contour_dict[tuple(special_point)] = cnt

                cv2.circle(marked_img, special_point, 12, (0, 0, 255), -1)  # BGR(0,0,255)=红色填充圆
                
                # 及时清理临时 mask
                del contour_mask

    # 8. 找到最远的顶点并沿着竖直方向移动到方向线上
    moved_point = None
    max_distance = 0

    # 如果匹配到 point.png，直接使用 point.png 中心
    if point_found:
        moved_point = point_center
        max_distance = math.sqrt((point_center[0] - main_center[0]) ** 2 + (point_center[1] - main_center[1]) ** 2)
        print("使用 point.png 的中心作为目标点")
    elif special_points:
        # 找到距离 main 中心最远的特殊点
        farthest_point, max_dist = calculate_farthest_point_to_main(special_points, main_center)

        if farthest_point:
            # 沿着竖直方向找到与方向线的交点
            intersection_point = find_vertical_intersection(farthest_point, line_start, line_end)

            if intersection_point:
                right_angle_point = intersection_point

                # 查找最近的竖直线段上顶点
                idx = special_points.index(farthest_point)
                farthest_point_type = point_types[idx]

                if farthest_point_type == "corner":
                    cnt = contour_dict.get(tuple(farthest_point))
                    if cnt is not None:
                        nearest_top_point = find_nearest_vertical_segment_top(cnt, farthest_point)
                        if nearest_top_point is not None:
                            # 标记为绿色点
                            cv2.circle(marked_img, nearest_top_point, 8, (0, 255, 0), -1)  # BGR(0,255,0)=绿色圆点
                            cv2.line(marked_img, farthest_point, nearest_top_point, (0, 255, 0), 2, cv2.LINE_AA)  # BGR(0,255,0)=绿色线段

                            # 计算直角点
                            right_angle_point = (farthest_point[0], nearest_top_point[1])

                            # 绘制直角边
                            cv2.line(marked_img, farthest_point, right_angle_point, (255, 0, 0), 2, cv2.LINE_AA)  # BGR(255,0,0)=蓝色线段（水平）
                            cv2.line(marked_img, right_angle_point, nearest_top_point, (255, 0, 0), 2, cv2.LINE_AA)  # BGR(255,0,0)=蓝色线段（垂直）
                            cv2.circle(marked_img, right_angle_point, 6, (255, 255, 0), -1)  # BGR(255,255,0)=黄色圆点

                # 计算交点与直角点的中点作为 moved_point
                moved_point = (
                    (intersection_point[0] + right_angle_point[0]) // 2,
                    (intersection_point[1] + right_angle_point[1]) // 2
                )

                max_distance = math.sqrt(
                    (moved_point[0] - main_center[0]) ** 2 + (moved_point[1] - main_center[1]) ** 2)

                # 绘制移动路径
                cv2.line(marked_img, farthest_point, intersection_point, (0, 255, 0), 2, cv2.LINE_AA)  # BGR(0,255,0)=绿色线段
                cv2.circle(marked_img, intersection_point, 5, (255, 255, 0), -1)  # BGR(255,255,0)=浅蓝色圆点
                cv2.circle(marked_img, moved_point, 5, (0, 255, 255), -1)  # BGR(0,255,255)=黄色圆点

    # 绘制所有相交轮廓
    overlay = marked_img.copy()
    cv2.drawContours(overlay, intersecting_contours, -1, (255, 0, 255), -1)  # BGR(255,0,255)=品红色填充
    cv2.addWeighted(overlay, 0.2, marked_img, 0.8, 0, marked_img)
    cv2.drawContours(marked_img, intersecting_contours, -1, (255, 0, 255), 2)  # BGR(255,0,255)=品红色轮廓线

    # 9. 添加综合标注
    font = cv2.FONT_HERSHEY_SIMPLEX
    info = [
        f"Special Points: {len(special_points)}",
        f"point.png: {'Found' if point_found else 'Not found'} , {max_val:.2f}",
    ]

    if moved_point:
        info.append(f"Max Distance: {max_distance:.1f}px")
        info.append("Moved Point: point.png Center" if point_found else "Moved Point: Calculated Center")

    for i, text in enumerate(info):
        cv2.putText(marked_img, text, (20, 40 + i * 40), font, 0.9, (255, 255, 255), 2)

    # 保存标记后的图像
    main_img = marked_img[main_ui_top:main_ui_bottom, main_ui_left:main_ui_right]
    marked_path = save_marked_image(output_dir, main_img, cycle_count, timestamp)

    if not marked_path:
        raise RuntimeError("无法保存标记截图")

    if moved_point:
        print(f"移动点距离：{max_distance:.1f}像素")
    
    # 清理大型临时对象
    del screen_img, marked_img, overlay, crop_region, hsv, edges, line_mask

    return {
        "top_loc": top_loc,
        "main_ui_rect": (main_ui_left, main_ui_top, main_ui_right, main_ui_bottom),
        "main_loc": (main_x, main_y),
        "main_center": main_center,
        "direction_angle": angle,
        "special_points": special_points,
        "point_types": point_types,
        "original_path": original_path,
        "marked_path": marked_path,
        "moved_point": moved_point,
        "max_distance": max_distance,
        "point_found": point_found
    }

def check_region_stability(top_loc, top_h, top_w):
    """检查 top 下方区域是否稳定"""
    try:
        region_top = top_loc[1] + top_h
        region_bottom = region_top + 700
        region_left = top_loc[0]
        region_right = top_loc[0] + top_w

        # 第一次截图
        screenshot1 = pyautogui.screenshot()
        img1 = np.array(screenshot1)
        region1 = img1[region_top:region_bottom, region_left:region_right]

        time.sleep(0.1)

        # 第二次截图
        screenshot2 = pyautogui.screenshot()
        img2 = np.array(screenshot2)
        region2 = img2[region_top:region_bottom, region_left:region_right]

        # 比较两个区域
        diff = cv2.absdiff(region1, region2)
        change_ratio = np.count_nonzero(diff) / diff.size
        
        # 清理临时对象
        del screenshot1, img1, region1, screenshot2, img2, region2, diff

        return change_ratio < 0.01
    except Exception as e:
        print(f"检查区域稳定性失败：{str(e)}")
        return False

def main_loop():
    """主循环"""
    if not run_start_script():
        print("无法启动 start.py，程序终止")
        return
    
    # 预加载模板图片
    try:
        load_templates()
    except ValueError as e:
        print(f"模板加载失败：{e}")
        return

    output_dir = r"D:\Desktop\t"
    os.makedirs(output_dir, exist_ok=True)
    cycle_count = 0

    while True:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cycle_count += 1
        print(f"\n====== 开始第 {cycle_count} 次循环 ======")

        # 确保鼠标状态正常
        pyautogui.mouseUp()

        try:
            result = analyze_and_mark_screen(output_dir, cycle_count, timestamp)
        except Exception as e:
            print(f"分析屏幕时出错: {e}")
            result = None
            break

        if result:
            # 执行点击操作
            if result.get("moved_point") is not None:
                x = result["max_distance"]
                click_duration = max(0, (x - 50) / 520)  # 确保非负
                print(f"点击持续时间: {click_duration:.3f}秒")
            else:
                click_duration = 0.3

            # 执行点击
            pyautogui.moveTo(result['main_center'][0], result['main_center'][1], duration=0.1)
            time.sleep(0.1)
            pyautogui.mouseDown()
            time.sleep(click_duration)
            pyautogui.mouseUp()

        # 间隔
        time.sleep(0.3)

        # 检查区域稳定性
        if result:
            top_loc = result["top_loc"]
            top_template = cv2.imread('top.png', cv2.IMREAD_COLOR)
            if top_template is not None:
                top_h, top_w = top_template.shape[:2]
                stable = False
                max_attempts = 20
                attempts = 0

                while not stable and attempts < max_attempts:
                    stable = check_region_stability(top_loc, top_h, top_w)
                    if not stable:
                        print(f"区域不稳定，等待重试 ({attempts + 1}/{max_attempts})")
                        time.sleep(0.3)
                        attempts += 1

                if stable:
                    print("区域稳定，继续执行")
                else:
                    print("区域不稳定，但已达到最大重试次数，继续执行")
        else:
            print("没有分析结果，跳过区域稳定性检查")

if __name__ == "__main__":
    main_loop()
    print("\n程序已结束")

