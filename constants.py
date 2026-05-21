"""
项目常量定义
集中管理文件扩展名、优先级等配置
"""

GERBER_EXTENSIONS = ['.gbr', '.gb', '.ger', '.gtl', '.gbl', '.gbs', '.gbo', '.gml', '.dxf']

EXCELLON_EXTENSIONS = ['.drl', '.ncd', '.xln', '.txt', '.drd', '.dri', '.nc']

PRIORITY_LAYERS = [
    'mask1.gbr', 'mask2.gbr',
    'via_plugging.gbr',
    'drilldrw.gbr',
    'lay1.gbr', 'lay4.gbr',
    'lay2.gbr', 'lay3.gbr',
    'silk1.gbr', 'silk2.gbr',
]

PAD_MERGE_TOLERANCE = 0.05

CLUSTER_DISTANCE_DEFAULT = 2.0

DRILL_PAD_MATCH_TOLERANCE = 0.5
