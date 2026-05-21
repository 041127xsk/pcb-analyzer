"""
Gerber 解析与焊盘提取模块
使用 gerbonara 库解析 Gerber 文件，提取 Flash 焊盘
"""

import csv
import copy
import warnings
from pathlib import Path

from gerbonara import GerberFile
from gerbonara.graphic_objects import Flash
from gerbonara.apertures import CircleAperture, RectangleAperture, ObroundAperture


class GerberExtractor:
    """Gerber 焊盘提取器"""
    
    PRIORITY_LAYERS = [
        'mask1.gbr', 'mask2.gbr',
        'via_plugging.gbr',
        'drilldrw.gbr',
        'lay1.gbr', 'lay4.gbr',
        'lay2.gbr', 'lay3.gbr',
        'silk1.gbr', 'silk2.gbr',
    ]
    
    GERBER_EXTENSIONS = ['.gbr', '.gb', '.ger', '.gtl', '.gbl', '.gbs', '.gbo', '.gml']
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.pads = []
        
    def extract_from_file(self, gerber_path):
        """从单个 Gerber 文件提取焊盘"""
        if self.verbose:
            print(f"  解析: {Path(gerber_path).name}")
        
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            
            try:
                layer = GerberFile.open(str(gerber_path))
            except Exception as e:
                if self.verbose:
                    print(f"    错误: {e}")
                return []
        
        pads = []
        
        for obj in layer.objects:
            if not isinstance(obj, Flash):
                continue
                
            pad = self._extract_single_pad(obj)
            if pad:
                pads.append(pad)
        
        if self.verbose:
            print(f"    提取: {len(pads)} 个焊盘")
        
        return pads
    
    def _extract_single_pad(self, flash_obj):
        """提取单个 Flash 焊盘"""
        x = flash_obj.x
        y = flash_obj.y
        apt = flash_obj.aperture
        
        if isinstance(apt, CircleAperture):
            shape = 'circle'
            width = height = apt.diameter
        elif isinstance(apt, RectangleAperture):
            shape = 'rect'
            width = apt.w
            height = apt.h
        elif isinstance(apt, ObroundAperture):
            shape = 'oval'
            width = apt.w
            height = apt.h
        else:
            shape = 'unknown'
            diameter = getattr(apt, 'diameter', None)
            if diameter:
                width = height = diameter
            else:
                size = getattr(apt, 'size', None)
                if size:
                    width = size[0]
                    height = size[1] if len(size) > 1 else width
                else:
                    width = height = 0
        
        return {
            'x': x,
            'y': y,
            'shape': shape,
            'width': width,
            'height': height
        }
    
    def extract_from_dir(self, gerber_dir, priority=True):
        """
        从目录提取所有焊盘
        
        Args:
            gerber_dir: Gerber 文件目录
            priority: 是否按优先级顺序处理
        
        Returns:
            list: 所有焊盘列表
        """
        gerber_dir = Path(gerber_dir)
        
        if not gerber_dir.exists():
            raise FileNotFoundError(f"目录不存在: {gerber_dir}")
        
        # 收集所有 Gerber 文件
        gbr_files = self._collect_gerber_files(gerber_dir)
        
        if not gbr_files:
            raise ValueError(f"目录中没有 Gerber 文件: {gerber_dir}")
        
        if self.verbose:
            print(f"找到 {len(gbr_files)} 个 Gerber 文件")
        
        all_pads = []
        
        if priority:
            # 按优先级顺序处理
            priority_files = set(self.PRIORITY_LAYERS)
            priority_list = []
            others = []
            
            for gf in gbr_files:
                if gf.name in priority_files:
                    priority_list.append((self.PRIORITY_LAYERS.index(gf.name), gf))
                else:
                    others.append(gf)
            
            priority_list.sort(key=lambda x: x[0])
            gbr_files = [f for _, f in priority_list] + others
        
        for gf in gbr_files:
            pads = self.extract_from_file(gf)
            all_pads.extend(pads)
        
        # 合并重复焊盘
        self.pads = self._merge_pads(all_pads)
        
        if self.verbose:
            print(f"\n总计提取: {len(self.pads)} 个焊盘")
            
            # 形状统计
            shapes = {}
            for p in self.pads:
                shapes[p['shape']] = shapes.get(p['shape'], 0) + 1
            print(f"形状分布: {shapes}")
        
        return self.pads
    
    def _collect_gerber_files(self, directory):
        """收集 Gerber 文件"""
        extensions = ['.gbr', '.gb', '.ger', '.gtl', '.gbl', '.gbs', '.gbo', '.gml']
        files = []
        
        for ext in extensions:
            files.extend(directory.glob(f'*{ext}'))
            files.extend(directory.glob(f'*{ext.upper()}'))
        
        return sorted(set(files))
    
    def _merge_pads(self, pads, tolerance=0.05):
        """合并重复焊盘"""
        seen = {}
        merged = []
        
        for pad in pads:
            key = (round(pad['x'] / tolerance), round(pad['y'] / tolerance))
            
            if key in seen:
                existing = seen[key]
                existing['width'] = max(existing['width'], pad.get('width', 0))
                existing['height'] = max(existing['height'], pad.get('height', 0))
            else:
                pad_copy = copy.deepcopy(pad)
                seen[key] = pad_copy
                merged.append(pad_copy)
        
        return merged
    
    def save_csv(self, output_path):
        """保存焊盘到 CSV"""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['x', 'y', 'shape', 'width', 'height'])
            writer.writeheader()
            writer.writerows(self.pads)
        
        if self.verbose:
            print(f"已保存: {output_path}")
        
        return output_path


def extract_pads(input_path, output_dir='output', verbose=True):
    """
    一键提取焊盘
    
    Args:
        input_path: Gerber 文件或目录
        output_dir: 输出目录
        verbose: 是否打印详细信息
    
    Returns:
        dict: 提取结果 {'pads': list, 'csv_path': str}
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extractor = GerberExtractor(verbose=verbose)
    
    if input_path.is_file():
        pads = extractor.extract_from_file(input_path)
        extractor.pads = pads
    elif input_path.is_dir():
        extractor.extract_from_dir(input_path)
    else:
        raise ValueError(f"无效路径: {input_path}")
    
    csv_path = output_dir / 'pads.csv'
    extractor.save_csv(csv_path)
    
    return {
        'pads': extractor.pads,
        'csv_path': str(csv_path)
    }


if __name__ == '__main__':
    # 测试
    import sys
    
    if len(sys.argv) > 1:
        result = extract_pads(sys.argv[1])
        print(f"\n提取完成: {len(result['pads'])} 个焊盘")
    else:
        print("用法: python extractor.py <gerber_file_or_dir>")