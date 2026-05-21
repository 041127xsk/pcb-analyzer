"""
库系统模块

管理封装库，支持默认库和自定义库的加载与查询
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from .models import PackageDefinition
from .config_loader import ConfigLoader


# 模块级 logger
_logger = logging.getLogger(__name__)

# 默认库路径
_DEFAULT_LIB_PATH = Path(__file__).parent.parent / 'config' / 'packages' / 'default_library.json'


def _ensure_default_lib() -> None:
    """
    如果外部 JSON 不存在，从代码中的默认值生成
    
    此函数在模块级别使用，因此使用模块级 logger
    """
    try:
        lib_dir = Path(__file__).parent.parent / 'config' / 'packages'
        lib_dir.mkdir(parents=True, exist_ok=True)
        
        defaults = [
            {'id': 'R_0402', 'type': 'resistor', 'pad_count': 2, 'width_min': 0.4, 'width_max': 0.8, 'height_min': 0.2, 'height_max': 0.6, 'aspect_ratio_min': 1.5, 'aspect_ratio_max': 4.0, 'category': 'passive', 'pad_shape': 'rect', 'description': 'SMD Resistor/Capacitor 0402'},
            {'id': 'R_0603', 'type': 'resistor', 'pad_count': 2, 'width_min': 0.6, 'width_max': 1.2, 'height_min': 0.3, 'height_max': 0.7, 'aspect_ratio_min': 1.2, 'aspect_ratio_max': 3.5, 'category': 'passive', 'pad_shape': 'rect', 'description': 'SMD Resistor/Capacitor 0603'},
            {'id': 'R_0805', 'type': 'resistor', 'pad_count': 2, 'width_min': 0.8, 'width_max': 1.6, 'height_min': 0.4, 'height_max': 1.0, 'aspect_ratio_min': 1.0, 'aspect_ratio_max': 3.0, 'category': 'passive', 'pad_shape': 'rect', 'description': 'SMD Resistor/Capacitor 0805'},
            {'id': 'R_1206', 'type': 'resistor', 'pad_count': 2, 'width_min': 1.2, 'width_max': 2.0, 'height_min': 0.5, 'height_max': 1.2, 'aspect_ratio_min': 1.0, 'aspect_ratio_max': 2.5, 'category': 'passive', 'pad_shape': 'rect', 'description': 'SMD Resistor/Capacitor 1206'},
            {'id': 'SOP_8', 'type': 'ic_sop', 'pad_count': 8, 'width_min': 3.0, 'width_max': 6.0, 'height_min': 2.5, 'height_max': 5.0, 'aspect_ratio_min': 1.0, 'aspect_ratio_max': 2.0, 'category': 'ic', 'layout_pattern': 'dual', 'pad_shape': 'rect', 'pad_pitch_min': 1.0, 'pad_pitch_max': 1.5, 'description': 'SOP-8'},
            {'id': 'SOP_16', 'type': 'ic_sop', 'pad_count': 16, 'width_min': 3.0, 'width_max': 7.0, 'height_min': 4.0, 'height_max': 10.0, 'aspect_ratio_min': 1.2, 'aspect_ratio_max': 2.5, 'category': 'ic', 'layout_pattern': 'dual', 'pad_shape': 'rect', 'pad_pitch_min': 1.0, 'pad_pitch_max': 1.5, 'description': 'SOP-16'},
            {'id': 'QFP_44', 'type': 'ic_qfp', 'pad_count': 44, 'width_min': 8.0, 'width_max': 14.0, 'height_min': 8.0, 'height_max': 14.0, 'aspect_ratio_min': 1.0, 'aspect_ratio_max': 1.3, 'category': 'ic', 'layout_pattern': 'quad', 'pad_shape': 'rect', 'pad_pitch_min': 0.5, 'pad_pitch_max': 1.0, 'description': 'QFP-44'},
            {'id': 'QFP_64', 'type': 'ic_qfp', 'pad_count': 64, 'width_min': 10.0, 'width_max': 16.0, 'height_min': 10.0, 'height_max': 16.0, 'aspect_ratio_min': 1.0, 'aspect_ratio_max': 1.3, 'category': 'ic', 'layout_pattern': 'quad', 'pad_shape': 'rect', 'pad_pitch_min': 0.4, 'pad_pitch_max': 0.8, 'description': 'QFP-64'},
            {'id': 'QFN_32', 'type': 'ic_qfn', 'pad_count': 32, 'width_min': 4.0, 'width_max': 6.0, 'height_min': 4.0, 'height_max': 6.0, 'aspect_ratio_min': 1.0, 'aspect_ratio_max': 1.4, 'category': 'ic', 'layout_pattern': 'quad', 'pad_shape': 'rect', 'pad_pitch_min': 0.4, 'pad_pitch_max': 0.8, 'description': 'QFN-32'},
            {'id': 'BGA_100', 'type': 'ic_bga', 'pad_count': 100, 'width_min': 7.0, 'width_max': 14.0, 'height_min': 7.0, 'height_max': 14.0, 'aspect_ratio_min': 1.0, 'aspect_ratio_max': 1.3, 'category': 'ic', 'layout_pattern': 'grid', 'pad_shape': 'circle', 'pad_pitch_min': 0.5, 'pad_pitch_max': 1.5, 'description': 'BGA-100'},
            {'id': 'SOT_23', 'type': 'transistor', 'pad_count': 3, 'width_min': 1.0, 'width_max': 2.2, 'height_min': 0.8, 'height_max': 1.8, 'aspect_ratio_min': 1.0, 'aspect_ratio_max': 2.0, 'category': 'discrete', 'pad_shape': 'rect', 'description': 'SOT-23'},
            {'id': 'PIN_HEADER_4', 'type': 'connector_pin', 'pad_count': 4, 'width_min': 2.0, 'width_max': 5.0, 'height_min': 5.0, 'height_max': 10.0, 'aspect_ratio_min': 1.5, 'aspect_ratio_max': 4.0, 'category': 'connector', 'layout_pattern': 'dual', 'pad_shape': 'circle', 'pad_pitch_min': 2.0, 'pad_pitch_max': 3.0, 'description': 'Pin Header 4P'},
        ]
        with open(_DEFAULT_LIB_PATH, 'w', encoding='utf-8') as f:
            json.dump({'packages': defaults}, f, indent=2, ensure_ascii=False)
        _logger.info(f"Generated default library: {_DEFAULT_LIB_PATH}")
    except PermissionError as e:
        _logger.error(f"Permission denied when generating default library: {e}")
    except OSError as e:
        _logger.error(f"OS error when generating default library: {e}")
    except Exception as e:
        _logger.warning(f"Could not generate default library: {e}")


def _build_default_packages() -> List[PackageDefinition]:
    """
    从外部 JSON 文件加载默认封装库
    
    Returns:
        封装定义列表，加载失败返回空列表
    """
    if not _DEFAULT_LIB_PATH.exists():
        _logger.warning(f"Default library not found: {_DEFAULT_LIB_PATH}")
        _logger.info("Attempting to generate default library...")
        _ensure_default_lib()
        if not _DEFAULT_LIB_PATH.exists():
            _logger.error("Failed to generate default library")
            return []
    
    try:
        with open(_DEFAULT_LIB_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        pkgs = []
        for item in data.get('packages', []):
            pkg = PackageDefinition(**item)
            pkg.aliases = [pkg.id]
            pkgs.append(pkg)
        _logger.debug(f"Loaded {len(pkgs)} packages from default library")
        return pkgs
    except FileNotFoundError:
        _logger.error(f"Default library file not found: {_DEFAULT_LIB_PATH}")
        return []
    except json.JSONDecodeError as e:
        _logger.error(f"Invalid JSON in default library: {e}")
        return []
    except PermissionError as e:
        _logger.error(f"Permission denied when reading default library: {e}")
        return []
    except Exception as e:
        _logger.warning(f"Failed to load default library: {e}")
        return []


class ComponentLibrarySystem:
    """
    元件封装库系统 — 管理默认库和自定义库
    
    提供封装库的加载、查询和管理功能
    
    Attributes:
        _packages: 所有封装定义列表
        _pad_count_index: 按焊盘数量索引
        _category_index: 按分类索引
    """

    def __init__(self, custom_lib_path: Optional[str] = None, log_level: int = logging.INFO):
        """
        初始化库系统
        
        Args:
            custom_lib_path: 自定义库配置文件或目录路径
            log_level: 日志级别
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        self._packages: List[PackageDefinition] = []
        self._pad_count_index: dict = {}
        self._category_index: dict = {}
        self._config_cache: dict = {}
        self._mtime_cache: dict = {}
        
        self.load_default_library()
        
        if custom_lib_path:
            self.load_custom_library(custom_lib_path)

    def load_default_library(self) -> None:
        """加载默认封装库"""
        self._packages = _build_default_packages()
        self._build_indexes()
        self.logger.info(f"默认库已加载: {len(self._packages)} 个封装")

    def load_custom_library(self, path: str) -> None:
        """
        加载自定义封装库
        
        Args:
            path: 配置文件或目录路径
        """
        path = Path(path)
        if not path.exists():
            self.logger.warning(f"自定义库路径不存在: {path}")
            return
        
        config_files = ConfigLoader.scan_directory(path) if path.is_dir() else [path]
        count = 0
        for cf in config_files:
            try:
                data = ConfigLoader.load_file(str(cf))
                is_valid, errors = ConfigLoader.validate_config(data)
                if not is_valid:
                    self.logger.warning(f"配置格式错误 {cf.name}: {'; '.join(errors)}")
                    continue
                for pkg_data in data['packages']:
                    pkg = PackageDefinition(**pkg_data)
                    # 自定义库覆盖默认库
                    existing = [i for i, p in enumerate(self._packages) if p.id == pkg.id]
                    if existing:
                        self._packages[existing[0]] = pkg
                        self.logger.debug(f"覆盖封装定义: {pkg.id}")
                    else:
                        self._packages.append(pkg)
                    count += 1
                self.logger.info(f"已加载: {cf.name}")
            except FileNotFoundError:
                self.logger.error(f"配置文件不存在: {cf}")
            except PermissionError:
                self.logger.error(f"权限不足，无法读取: {cf}")
            except Exception as e:
                self.logger.warning(f"加载失败 {cf.name}: {e}")
        
        self._build_indexes()
        self.logger.info(f"自定义库: {count} 个封装, 总计: {len(self._packages)} 个")

    def _build_indexes(self) -> None:
        """构建索引以加速查询"""
        self._pad_count_index = {}
        self._category_index = {}
        for i, pkg in enumerate(self._packages):
            pc = pkg.pad_count
            if pc not in self._pad_count_index:
                self._pad_count_index[pc] = []
            self._pad_count_index[pc].append(i)
            
            cat = pkg.category
            if cat not in self._category_index:
                self._category_index[cat] = []
            self._category_index[cat].append(i)

    def get_all_packages(self) -> List[PackageDefinition]:
        """获取所有封装定义"""
        return self._packages

    def get_package_by_id(self, package_id: str) -> Optional[PackageDefinition]:
        """
        按 ID 查找封装
        
        Args:
            package_id: 封装 ID
            
        Returns:
            封装定义或 None
        """
        for pkg in self._packages:
            if pkg.id == package_id:
                return pkg
            if package_id in pkg.aliases:
                return pkg
        return None

    def find_packages_by_pad_count(self, count: int, tolerance: int = 0) -> List[PackageDefinition]:
        """
        按焊盘数量查找封装
        
        Args:
            count: 焊盘数量
            tolerance: 容差范围
            
        Returns:
            匹配的封装列表
        """
        results = []
        for lo in range(count - tolerance, count + tolerance + 1):
            for idx in self._pad_count_index.get(lo, []):
                results.append(self._packages[idx])
        return results

    def validate_config_file(self, file_path: str) -> bool:
        """
        验证配置文件的正确性
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            是否有效
        """
        path = Path(file_path)
        try:
            data = ConfigLoader.load_file(str(path))
        except FileNotFoundError:
            self.logger.error(f"配置文件不存在: {path}")
            return False
        except PermissionError:
            self.logger.error(f"权限不足，无法读取: {path}")
            return False
        except Exception as e:
            self.logger.error(f"配置文件加载错误: {e}")
            return False
        
        is_valid, errors = ConfigLoader.validate_config(data)
        if is_valid:
            self.logger.info(f"Configuration file is valid: {path}")
            self.logger.info(f"Contains {len(data['packages'])} package definitions")
        else:
            self.logger.error(f"Configuration file has errors: {path}")
            for err in errors:
                self.logger.error(f"  - {err}")
        return is_valid

    def list_packages(self, category: Optional[str] = None) -> None:
        """
        格式化列出所有封装
        
        Args:
            category: 按分类筛选
        """
        pkgs = self._packages
        if category:
            pkgs = [p for p in pkgs if p.category == category]
        
        # list_packages 是用户交互方法，保留 print 输出
        print(f"{'ID':<20} {'Type':<16} {'Pads':>5} {'Size Range(mm)':<24} {'Description'}")
        print("-" * 90)
        for pkg in sorted(pkgs, key=lambda p: (p.category, p.pad_count, p.id)):
            size_range = f"{pkg.width_min:.1f}-{pkg.width_max:.1f}x{pkg.height_min:.1f}-{pkg.height_max:.1f}"
            print(f"{pkg.id:<20} {pkg.type:<16} {pkg.pad_count:>5} {size_range:<24} {pkg.description}")
        print(f"\nTotal: {len(pkgs)} packages")
