"""
可视化模块 - 增强版
生成焊盘可视化图、Gerber背景图、叠加验证图
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Patch
from pathlib import Path
import numpy as np
import csv
import warnings


class Visualizer:
    """PCB 可视化器"""
    
    COLORS = {
        'circle': '#3498db',
        'rect': '#2ecc71',
        'oval': '#e74c3c',
        'unknown': '#95a5a6',
    }
    
    COMPONENT_COLORS = {
        'Resistor': '#e74c3c',
        'Capacitor': '#3498db',
        'SOP': '#2ecc71',
        'QFP': '#f39c12',
        'QFN': '#9b59b6',
        'BGA': '#1abc9c',
        'Unknown': '#95a5a6'
    }
    
    CONFIDENCE_COLORS = {
        'high': '#2ecc71',
        'medium': '#f1c40f',
        'low': '#e74c3c',
        'unknown': '#95a5a6'
    }
    
    def __init__(self, figsize=(12, 10), dpi=150):
        self.figsize = figsize
        self.dpi = dpi
    
    def _draw_pad(self, ax, pad, color, alpha=0.7, linewidth=0.5):
        """绘制单个焊盘"""
        shape = pad.get('shape', 'unknown')
        x, y = pad['x'], pad['y']
        
        if shape == 'rect':
            w = pad.get('width', 1)
            h = pad.get('height', 1)
            rect = patches.Rectangle(
                (x - w/2, y - h/2), w, h,
                linewidth=linewidth, edgecolor='black',
                facecolor=color, alpha=alpha
            )
            ax.add_patch(rect)
        else:
            r = pad.get('width', 1) / 2
            circle = patches.Circle(
                (x, y), r,
                linewidth=linewidth, edgecolor='black',
                facecolor=color, alpha=alpha
            )
            ax.add_patch(circle)
    
    def _set_plot_limits(self, ax, pads, margin_factor=0.1):
        """设置绘图范围"""
        xs = [p['x'] for p in pads]
        ys = [p['y'] for p in pads]
        
        if xs and ys:
            x_range = max(xs) - min(xs)
            y_range = max(ys) - min(ys)
            margin = max(x_range, y_range) * margin_factor
            ax.set_xlim(min(xs) - margin, max(xs) + margin)
            ax.set_ylim(min(ys) - margin, max(ys) + margin)
    
    def _get_component_color(self, comp_type):
        """获取元件类型颜色"""
        for key, col in self.COMPONENT_COLORS.items():
            if key in comp_type:
                return col
        return '#95a5a6'
    
    def plot_pads(self, pads, output_path, title="PCB Pads", show_shape=True):
        """绘制焊盘散点图"""
        if not pads:
            print("警告: 没有焊盘数据")
            return
        
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        for pad in pads:
            shape = pad.get('shape', 'unknown')
            color = self.COLORS.get(shape, '#95a5a6')
            self._draw_pad(ax, pad, color, alpha=0.7, linewidth=0.5)
        
        self._set_plot_limits(ax, pads)
        
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_title(f"{title} - {len(pads)} pads")
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        print(f"已保存: {output_path}")
        return output_path
    
    def plot_with_clusters(self, pads, clusters, output_path, title="PCB Components"):
        """绘制焊盘并按聚类着色"""
        if not pads:
            return
        
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        pad_cluster_map = {}
        for i, cluster in enumerate(clusters):
            for idx in cluster['indices']:
                pad_cluster_map[idx] = i
        
        for i, pad in enumerate(pads):
            cluster_idx = pad_cluster_map.get(i, -1)
            
            if cluster_idx >= 0:
                comp_type = clusters[cluster_idx].get('component_type', 'Unknown')
                color = self._get_component_color(comp_type)
            else:
                color = '#95a5a6'
            
            self._draw_pad(ax, pad, color, alpha=0.6, linewidth=0.3)
        
        self._set_plot_limits(ax, pads)
        
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_title(f"{title} - {len(pads)} pads, {len(clusters)} components")
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2, linestyle='--')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        print(f"已保存: {output_path}")
        return output_path
    
    def plot_overlay(self, gerber_path, pads, output_path, title="Gerber Overlay"):
        """绘制 Gerber 渲染 + 焊盘叠加图"""
        from gerbonara import GerberFile
        
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            
            try:
                layer = GerberFile.open(str(gerber_path))
                bbox = layer.bounding_box()
            except Exception as e:
                print(f"渲染错误: {e}")
                return None
        
        fig, ax = plt.subplots(figsize=(10, 10), dpi=self.dpi)
        
        ax.set_xlim(bbox[0][0], bbox[1][0])
        ax.set_ylim(bbox[0][1], bbox[1][1])
        
        for obj in layer.objects:
            if type(obj).__name__ == 'Line':
                ax.plot([obj.p1[0], obj.p2[0]], [obj.p1[1], obj.p2[1]], 
                       'k-', linewidth=0.2, alpha=0.5)
            elif type(obj).__name__ == 'Flash':
                x, y = obj.x, obj.y
                apt = obj.aperture
                apt_type = type(apt).__name__
                
                if apt_type == 'CircleAperture':
                    r = apt.diameter / 2
                    circle = plt.Circle((x, y), r, color='#666666', alpha=0.5, fill=True)
                    ax.add_patch(circle)
                elif apt_type == 'RectangleAperture':
                    w, h = apt.w, apt.h
                    rect = patches.Rectangle((x-w/2, y-h/2), w, h, 
                                            color='#666666', alpha=0.5, fill=True)
                    ax.add_patch(rect)
        
        for pad in pads:
            ax.plot(pad['x'], pad['y'], 'o', color='red', markersize=3,
                   markeredgecolor='darkred', markeredgewidth=0.5, alpha=0.9)
        
        ax.set_aspect('equal')
        ax.axis('off')
        ax.invert_yaxis()
        
        plt.tight_layout(pad=0)
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"已保存: {output_path}")
        return output_path
    
    def generate_pcb_image(self, gerber_path, output_path, dpi=300):
        """
        生成 PCB 图像 (pcb.png)
        
        Args:
            gerber_path: Gerber 文件路径
            output_path: 输出 PNG 路径
            dpi: 输出图像 DPI
        
        Returns:
            dict: 图像信息 (width, height, bbox, unit)
        """
        from gerbonara import GerberFile
        
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            
            try:
                layer = GerberFile.open(str(gerber_path))
                bbox = layer.bounding_box()
                unit = layer.unit
                unit_name = str(unit).lower() if unit else 'mm'
            except Exception as e:
                print(f"渲染错误: {e}")
                return None
        
        width_mm = bbox[1][0] - bbox[0][0]
        height_mm = bbox[1][1] - bbox[0][1]
        
        width_px = int(width_mm * dpi / 25.4)
        height_px = int(height_mm * dpi / 25.4)
        
        fig_size = (width_px / dpi, height_px / dpi)
        
        fig, ax = plt.subplots(figsize=fig_size, dpi=dpi)
        
        ax.set_xlim(bbox[0][0], bbox[1][0])
        ax.set_ylim(bbox[0][1], bbox[1][1])
        
        obj_count = 0
        for obj in layer.objects:
            if type(obj).__name__ == 'Line':
                ax.plot([obj.p1[0], obj.p2[0]], [obj.p1[1], obj.p2[1]], 
                       'k-', linewidth=0.15, alpha=0.8)
                obj_count += 1
            elif type(obj).__name__ == 'Flash':
                x, y = obj.x, obj.y
                apt = obj.aperture
                apt_type = type(apt).__name__
                
                if apt_type == 'CircleAperture':
                    r = apt.diameter / 2
                    circle = plt.Circle((x, y), r, color='#333333', alpha=0.9, fill=True)
                    ax.add_patch(circle)
                elif apt_type == 'RectangleAperture':
                    w, h = apt.w, apt.h
                    rect = patches.Rectangle((x-w/2, y-h/2), w, h, 
                                            color='#333333', alpha=0.9, fill=True)
                    ax.add_patch(rect)
                obj_count += 1
        
        ax.set_aspect('equal')
        ax.axis('off')
        ax.invert_yaxis()
        ax.margins(0)
        
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight',
                   pad_inches=0, facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"已生成 PCB 图像: {output_path} ({width_px}x{height_px}px)")
        
        return {
            'width_px': width_px,
            'height_px': height_px,
            'width_mm': width_mm,
            'height_mm': height_mm,
            'bbox': bbox,
            'unit': unit_name,
            'obj_count': obj_count
        }
    
    def create_verification_overlay(self, pcb_image_path, pads_csv_path, 
                                     output_path, marker_size=4):
        """
        创建验证叠加图
        读取 pads.csv，将坐标叠加到 PCB 图像上
        
        Args:
            pcb_image_path: PCB 背景图路径
            pads_csv_path: 焊盘坐标 CSV 路径
            output_path: 输出叠加图路径
            marker_size: 红点大小
        
        Returns:
            dict: 叠加结果
        """
        from PIL import Image
        
        try:
            img = Image.open(pcb_image_path)
            width_px, height_px = img.size
        except Exception as e:
            print(f"无法读取图像: {e}")
            return None
        
        pads = []
        try:
            with open(pads_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pads.append({
                        'x': float(row['x']),
                        'y': float(row['y']),
                        'shape': row.get('shape', 'unknown')
                    })
        except Exception as e:
            print(f"无法读取 CSV: {e}")
            return None
        
        if not pads:
            print("警告: CSV 中没有焊盘数据")
            return None
        
        xs = [p['x'] for p in pads]
        ys = [p['y'] for p in pads]
        
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        
        x_range = x_max - x_min
        y_range = y_max - y_min
        margin = max(x_range, y_range) * 0.1
        
        gerber_x_min = x_min - margin
        gerber_x_max = x_max + margin
        gerber_y_min = y_min - margin
        gerber_y_max = y_max + margin
        
        fig, ax = plt.subplots(figsize=(width_px/100, height_px/100), dpi=100)
        ax.imshow(img)
        
        for pad in pads:
            px = (pad['x'] - gerber_x_min) / (gerber_x_max - gerber_x_min) * width_px
            py = (1 - (pad['y'] - gerber_y_min) / (gerber_y_max - gerber_y_min)) * height_px
            
            ax.plot(px, py, 'o', color='red', markersize=marker_size,
                   markeredgecolor='darkred', markeredgewidth=0.5, alpha=0.9)
        
        ax.set_xlim(0, width_px)
        ax.set_ylim(height_px, 0)
        ax.set_aspect('equal')
        ax.axis('off')
        
        plt.tight_layout(pad=0)
        plt.savefig(output_path, dpi=100, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"已保存叠加图: {output_path}")
        
        return {
            'pads_count': len(pads),
            'image_size': (width_px, height_px)
        }

    def plot_with_confidence(self, pads, clusters, output_path, title="Component Recognition Confidence"):
        """
        按置信度着色绘制元件识别图
        
        高置信度 >= 80: 绿色
        中置信度 60-79: 黄色
        低置信度 < 60: 红色
        Unknown: 灰色
        """
        if not pads or not clusters:
            return
        
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        
        pad_cluster_map = {}
        for i, cluster in enumerate(clusters):
            for idx in cluster.get('indices', []):
                pad_cluster_map[idx] = i
        
        for i, pad in enumerate(pads):
            cluster_idx = pad_cluster_map.get(i, -1)
            color = '#cccccc'
            
            if cluster_idx >= 0:
                conf = float(clusters[cluster_idx].get('confidence', 0))
                if conf >= 80:
                    color = self.CONFIDENCE_COLORS['high']
                elif conf >= 60:
                    color = self.CONFIDENCE_COLORS['medium']
                elif conf > 0:
                    color = self.CONFIDENCE_COLORS['low']
                else:
                    color = self.CONFIDENCE_COLORS['unknown']
            
            self._draw_pad(ax, pad, color, alpha=0.7, linewidth=0.3)
        
        self._set_plot_limits(ax, pads, margin_factor=0.05)
        
        ax.set_aspect('equal')
        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_title(title)
        ax.grid(True, alpha=0.2)
        
        legend_elements = [
            Patch(facecolor=self.CONFIDENCE_COLORS['high'], label='High confidence (>=80)'),
            Patch(facecolor=self.CONFIDENCE_COLORS['medium'], label='Medium confidence (60-79)'),
            Patch(facecolor=self.CONFIDENCE_COLORS['low'], label='Low confidence (<60)'),
            Patch(facecolor=self.CONFIDENCE_COLORS['unknown'], label='Unknown / Unrecognized'),
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        print(f"已保存置信度图: {output_path}")
        return output_path


def run_verification(input_dir, output_dir='output'):
    """
    一键运行可视化验证模块
    
    Args:
        input_dir: Gerber 文件目录
        output_dir: 输出目录
    
    Returns:
        dict: 输出文件路径
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    viz = Visualizer(dpi=200)
    
    results = {}
    
    # 查找 Gerber 文件
    gerber_files = {
        'mask1': 'mask1.gbr',
        'mask2': 'mask2.gbr', 
        'top_copper': 'lay1.gbr',
        'bottom_copper': 'lay4.gbr'
    }
    
    gerber_path = None
    for key, name in gerber_files.items():
        candidate = input_dir / name
        if candidate.exists():
            gerber_path = candidate
            print(f"使用 Gerber 文件: {name}")
            break
    
    if not gerber_path:
        # 查找任意 gbr 文件
        gbr_files = list(input_dir.glob('*.gbr'))
        if gbr_files:
            gerber_path = gbr_files[0]
            print(f"使用 Gerber 文件: {gerber_path.name}")
        else:
            print("错误: 没有找到 Gerber 文件")
            return results
    
    # 1. 生成 PCB 图像
    pcb_image_path = output_dir / 'pcb.png'
    pcb_info = viz.generate_pcb_image(gerber_path, pcb_image_path, dpi=200)
    results['pcb_png'] = str(pcb_image_path)
    
    # 2. 读取 pads.csv
    pads_csv_path = output_dir / 'pads.csv'
    if not pads_csv_path.exists():
        print(f"警告: {pads_csv_path} 不存在")
        return results
    
    # 3. 创建叠加图
    overlay_path = output_dir / 'overlay.png'
    overlay_info = viz.create_verification_overlay(
        pcb_image_path, pads_csv_path, overlay_path, marker_size=3
    )
    results['overlay_png'] = str(overlay_path)
    
    print(f"\n验证完成!")
    print(f"  - PCB 图像: {pcb_image_path}")
    print(f"  - 焊盘叠加: {overlay_path}")
    if overlay_info:
        print(f"  - 焊盘数量: {overlay_info['pads_count']}")
    
    return results


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        run_verification(sys.argv[1])
    else:
        print("用法: python verify_overlay.py <gerber_directory>")