"""
GerberExtractor 单元测试
"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractor import GerberExtractor


class TestGerberExtractor:
    """GerberExtractor 测试类"""
    
    @pytest.fixture
    def extractor(self):
        return GerberExtractor(verbose=False)
    
    def test_extract_from_nonexistent_file(self, extractor):
        """测试不存在的文件"""
        pads = extractor.extract_from_file('/nonexistent/path.gbr')
        assert pads == []
    
    def test_extract_from_dir_nonexistent(self, extractor):
        """测试不存在的目录"""
        with pytest.raises(FileNotFoundError):
            extractor.extract_from_dir('/nonexistent/dir')
    
    def test_extract_from_dir_no_gerber(self, extractor):
        """测试目录中没有 Gerber 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, 'readme.txt').write_text('hello')
            with pytest.raises(ValueError, match="没有 Gerber"):
                extractor.extract_from_dir(tmpdir)
    
    def test_merge_pads_no_duplicates(self, extractor):
        """测试无重复焊盘合并"""
        pads = [
            {'x': 10.0, 'y': 10.0, 'shape': 'circle', 'width': 1.0, 'height': 1.0},
            {'x': 20.0, 'y': 20.0, 'shape': 'rect', 'width': 2.0, 'height': 1.5},
        ]
        merged = extractor._merge_pads(pads)
        assert len(merged) == 2
    
    def test_merge_pads_with_duplicates(self, extractor):
        """测试重复焊盘合并"""
        pads = [
            {'x': 10.0, 'y': 10.0, 'shape': 'circle', 'width': 1.0, 'height': 1.0},
            {'x': 10.001, 'y': 10.001, 'shape': 'circle', 'width': 1.5, 'height': 1.5},
            {'x': 20.0, 'y': 20.0, 'shape': 'rect', 'width': 2.0, 'height': 1.5},
        ]
        merged = extractor._merge_pads(pads)
        assert len(merged) == 2
        assert merged[0]['width'] == 1.5
    
    def test_merge_pads_no_mutation(self, extractor):
        """测试合并时不修改原始数据"""
        original_pads = [
            {'x': 10.0, 'y': 10.0, 'shape': 'circle', 'width': 1.0, 'height': 1.0},
            {'x': 10.001, 'y': 10.001, 'shape': 'circle', 'width': 1.5, 'height': 1.5},
        ]
        merged = extractor._merge_pads(original_pads)
        assert original_pads[0]['width'] == 1.0
    
    def test_save_csv(self, extractor):
        """测试保存 CSV"""
        extractor.pads = [
            {'x': 10.0, 'y': 10.0, 'shape': 'circle', 'width': 1.0, 'height': 1.0},
            {'x': 20.0, 'y': 20.0, 'shape': 'rect', 'width': 2.0, 'height': 1.5},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            extractor.save_csv(csv_path)
            assert os.path.exists(csv_path)
            
            import csv
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2
            assert rows[0]['x'] == '10.0'
            assert rows[0]['shape'] == 'circle'
        finally:
            os.unlink(csv_path)
    
    def test_collect_gerber_files(self, extractor):
        """测试收集 Gerber 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, 'lay1.gbr').touch()
            Path(tmpdir, 'mask1.gbr').touch()
            Path(tmpdir, 'readme.txt').touch()
            
            files = extractor._collect_gerber_files(Path(tmpdir))
            assert len(files) == 2
            assert all(f.suffix == '.gbr' for f in files)
    
    def test_extract_single_pad_circle(self, extractor):
        """测试提取圆形焊盘"""
        from gerbonara.apertures import CircleAperture
        
        class MockFlash:
            def __init__(self):
                self.x = 10.0
                self.y = 20.0
                self.aperture = CircleAperture(diameter=1.5)
        
        pad = extractor._extract_single_pad(MockFlash())
        assert pad['shape'] == 'circle'
        assert pad['width'] == 1.5
        assert pad['height'] == 1.5
    
    def test_extract_single_pad_rect(self, extractor):
        """测试提取矩形焊盘"""
        from gerbonara.apertures import RectangleAperture
        
        class MockFlash:
            def __init__(self):
                self.x = 10.0
                self.y = 20.0
                self.aperture = RectangleAperture(w=2.0, h=1.0)
        
        pad = extractor._extract_single_pad(MockFlash())
        assert pad['shape'] == 'rect'
        assert pad['width'] == 2.0
        assert pad['height'] == 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
