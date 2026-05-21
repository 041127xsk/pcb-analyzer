"""
配置加载器模块

支持 JSON 和 YAML 配置文件的加载和验证
"""

import json
from pathlib import Path
from typing import Tuple, List, Dict, Any


class ConfigLoader:
    """
    配置文件加载器 — 支持 JSON 和 YAML
    
    自动检测文件格式并加载，提供配置验证功能
    """

    YAML_AVAILABLE = False
    try:
        import yaml as _yaml
        YAML_AVAILABLE = True
    except ImportError:
        pass

    @staticmethod
    def load_json(file_path: str) -> Dict[str, Any]:
        """
        加载 JSON 配置文件
        
        Args:
            file_path: JSON 文件路径
            
        Returns:
            解析后的字典数据
            
        Raises:
            FileNotFoundError: 文件不存在
            json.JSONDecodeError: JSON 格式错误
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def load_yaml(file_path: str) -> Dict[str, Any]:
        """
        加载 YAML 配置文件
        
        Args:
            file_path: YAML 文件路径
            
        Returns:
            解析后的字典数据
            
        Raises:
            ImportError: pyyaml 未安装
            FileNotFoundError: 文件不存在
        """
        if not ConfigLoader.YAML_AVAILABLE:
            raise ImportError("pyyaml 未安装。运行: pip install pyyaml")
        import yaml
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @staticmethod
    def load_file(file_path: str) -> Dict[str, Any]:
        """
        自动检测格式并加载配置文件
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            解析后的字典数据
            
        Raises:
            ValueError: 不支持的文件格式
        """
        path = Path(file_path)
        if path.suffix in ('.json',):
            return ConfigLoader.load_json(file_path)
        elif path.suffix in ('.yaml', '.yml'):
            return ConfigLoader.load_yaml(file_path)
        else:
            raise ValueError(f"不支持的配置文件格式: {path.suffix}")

    @staticmethod
    def validate_config(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证配置数据结构
        
        Args:
            data: 配置数据字典
            
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        if not isinstance(data, dict):
            return False, ['配置根元素必须是字典']
        if 'packages' not in data:
            return False, ['配置缺少 "packages" 字段']
        if not isinstance(data['packages'], list):
            return False, ['"packages" 必须是列表']
        
        for i, pkg in enumerate(data['packages']):
            prefix = f"packages[{i}]"
            required = ['id', 'type', 'pad_count', 'width_min', 'width_max', 'height_min', 'height_max']
            for field in required:
                if field not in pkg:
                    errors.append(f"{prefix}: 缺少必填字段 '{field}'")
            if 'width_min' in pkg and 'width_max' in pkg:
                if pkg['width_min'] > pkg['width_max']:
                    errors.append(f"{prefix}: width_min > width_max")
            if 'height_min' in pkg and 'height_max' in pkg:
                if pkg['height_min'] > pkg['height_max']:
                    errors.append(f"{prefix}: height_min > height_max")
        
        return len(errors) == 0, errors

    @staticmethod
    def scan_directory(dir_path: str) -> List[Path]:
        """
        扫描目录中的 .json 和 .yaml 文件
        
        Args:
            dir_path: 目录路径
            
        Returns:
            配置文件路径列表
        """
        dir_path = Path(dir_path)
        files = []
        for ext in ('.json', '.yaml', '.yml'):
            files.extend(dir_path.rglob(f'*{ext}'))
        return sorted(files)
