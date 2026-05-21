"""
数据模型模块

定义封装库系统中使用的所有数据类
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class PackageDefinition:
    """
    封装定义数据类
    
    描述一个元件封装的完整规格，用于识别匹配
    
    Attributes:
        id: 唯一标识, e.g. "R_0402"
        type: 类型: resistor, capacitor, ic, connector, bga, diode, other
        pad_count: 焊盘数量
        width_min: 包围盒最小宽度 (mm)
        width_max: 包围盒最大宽度 (mm)
        height_min: 包围盒最小高度 (mm)
        height_max: 包围盒最大高度 (mm)
        aspect_ratio_min: 最小长宽比 (默认 0.0)
        aspect_ratio_max: 最大长宽比 (默认 999.0)
        category: 分类: passive, ic, connector, discrete, other
        hierarchy: 层级: generic, specific
        pad_pitch_min: 最小引脚间距 (mm), 可选
        pad_pitch_max: 最大引脚间距 (mm), 可选
        pad_shape: 焊盘形状: any, circle, rect, oval
        pad_width_min: 焊盘最小宽度 (mm), 可选
        pad_width_max: 焊盘最大宽度 (mm), 可选
        pad_height_min: 焊盘最小高度 (mm), 可选
        pad_height_max: 焊盘最大高度 (mm), 可选
        layout_pattern: 布局模式: any, dual, quad, grid, single
        description: 描述
        aliases: 别名列表
    """
    id: str
    type: str
    pad_count: int
    width_min: float
    width_max: float
    height_min: float
    height_max: float
    aspect_ratio_min: float = 0.0
    aspect_ratio_max: float = 999.0
    category: str = 'unknown'
    hierarchy: str = 'generic'
    pad_pitch_min: Optional[float] = None
    pad_pitch_max: Optional[float] = None
    pad_shape: str = 'any'
    pad_width_min: Optional[float] = None
    pad_width_max: Optional[float] = None
    pad_height_min: Optional[float] = None
    pad_height_max: Optional[float] = None
    layout_pattern: str = 'any'
    description: str = ''
    aliases: List[str] = field(default_factory=list)


@dataclass
class ClusterFeatures:
    """
    聚类特征 — 从焊盘提取的几何特征
    
    用于与封装定义进行匹配识别
    
    Attributes:
        pad_count: 焊盘数量
        width: 包围盒宽度
        height: 包围盒高度
        aspect_ratio: 长宽比
        avg_pad_width: 平均焊盘宽度
        avg_pad_height: 平均焊盘高度
        pad_shapes: 焊盘形状列表
        pad_pitch: 焊盘间距
        layout_pattern: 布局模式
        has_circle_pads: 是否有圆形焊盘
        has_rect_pads: 是否有矩形焊盘
    """
    pad_count: int
    width: float
    height: float
    aspect_ratio: float
    avg_pad_width: float = 0.0
    avg_pad_height: float = 0.0
    pad_shapes: List[str] = field(default_factory=list)
    pad_pitch: Optional[float] = None
    layout_pattern: str = 'unknown'
    has_circle_pads: bool = False
    has_rect_pads: bool = False


@dataclass
class RecognitionResult:
    """
    识别结果
    
    封装识别引擎的输出结果
    
    Attributes:
        component_type: 识别的元件类型
        confidence: 置信度 (0-100)
        category: 分类
        hierarchy: 层级
        matched_package_id: 匹配的封装ID
        features: 聚类特征
    """
    component_type: str = 'Unknown'
    confidence: float = 0.0
    category: str = 'unknown'
    hierarchy: str = 'generic'
    matched_package_id: Optional[str] = None
    features: Optional[ClusterFeatures] = None
