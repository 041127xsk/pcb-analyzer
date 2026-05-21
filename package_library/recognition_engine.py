"""
识别引擎模块

基于特征的封装匹配算法
"""

from typing import List, Tuple, Optional, Dict, Any

from .models import PackageDefinition, ClusterFeatures, RecognitionResult
from .library_system import ComponentLibrarySystem


class RecognitionEngine:
    """
    识别引擎 — 基于特征的封装匹配
    
    使用多维度特征匹配算法计算置信度
    
    Attributes:
        library: 封装库系统实例
        W_PAD_COUNT: 焊盘数量权重
        W_SIZE: 尺寸权重
        W_ASPECT: 长宽比权重
        W_PITCH: 间距权重
        W_SHAPE: 焊盘形状权重
        W_LAYOUT: 布局模式权重
        SIZE_TOLERANCE: 尺寸容差 (mm)
        PAD_COUNT_TOLERANCE: 焊盘数量容差
    """

    # 置信度权重
    W_PAD_COUNT = 0.30
    W_SIZE = 0.25
    W_ASPECT = 0.15
    W_PITCH = 0.15
    W_SHAPE = 0.10
    W_LAYOUT = 0.05
    
    # 容差配置
    SIZE_TOLERANCE = 0.5
    PAD_COUNT_TOLERANCE = 2

    def __init__(self, library_system: ComponentLibrarySystem):
        """
        初始化识别引擎
        
        Args:
            library_system: 封装库系统实例
        """
        self.library = library_system

    def extract_features(self, cluster: Dict[str, Any], pads: List[Dict[str, Any]]) -> ClusterFeatures:
        """
        从聚类和焊盘提取特征
        
        Args:
            cluster: 聚类信息字典
            pads: 所有焊盘的完整列表
            
        Returns:
            聚类特征对象
        """
        indices = cluster.get('indices', [])
        cluster_pads = [pads[i] for i in indices] if indices else []
        
        pad_shapes = [p.get('shape', 'unknown') for p in cluster_pads]
        has_circle = any(s == 'circle' for s in pad_shapes)
        has_rect = any(s in ('rect', 'oval') for s in pad_shapes)
        
        avg_w = sum(p.get('width', 0) for p in cluster_pads) / max(len(cluster_pads), 1)
        avg_h = sum(p.get('height', 0) for p in cluster_pads) / max(len(cluster_pads), 1)
        
        pitch = self._calculate_pad_pitch(cluster_pads)
        
        layout = self._detect_layout_pattern(
            cluster_pads, 
            cluster.get('width', 0), 
            cluster.get('height', 0)
        )
        
        return ClusterFeatures(
            pad_count=cluster.get('count', len(cluster_pads)),
            width=cluster.get('width', 0),
            height=cluster.get('height', 0),
            aspect_ratio=cluster.get('width', 0) / max(cluster.get('height', 0.01), 0.01),
            avg_pad_width=avg_w,
            avg_pad_height=avg_h,
            pad_shapes=pad_shapes,
            pad_pitch=pitch,
            layout_pattern=layout,
            has_circle_pads=has_circle,
            has_rect_pads=has_rect,
        )

    def _calculate_pad_pitch(self, pads: List[Dict[str, Any]]) -> Optional[float]:
        """
        计算焊盘间距
        
        Args:
            pads: 焊盘列表
            
        Returns:
            平均间距或 None
        """
        if len(pads) < 2:
            return None
        
        coords = [(p['x'], p['y']) for p in pads]
        
        # 按 x 排序计算水平间距
        sorted_x = sorted(coords, key=lambda c: c[0])
        pitches_x = [sorted_x[i+1][0] - sorted_x[i][0] for i in range(len(sorted_x)-1)]
        pitches_x = [p for p in pitches_x if 0.1 < p < 5.0]
        
        # 按 y 排序计算垂直间距
        sorted_y = sorted(coords, key=lambda c: c[1])
        pitches_y = [sorted_y[i+1][1] - sorted_y[i][1] for i in range(len(sorted_y)-1)]
        pitches_y = [p for p in pitches_y if 0.1 < p < 5.0]
        
        all_pitches = pitches_x + pitches_y
        if not all_pitches:
            return None
        
        avg = sum(all_pitches) / len(all_pitches)
        std = (sum((p - avg) ** 2 for p in all_pitches) / len(all_pitches)) ** 0.5
        
        if std / avg < 0.2:
            return round(avg, 3)
        return None

    def _detect_layout_pattern(
        self, 
        pads: List[Dict[str, Any]], 
        width: float, 
        height: float
    ) -> str:
        """
        检测布局模式: single, dual, quad, grid
        
        Args:
            pads: 焊盘列表
            width: 包围盒宽度
            height: 包围盒高度
            
        Returns:
            布局模式字符串
        """
        if len(pads) <= 1:
            return 'single'
        
        xs = [p['x'] for p in pads]
        ys = [p['y'] for p in pads]
        
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        
        # 统计四边焊盘
        half_w = width / 2
        half_h = height / 2
        left = sum(1 for p in pads if abs(p['x'] - (cx - half_w)) < half_w * 0.4)
        right = sum(1 for p in pads if abs(p['x'] - (cx + half_w)) < half_w * 0.4)
        top = sum(1 for p in pads if abs(p['y'] - (cy + half_h)) < half_h * 0.4)
        bottom = sum(1 for p in pads if abs(p['y'] - (cy - half_h)) < half_h * 0.4)
        
        if left > 2 and right > 2 and top > 2 and bottom > 2:
            return 'quad'
        if left > 2 and right > 2:
            return 'dual'
        if len(pads) > 20 and left > 4 and right > 4:
            return 'grid'
        return 'single'

    def match_package(self, features: ClusterFeatures) -> List[Tuple[PackageDefinition, float]]:
        """
        匹配封装，返回按置信度排序的匹配列表
        
        Args:
            features: 聚类特征
            
        Returns:
            (封装定义, 置信度) 列表，按置信度降序排列
        """
        candidates = self.library.find_packages_by_pad_count(
            features.pad_count, 
            tolerance=2
        )
        
        matches = []
        for pkg in candidates:
            confidence = self._calculate_confidence(features, pkg)
            if confidence > 0:
                matches.append((pkg, confidence))
        
        matches.sort(key=lambda x: -x[1])
        return matches

    def _calculate_confidence(self, features: ClusterFeatures, pkg: PackageDefinition) -> float:
        """
        计算特征与封装定义的置信度 (0-100)
        
        Args:
            features: 聚类特征
            pkg: 封装定义
            
        Returns:
            置信度分数
        """
        score = 0.0
        
        # 1. 焊盘数量匹配 (30%)
        if features.pad_count == pkg.pad_count:
            score += self.W_PAD_COUNT * 100
        elif abs(features.pad_count - pkg.pad_count) <= self.PAD_COUNT_TOLERANCE:
            score += self.W_PAD_COUNT * 50
        else:
            return 0  # 焊盘数量偏差太大，直接淘汰
        
        # 2. 尺寸匹配 (25%)
        w = features.width
        h = features.height
        if pkg.width_min <= w <= pkg.width_max and pkg.height_min <= h <= pkg.height_max:
            score += self.W_SIZE * 100
        elif (self._is_in_tolerance(w, pkg.width_min, pkg.width_max, self.SIZE_TOLERANCE) and 
              self._is_in_tolerance(h, pkg.height_min, pkg.height_max, self.SIZE_TOLERANCE)):
            score += self.W_SIZE * 60
        else:
            score += self.W_SIZE * 20
        
        # 3. 长宽比匹配 (15%)
        ar = features.aspect_ratio
        if pkg.aspect_ratio_min <= ar <= pkg.aspect_ratio_max:
            score += self.W_ASPECT * 100
        else:
            score += self.W_ASPECT * 20
        
        # 4. 间距匹配 (15%)
        if (features.pad_pitch is not None and 
            pkg.pad_pitch_min is not None and 
            pkg.pad_pitch_max is not None):
            if pkg.pad_pitch_min <= features.pad_pitch <= pkg.pad_pitch_max:
                score += self.W_PITCH * 100
            else:
                score += self.W_PITCH * 20
        elif features.pad_pitch is not None and pkg.pad_pitch_min is None:
            score += self.W_PITCH * 50  # 封装未定义间距，中等置信
        else:
            score += self.W_PITCH * 30  # 无法计算间距
        
        # 5. 焊盘形状匹配 (10%)
        pkg_shape = pkg.pad_shape
        if pkg_shape == 'any':
            score += self.W_SHAPE * 100
        elif pkg_shape == 'circle' and features.has_circle_pads and not features.has_rect_pads:
            score += self.W_SHAPE * 100
        elif pkg_shape == 'rect' and features.has_rect_pads:
            score += self.W_SHAPE * 80
        else:
            score += self.W_SHAPE * 30
        
        return round(score, 1)

    def _is_in_tolerance(self, value: float, min_val: float, max_val: float, tolerance_mm: float) -> bool:
        """
        检查值是否在容差范围内
        
        Args:
            value: 待检查的值
            min_val: 最小值
            max_val: 最大值
            tolerance_mm: 容差
            
        Returns:
            是否在容差范围内
        """
        return (min_val - tolerance_mm) <= value <= (max_val + tolerance_mm)

    def select_best_match(
        self, 
        matches: List[Tuple[PackageDefinition, float]], 
        threshold: float = 60
    ) -> RecognitionResult:
        """
        选择最佳匹配
        
        Args:
            matches: 匹配列表
            threshold: 置信度阈值
            
        Returns:
            识别结果
        """
        if not matches:
            return RecognitionResult(features=None)
        
        best_pkg, best_conf = matches[0]
        
        if best_conf < threshold:
            return RecognitionResult(
                component_type="Unknown",
                confidence=best_conf,
                category='unknown',
                matched_package_id=best_pkg.id if best_conf > 30 else None
            )
        
        # 格式化元件类型名称
        if best_pkg.type.startswith('ic_'):
            comp_type = best_pkg.type.replace('ic_', '').upper()
        else:
            comp_type = best_pkg.type.capitalize()
        
        result = RecognitionResult(
            component_type=comp_type,
            confidence=best_conf,
            category=best_pkg.category,
            hierarchy=best_pkg.hierarchy,
            matched_package_id=best_pkg.id
        )
        
        # 如果有多个接近的匹配，选用 more specific 的
        if len(matches) > 1:
            second_pkg, second_conf = matches[1]
            if abs(best_conf - second_conf) < 5:
                if best_pkg.hierarchy == 'generic' and second_pkg.hierarchy == 'specific':
                    result.component_type = second_pkg.type.upper()
                    result.matched_package_id = second_pkg.id
        
        return result

    def recognize(
        self, 
        cluster: Dict[str, Any], 
        pads: List[Dict[str, Any]]
    ) -> RecognitionResult:
        """
        完整识别流程
        
        Args:
            cluster: 聚类信息
            pads: 焊盘列表
            
        Returns:
            识别结果
        """
        features = self.extract_features(cluster, pads)
        matches = self.match_package(features)
        result = self.select_best_match(matches)
        result.features = features
        return result
