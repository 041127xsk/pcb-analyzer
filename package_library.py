"""
元件封装库系统 — 兼容层

为了保持向后兼容，保留此文件作为入口点。
实际实现已迁移到 package_library 包中。

推荐使用新导入方式:
    from package_library import ComponentLibrarySystem, RecognitionEngine

保留的兼容导入:
    from package_library import ComponentLibrarySystem  # 仍然有效
"""

# 从新的包结构中导入所有公共 API
from package_library import (
    PackageDefinition,
    ClusterFeatures,
    RecognitionResult,
    ConfigLoader,
    ComponentLibrarySystem,
    RecognitionEngine,
)

# 保持向后兼容的便捷函数
def create_library_system(custom_lib_path=None):
    """创建封装库系统实例（向后兼容）"""
    return ComponentLibrarySystem(custom_lib_path)


__all__ = [
    'PackageDefinition',
    'ClusterFeatures',
    'RecognitionResult',
    'ConfigLoader',
    'ComponentLibrarySystem',
    'RecognitionEngine',
    'create_library_system',
]


if __name__ == '__main__':
    # 测试
    lib = ComponentLibrarySystem()
    print(f"默认封装库: {len(lib.get_all_packages())} 个封装")
    lib.list_packages()
