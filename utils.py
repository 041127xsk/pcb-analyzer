"""
工具函数模块
提供坐标转换、单位处理等通用功能
"""

import os
import copy
from pathlib import Path


def ensure_output_dir(output_dir='output'):
    """确保输出目录存在"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return output_dir


def get_gerber_files(input_path):
    """
    获取 Gerber 文件列表
    
    Args:
        input_path: 文件或目录路径
    
    Returns:
        list: Gerber 文件路径列表
    """
    input_path = Path(input_path)
    
    if input_path.is_file():
        return [input_path]
    
    if input_path.is_dir():
        extensions = ['.gbr', '.gb', '.ger', '.gtl', '.gbl', '.gbs', '.gbo', '.gml', '.dxf']
        files = []
        for ext in extensions:
            files.extend(input_path.glob(f'*{ext}'))
            files.extend(input_path.glob(f'*{ext.upper()}'))
        return sorted(files)
    
    return []


def parse_gerber_unit(gerber_path):
    """解析 Gerber 文件的单位"""
    try:
        from gerbonara import GerberFile
        layer = GerberFile.open(str(gerber_path))
        unit = layer.unit
        if hasattr(unit, 'name'):
            return unit.name.lower()
        return 'mm'
    except Exception:
        return 'mm'


def format_coord(value, precision=2):
    """格式化坐标值"""
    return round(float(value), precision)


def format_size(value, precision=3):
    """格式化尺寸值"""
    return round(float(value), precision)


def merge_results(results):
    """
    合并多个提取结果
    
    Args:
        results: 多个焊盘列表
    
    Returns:
        list: 合并后的焊盘列表（去重）
    """
    all_pads = []
    seen = {}
    tolerance = 0.05
    
    for pads in results:
        for pad in pads:
            key = (round(pad['x'] / tolerance), round(pad['y'] / tolerance))
            if key not in seen:
                pad_copy = copy.deepcopy(pad)
                seen[key] = pad_copy
                all_pads.append(pad_copy)
            else:
                existing = seen[key]
                existing['width'] = max(existing['width'], pad.get('width', 0))
                existing['height'] = max(existing['height'], pad.get('height', 0))
    
    return all_pads


def validate_pad(pad):
    """验证焊盘数据完整性"""
    required_fields = ['x', 'y', 'shape']
    for field in required_fields:
        if field not in pad:
            return False
    if not isinstance(pad.get('x'), (int, float)) or not isinstance(pad.get('y'), (int, float)):
        return False
    return True


def get_file_size(filepath):
    """获取文件大小（人类可读）"""
    size = os.path.getsize(filepath)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"