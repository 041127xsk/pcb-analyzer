"""
Excellon 钻孔文件解析模块
使用 gerbonara 库解析 Excellon 钻孔文件，提取钻孔坐标和孔径信息
"""

import warnings
from pathlib import Path

from gerbonara import ExcellonFile
from gerbonara.excellon import Flash, Line


class DrillExtractor:
    """Excellon 钻孔提取器"""
    
    EXCELLON_EXTENSIONS = ['.drl', '.ncd', '.xln', '.txt', '.drd', '.dri', '.nc']
    
    def __init__(self, verbose=True):
        """
        初始化提取器
        
        Args:
            verbose: 是否打印详细信息
        """
        self.verbose = verbose
        self.drills = []
        
    def extract_from_file(self, excellon_path, plated=None):
        """
        从单个 Excellon 文件提取钻孔
        
        Args:
            excellon_path: Excellon 文件路径
            plated: 是否镀通孔 (True/False/None=自动)
        
        Returns:
            list: 钻孔列表
        """
        if self.verbose:
            print(f"  解析钻孔: {Path(excellon_path).name}")
        
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            
            try:
                drill_file = ExcellonFile.open(str(excellon_path), plated=plated)
            except Exception as e:
                if self.verbose:
                    print(f"    错误: {e}")
                return []
        
        drills = []
        
        for obj in drill_file.objects:
            if isinstance(obj, Flash):
                drill = self._extract_drill_flash(obj, plated)
                if drill:
                    drills.append(drill)
            elif isinstance(obj, Line):
                slot_drills = self._extract_drill_slot(obj, plated)
                drills.extend(slot_drills)
        
        if self.verbose:
            print(f"    提取: {len(drills)} 个钻孔")
        
        return drills
    
    def _extract_drill_flash(self, flash_obj, plated_override=None):
        """提取单个圆形钻孔"""
        x = flash_obj.x
        y = flash_obj.y
        tool = flash_obj.tool
        
        diameter = tool.diameter if tool else 0
        plated = self._get_plating_status(flash_obj, plated_override)
        
        return {
            'x': x,
            'y': y,
            'diameter': diameter,
            'plated': plated,
            'type': 'round'
        }
    
    def _extract_drill_slot(self, line_obj, plated_override=None):
        """提取槽孔（长圆孔）"""
        slots = []
        
        x1, y1 = line_obj.x1, line_obj.y1
        x2, y2 = line_obj.x2, line_obj.y2
        tool = line_obj.tool
        
        diameter = tool.diameter if tool else 0
        plated = self._get_plating_status(line_obj, plated_override)
        
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        slots.append({
            'x': center_x,
            'y': center_y,
            'diameter': diameter,
            'length': length + diameter,
            'plated': plated,
            'type': 'slot',
            'x1': x1,
            'y1': y1,
            'x2': x2,
            'y2': y2
        })
        
        return slots
    
    def _get_plating_status(self, obj, plated_override=None):
        """获取镀层状态"""
        if plated_override is not None:
            return 'plated' if plated_override else 'nonplated'
        
        plated = getattr(obj, 'plated', None)
        
        if plated is True:
            return 'plated'
        elif plated is False:
            return 'nonplated'
        else:
            return 'unknown'
    
    def extract_from_dir(self, gerber_dir):
        """
        从目录提取所有钻孔
        
        Args:
            gerber_dir: Gerber/Excellon 文件目录
        
        Returns:
            list: 所有钻孔列表
        """
        gerber_dir = Path(gerber_dir)
        
        if not gerber_dir.exists():
            raise FileNotFoundError(f"目录不存在: {gerber_dir}")
        
        drill_files = self._collect_excellon_files(gerber_dir)
        
        if not drill_files:
            if self.verbose:
                print("未找到 Excellon 钻孔文件")
            return []
        
        if self.verbose:
            print(f"找到 {len(drill_files)} 个钻孔文件")
        
        all_drills = []
        
        for df in drill_files:
            plated = self._infer_plating_from_filename(df.name)
            drills = self.extract_from_file(df, plated=plated)
            all_drills.extend(drills)
        
        self.drills = self._merge_drills(all_drills)
        
        if self.verbose:
            print(f"\n总计提取: {len(self.drills)} 个钻孔")
            
            plated_count = sum(1 for d in self.drills if d['plated'] == 'plated')
            nonplated_count = sum(1 for d in self.drills if d['plated'] == 'nonplated')
            unknown_count = sum(1 for d in self.drills if d['plated'] == 'unknown')
            print(f"镀通孔: {plated_count}, 非镀通孔: {nonplated_count}, 未知: {unknown_count}")
        
        return self.drills
    
    def _collect_excellon_files(self, directory):
        """收集 Excellon 文件"""
        files = []
        
        for ext in self.EXCELLON_EXTENSIONS:
            files.extend(directory.glob(f'*{ext}'))
            files.extend(directory.glob(f'*{ext.upper()}'))
        
        return sorted(set(files))
    
    def _infer_plating_from_filename(self, filename):
        """从文件名推断镀层状态"""
        name_lower = filename.lower()
        
        nonplated_keywords = ['npth', 'nonplated', 'np', 'slot']
        plated_keywords = ['pth', 'plated', 'drill']
        
        for kw in nonplated_keywords:
            if kw in name_lower:
                return False
        
        for kw in plated_keywords:
            if kw in name_lower:
                return True
        
        return None
    
    def _merge_drills(self, drills, tolerance=0.05):
        """合并重复钻孔"""
        seen = {}
        merged = []
        
        for drill in drills:
            key = (round(drill['x'] / tolerance), round(drill['y'] / tolerance))
            
            if key not in seen:
                seen[key] = drill
                merged.append(drill)
        
        return merged
    
    def save_csv(self, output_path):
        """保存钻孔到 CSV"""
        import csv
        
        fieldnames = ['x', 'y', 'diameter', 'plated', 'type']
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.drills)
        
        if self.verbose:
            print(f"已保存钻孔: {output_path}")
        
        return output_path
    
    def get_through_hole_pads(self, pads, tolerance=0.5):
        """
        将钻孔与焊盘匹配，识别通孔焊盘
        
        Args:
            pads: 焊盘列表 (来自 GerberExtractor)
            tolerance: 匹配容差 (mm)
        
        Returns:
            list: 增强后的焊盘列表，包含钻孔信息
        """
        enhanced_pads = []
        
        for pad in pads:
            pad_copy = pad.copy()
            pad_copy['has_drill'] = False
            pad_copy['drill_diameter'] = None
            pad_copy['plated'] = None
            
            for drill in self.drills:
                dist = ((pad['x'] - drill['x']) ** 2 + (pad['y'] - drill['y']) ** 2) ** 0.5
                
                if dist < tolerance:
                    pad_copy['has_drill'] = True
                    pad_copy['drill_diameter'] = drill['diameter']
                    pad_copy['plated'] = drill['plated']
                    break
            
            enhanced_pads.append(pad_copy)
        
        through_hole_count = sum(1 for p in enhanced_pads if p['has_drill'])
        
        if self.verbose:
            print(f"通孔焊盘: {through_hole_count}/{len(enhanced_pads)}")
        
        return enhanced_pads


def extract_drills(input_path, output_dir='output', verbose=True):
    """
    一键提取钻孔
    
    Args:
        input_path: Excellon 文件或目录
        output_dir: 输出目录
        verbose: 是否打印详细信息
    
    Returns:
        dict: 提取结果 {'drills': list, 'csv_path': str}
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extractor = DrillExtractor(verbose=verbose)
    
    if input_path.is_file():
        drills = extractor.extract_from_file(input_path)
        extractor.drills = drills
    elif input_path.is_dir():
        extractor.extract_from_dir(input_path)
    else:
        raise ValueError(f"无效路径: {input_path}")
    
    if extractor.drills:
        csv_path = output_dir / 'drills.csv'
        extractor.save_csv(csv_path)
        return {
            'drills': extractor.drills,
            'csv_path': str(csv_path)
        }
    else:
        return {
            'drills': [],
            'csv_path': None
        }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        result = extract_drills(sys.argv[1])
        if result['drills']:
            print(f"\n提取完成: {len(result['drills'])} 个钻孔")
        else:
            print("\n未找到钻孔文件")
    else:
        print("用法: python drill_extractor.py <excellon_file_or_dir>")
