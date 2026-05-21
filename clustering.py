"""
焊盘聚类与元件识别模块
基于坐标进行聚类，识别元件封装类型
支持可插拔的封装库识别引擎
"""

import numpy as np
from pathlib import Path
from collections import deque

try:
    from scipy.spatial import cKDTree
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

try:
    from scipy.spatial import cKDTree
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


class PadClustering:
    """焊盘聚类器"""
    
    _ALL_CSV_FIELDS = [
        'component_type', 'confidence', 'category', 'package_id',
        'mount_type', 'has_drill', 'drill_count', 'plated_drill_count',
        'pad_count', 'center_x', 'center_y',
        'x_min', 'x_max', 'y_min', 'y_max'
    ]
    
    def __init__(self, threshold=2.0, verbose=True, library_system=None, drills=None):
        """
        初始化聚类器
        
        Args:
            threshold: 聚类距离阈值 (mm)
            verbose: 是否打印详细信息
            library_system: 可选的 ComponentLibrarySystem 实例
            drills: 可选的钻孔列表 (来自 DrillExtractor)
        """
        self.threshold = threshold
        self.verbose = verbose
        self.clusters = []
        self.pads = []
        self.library_system = library_system
        self.drills = drills or []
        self.recognition_engine = None
        self._use_new_engine = False
        self._types_assigned = False
        
        if library_system is not None:
            from package_library import RecognitionEngine
            self.recognition_engine = RecognitionEngine(library_system)
            self._use_new_engine = True
    
    def fit(self, pads):
        """
        对焊盘进行聚类
        
        Args:
            pads: 焊盘列表
        
        Returns:
            list: 聚类结果列表
        """
        self.pads = pads
        self._types_assigned = False
        
        if not pads:
            return []
        
        coords = np.array([[p['x'], p['y']] for p in pads])
        n = len(coords)
        
        visited = [False] * n
        self.clusters = []
        
        tree = cKDTree(coords) if _HAS_SCIPY else None
        
        for i in range(n):
            if visited[i]:
                continue
            
            cluster = self._bfs_cluster(i, coords, visited, tree)
            
            cluster_info = self._compute_cluster_info(cluster, coords)
            self.clusters.append(cluster_info)
        
        if self.verbose:
            print(f"聚类完成: 识别出 {len(self.clusters)} 个区域/元件")
        
        return self.clusters
    
    def _bfs_cluster(self, start_idx, coords, visited, tree=None):
        """广度优先搜索聚类（KD-Tree 优化）"""
        cluster = [start_idx]
        queue = deque([start_idx])
        visited[start_idx] = True
        
        if tree is not None:
            while queue:
                current = queue.popleft()
                for i in tree.query_ball_point(coords[current], self.threshold):
                    if not visited[i]:
                        visited[i] = True
                        cluster.append(i)
                        queue.append(i)
        else:
            while queue:
                current = queue.popleft()
                for i in range(len(coords)):
                    if not visited[i]:
                        dist = np.linalg.norm(coords[current] - coords[i])
                        if dist < self.threshold:
                            visited[i] = True
                            cluster.append(i)
                            queue.append(i)
        
        return cluster
    
    def _compute_cluster_info(self, indices, coords):
        """计算聚类信息"""
        cluster_coords = coords[indices]
        
        info = {
            'indices': indices,
            'count': len(indices),
            'x_min': cluster_coords[:, 0].min(),
            'x_max': cluster_coords[:, 0].max(),
            'y_min': cluster_coords[:, 1].min(),
            'y_max': cluster_coords[:, 1].max(),
            'center_x': cluster_coords[:, 0].mean(),
            'center_y': cluster_coords[:, 1].mean(),
            'width': cluster_coords[:, 0].max() - cluster_coords[:, 0].min(),
            'height': cluster_coords[:, 1].max() - cluster_coords[:, 1].min()
        }
        
        if self.drills:
            drill_info = self._match_drills_to_cluster(indices)
            info.update(drill_info)
        
        return info
    
    def _match_drills_to_cluster(self, indices, tolerance=0.5):
        """将钻孔匹配到聚类"""
        cluster_drills = []
        
        for idx in indices:
            pad = self.pads[idx]
            pad_x, pad_y = pad['x'], pad['y']
            
            for drill in self.drills:
                dist = ((pad_x - drill['x']) ** 2 + (pad_y - drill['y']) ** 2) ** 0.5
                
                if dist < tolerance:
                    cluster_drills.append(drill)
                    break
        
        has_drill = len(cluster_drills) > 0
        plated_count = sum(1 for d in cluster_drills if d.get('plated') == 'plated')
        
        return {
            'has_drill': has_drill,
            'drill_count': len(cluster_drills),
            'plated_drill_count': plated_count,
            'mount_type': 'through-hole' if has_drill else 'smd'
        }
    
    def guess_component_type(self, cluster):
        """
        根据焊盘数量和分布推测元件封装类型
        
        Args:
            cluster: 聚类信息
        
        Returns:
            str 或 dict: 推测的封装类型
        """
        if self._use_new_engine and self.recognition_engine:
            result = self.recognition_engine.recognize(cluster, self.pads)
            return {
                'component_type': result.component_type,
                'confidence': result.confidence,
                'category': result.category,
                'package_id': result.matched_package_id or '',
            }
        
        return self._guess_component_type_legacy(cluster)
    
    def _guess_component_type_legacy(self, cluster):
        """原有硬编码识别逻辑（向后兼容）"""
        count = cluster['count']
        width = cluster['width']
        height = cluster['height']
        
        aspect = max(width, height) / min(width, height) if min(width, height) > 0 else 1
        
        if count == 1:
            return 'Unknown'
        if count == 2:
            if aspect > 4:
                return 'Resistor 0402'
            elif aspect > 2.5:
                return 'Resistor/Capacitor 0603'
            elif aspect > 1.5:
                return 'Resistor/Capacitor 0805'
            else:
                return 'Resistor/Capacitor'
        if count == 3:
            return 'Unknown'
        
        if 4 <= count <= 6:
            return 'SOP/TSOP'
        
        if count == 8:
            if aspect > 2:
                return 'SOP/TSOP'
            return 'QFN'
        if count == 14:
            return 'SOP/TSOP'
        if count == 16:
            if aspect > 1.5:
                return 'QFP-16'
            return 'QFN'
        if count == 20:
            return 'QFN'
        if count == 24:
            return 'QFP-24'
        if count == 32:
            return 'QFP-32'
        if count == 44:
            return 'QFP-44'
        if count == 48:
            return 'QFP-48'
        if count == 64:
            return 'QFP-64'
        
        if 9 <= count <= 19:
            return 'QFN'
        if count > 20:
            if aspect > 1.5:
                return 'BGA'
            return 'QFN'
        
        return 'Unknown'
    
    def add_component_type(self):
        """为每个聚类添加元件类型"""
        if self._types_assigned:
            return self.clusters
        
        for cluster in self.clusters:
            result = self.guess_component_type(cluster)
            if isinstance(result, dict):
                cluster['component_type'] = result['component_type']
                cluster['confidence'] = result['confidence']
                cluster['category'] = result['category']
                cluster['package_id'] = result['package_id']
            else:
                cluster['component_type'] = result
        
        self._types_assigned = True
        return self.clusters
    
    def save_csv(self, output_path):
        """保存聚类结果到 CSV"""
        import csv
        
        self.add_component_type()
        
        has_drills = bool(self.drills)
        has_new = self._use_new_engine
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self._ALL_CSV_FIELDS, extrasaction='ignore')
            writer.writeheader()
            
            for c in self.clusters:
                row = {
                    'component_type': c['component_type'],
                    'pad_count': c['count'],
                    'center_x': round(c['center_x'], 2),
                    'center_y': round(c['center_y'], 2),
                    'x_min': round(c['x_min'], 2),
                    'x_max': round(c['x_max'], 2),
                    'y_min': round(c['y_min'], 2),
                    'y_max': round(c['y_max'], 2),
                }
                if has_new:
                    row['confidence'] = round(c.get('confidence', 0), 1)
                    row['category'] = c.get('category', 'unknown')
                    row['package_id'] = c.get('package_id', '')
                if has_drills:
                    row['mount_type'] = c.get('mount_type', 'smd')
                    row['has_drill'] = c.get('has_drill', False)
                    row['drill_count'] = c.get('drill_count', 0)
                    row['plated_drill_count'] = c.get('plated_drill_count', 0)
                writer.writerow(row)
        
        if self.verbose:
            print(f"已保存: {output_path}")
        
        return output_path
    
    def get_summary(self):
        """获取聚类统计摘要"""
        if not self.clusters:
            return {}
        
        types = {}
        for c in self.clusters:
            t = c.get('component_type', 'Unknown')
            types[t] = types.get(t, 0) + 1
        
        return types


def cluster_pads(pads, threshold=2.0, output_dir='output', verbose=True, drills=None):
    """
    一键聚类分析
    
    Args:
        pads: 焊盘列表
        output_dir: 输出目录
        threshold: 聚类距离阈值
        verbose: 是否打印详细信息
        drills: 可选的钻孔列表
    
    Returns:
        dict: 聚类结果 {'clusters': list, 'csv_path': str}
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    clusterer = PadClustering(threshold=threshold, verbose=verbose, drills=drills)
    clusterer.fit(pads)
    
    csv_path = output_dir / 'components.csv'
    clusterer.save_csv(csv_path)
    
    return {
        'clusters': clusterer.clusters,
        'csv_path': str(csv_path),
        'summary': clusterer.get_summary()
    }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        # 测试: 加载 CSV 并聚类
        import csv
        
        with open(sys.argv[1], 'r') as f:
            reader = csv.DictReader(f)
            pads = list(reader)
        
        for p in pads:
            p['x'] = float(p['x'])
            p['y'] = float(p['y'])
        
        result = cluster_pads(pads)
        print(f"\n聚类完成: {len(result['clusters'])} 个元件")
        print(f"统计: {result['summary']}")
    else:
        print("用法: python clustering.py <pads.csv>")