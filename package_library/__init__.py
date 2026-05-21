"""
元件封装库系统 — 可配置的封装定义与识别引擎

支持 JSON/YAML 配置文件、默认库、置信度评分识别

主要组件:
    - PackageDefinition: 封装定义数据类
    - ClusterFeatures: 聚类特征
    - RecognitionResult: 识别结果
    - ConfigLoader: 配置加载器
    - ComponentLibrarySystem: 库系统主类
    - RecognitionEngine: 识别引擎

使用方法:
    from package_library import ComponentLibrarySystem, RecognitionEngine
    
    # 创建库系统
    lib = ComponentLibrarySystem(custom_lib_path='path/to/custom_lib.json')
    
    # 创建识别引擎
    engine = RecognitionEngine(lib)
    
    # 识别元件
    result = engine.recognize(cluster, pads)
    print(f"识别结果: {result.component_type}, 置信度: {result.confidence}")
"""

from .models import PackageDefinition, ClusterFeatures, RecognitionResult
from .config_loader import ConfigLoader
from .library_system import ComponentLibrarySystem
from .recognition_engine import RecognitionEngine

__all__ = [
    'PackageDefinition',
    'ClusterFeatures',
    'RecognitionResult',
    'ConfigLoader',
    'ComponentLibrarySystem',
    'RecognitionEngine',
]

__version__ = '1.0.0'
