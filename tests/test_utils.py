"""
utils 模块单元测试
"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    ensure_output_dir, get_gerber_files, parse_gerber_unit,
    format_coord, format_size, merge_results, validate_pad, get_file_size
)


class TestUtils:
    """utils 测试类"""
    
    def test_ensure_output_dir(self):
        """测试创建输出目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / 'sub' / 'output'
            result = ensure_output_dir(str(new_dir))
            assert new_dir.exists()
            assert str(result) == str(new_dir)
    
    def test_ensure_output_dir_existing(self):
        """测试已存在的目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_output_dir(tmpdir)
            assert result == tmpdir
    
    def test_get_gerber_files_single(self):
        """测试单个文件"""
        with tempfile.NamedTemporaryFile(suffix='.gbr', delete=False) as f:
            files = get_gerber_files(f.name)
            assert len(files) == 1
            assert files[0] == Path(f.name)
    
    def test_get_gerber_files_directory(self):
        """测试目录中的 Gerber 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, 'lay1.gbr').touch()
            Path(tmpdir, 'mask1.gbr').touch()
            Path(tmpdir, 'readme.txt').touch()
            
            files = get_gerber_files(tmpdir)
            assert len(files) >= 2
    
    def test_get_gerber_files_empty_dir(self):
        """测试空目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = get_gerber_files(tmpdir)
            assert files == []
    
    def test_get_gerber_files_invalid_path(self):
        """测试无效路径"""
        files = get_gerber_files('/nonexistent/path')
        assert files == []
    
    def test_parse_gerber_unit_fallback(self):
        """测试单位解析回退"""
        result = parse_gerber_unit('/nonexistent/file.gbr')
        assert result == 'mm'
    
    def test_format_coord(self):
        """测试坐标格式化"""
        assert format_coord(10.12345) == 10.12
        assert format_coord(10.12345, precision=3) == 10.123
    
    def test_format_size(self):
        """测试尺寸格式化"""
        assert format_size(1.2345) == 1.234
        assert format_size(1.2345, precision=1) == 1.2
    
    def test_merge_results_no_duplicates(self):
        """测试合并无重复结果"""
        results = [
            [{'x': 10.0, 'y': 10.0, 'shape': 'circle', 'width': 1.0, 'height': 1.0}],
            [{'x': 20.0, 'y': 20.0, 'shape': 'rect', 'width': 2.0, 'height': 1.5}],
        ]
        merged = merge_results(results)
        assert len(merged) == 2
    
    def test_merge_results_with_duplicates(self):
        """测试合并有重复结果"""
        results = [
            [{'x': 10.0, 'y': 10.0, 'shape': 'circle', 'width': 1.0, 'height': 1.0}],
            [{'x': 10.001, 'y': 10.001, 'shape': 'circle', 'width': 1.5, 'height': 1.5}],
        ]
        merged = merge_results(results)
        assert len(merged) == 1
        assert merged[0]['width'] == 1.5
    
    def test_merge_results_no_mutation(self):
        """测试合并不修改原始数据"""
        pad1 = {'x': 10.0, 'y': 10.0, 'shape': 'circle', 'width': 1.0, 'height': 1.0}
        pad2 = {'x': 10.001, 'y': 10.001, 'shape': 'circle', 'width': 1.5, 'height': 1.5}
        results = [[pad1], [pad2]]
        
        merge_results(results)
        
        assert pad1['width'] == 1.0
        assert pad2['width'] == 1.5
    
    def test_validate_pad_valid(self):
        """测试有效焊盘"""
        pad = {'x': 10.0, 'y': 10.0, 'shape': 'circle'}
        assert validate_pad(pad) is True
    
    def test_validate_pad_missing_field(self):
        """测试缺少字段"""
        pad = {'x': 10.0, 'shape': 'circle'}
        assert validate_pad(pad) is False
    
    def test_validate_pad_invalid_type(self):
        """测试无效类型"""
        pad = {'x': 'invalid', 'y': 10.0, 'shape': 'circle'}
        assert validate_pad(pad) is False
    
    def test_get_file_size(self):
        """测试文件大小"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'x' * 1024)
            f.flush()
            size_str = get_file_size(f.name)
            assert 'KB' in size_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
