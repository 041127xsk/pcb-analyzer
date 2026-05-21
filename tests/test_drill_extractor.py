"""
DrillExtractor 单元测试
"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from drill_extractor import DrillExtractor


class TestDrillExtractor:
    """DrillExtractor 测试类"""
    
    @pytest.fixture
    def sample_excellon_file(self):
        """创建测试 Excellon 文件"""
        content = """%
M48
METRIC,TZ
T01C0.8
T02C1.0
T03C1.2
%
T01
X10.0Y10.0
X15.0Y10.0
X20.0Y10.0
T02
X25.0Y10.0
X30.0Y10.0
T03
X35.0Y10.0
X40.0Y10.0
M30
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.drl', delete=False) as f:
            f.write(content)
            f.flush()
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def extractor(self):
        """创建提取器实例"""
        return DrillExtractor(verbose=False)
    
    def test_extract_from_file(self, sample_excellon_file, extractor):
        """测试从文件提取钻孔"""
        drills = extractor.extract_from_file(sample_excellon_file)
        
        assert len(drills) == 7
        assert all('x' in d for d in drills)
        assert all('y' in d for d in drills)
        assert all('diameter' in d for d in drills)
        assert all('plated' in d for d in drills)
        assert all('type' in d for d in drills)
    
    def test_extract_first_drill(self, sample_excellon_file, extractor):
        """测试第一个钻孔数据"""
        drills = extractor.extract_from_file(sample_excellon_file)
        
        first = drills[0]
        assert first['x'] == 10.0
        assert first['y'] == 10.0
        assert first['diameter'] == 0.8
        assert first['type'] == 'round'
    
    def test_extract_different_diameters(self, sample_excellon_file, extractor):
        """测试不同孔径提取"""
        drills = extractor.extract_from_file(sample_excellon_file)
        
        diameters = set(d['diameter'] for d in drills)
        assert 0.8 in diameters
        assert 1.0 in diameters
        assert 1.2 in diameters
    
    def test_infer_plating_pth(self, extractor):
        """测试从文件名推断镀层状态"""
        assert extractor._infer_plating_from_filename('drill.drl') is True
        assert extractor._infer_plating_from_filename('PTH.drl') is True
        assert extractor._infer_plating_from_filename('plated.drl') is True
        assert extractor._infer_plating_from_filename('NPTH.drl') is False
        assert extractor._infer_plating_from_filename('npth.drl') is False
        assert extractor._infer_plating_from_filename('slot.drl') is False
        assert extractor._infer_plating_from_filename('unknown.drl') is None
    
    def test_merge_drills(self, extractor):
        """测试钻孔合并"""
        drills = [
            {'x': 10.0, 'y': 10.0, 'diameter': 0.8, 'plated': 'plated', 'type': 'round'},
            {'x': 10.001, 'y': 10.001, 'diameter': 0.8, 'plated': 'plated', 'type': 'round'},
            {'x': 20.0, 'y': 20.0, 'diameter': 1.0, 'plated': 'nonplated', 'type': 'round'},
        ]
        
        merged = extractor._merge_drills(drills, tolerance=0.05)
        assert len(merged) == 2
    
    def test_save_csv(self, sample_excellon_file, extractor):
        """测试保存 CSV"""
        drills = extractor.extract_from_file(sample_excellon_file)
        extractor.drills = drills
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            extractor.save_csv(csv_path)
            
            assert os.path.exists(csv_path)
            
            import csv
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 7
            assert 'x' in rows[0]
            assert 'y' in rows[0]
            assert 'diameter' in rows[0]
        finally:
            os.unlink(csv_path)
    
    def test_get_through_hole_pads(self, extractor):
        """测试通孔焊盘匹配"""
        extractor.drills = [
            {'x': 10.0, 'y': 10.0, 'diameter': 0.8, 'plated': 'plated', 'type': 'round'},
            {'x': 20.0, 'y': 20.0, 'diameter': 1.0, 'plated': 'nonplated', 'type': 'round'},
        ]
        
        pads = [
            {'x': 10.0, 'y': 10.0, 'shape': 'circle', 'width': 1.5, 'height': 1.5},
            {'x': 20.0, 'y': 20.0, 'shape': 'rect', 'width': 2.0, 'height': 2.0},
            {'x': 50.0, 'y': 50.0, 'shape': 'circle', 'width': 1.0, 'height': 1.0},
        ]
        
        enhanced = extractor.get_through_hole_pads(pads, tolerance=0.5)
        
        assert enhanced[0]['has_drill'] is True
        assert enhanced[0]['drill_diameter'] == 0.8
        assert enhanced[0]['plated'] == 'plated'
        
        assert enhanced[1]['has_drill'] is True
        assert enhanced[1]['drill_diameter'] == 1.0
        assert enhanced[1]['plated'] == 'nonplated'
        
        assert enhanced[2]['has_drill'] is False
        assert enhanced[2]['drill_diameter'] is None
    
    def test_extract_from_empty_dir(self, extractor):
        """测试空目录提取"""
        with tempfile.TemporaryDirectory() as tmpdir:
            drills = extractor.extract_from_dir(tmpdir)
            assert drills == []
    
    def test_collect_excellon_files(self, extractor):
        """测试收集 Excellon 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, 'drill.drl').touch()
            Path(tmpdir, 'ncdrill.ncd').touch()
            Path(tmpdir, 'lay1.gbr').touch()
            Path(tmpdir, 'readme.md').touch()
            
            files = extractor._collect_excellon_files(Path(tmpdir))
            
            assert len(files) == 2
            assert any(f.name == 'drill.drl' for f in files)
            assert any(f.name == 'ncdrill.ncd' for f in files)
    
    def test_extract_with_plated_override(self, sample_excellon_file, extractor):
        """测试镀层覆盖"""
        drills = extractor.extract_from_file(sample_excellon_file, plated=True)
        
        assert all(d['plated'] == 'plated' for d in drills)
        
        drills = extractor.extract_from_file(sample_excellon_file, plated=False)
        assert all(d['plated'] == 'nonplated' for d in drills)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
