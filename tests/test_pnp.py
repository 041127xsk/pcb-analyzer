"""
PNP 模块单元测试
"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from pnp import assign_refdes, estimate_rotation, generate_pnp, generate_pnp_simple


class TestPNP:
    """PNP 测试类"""
    
    @pytest.fixture
    def sample_clusters(self):
        return [
            {'count': 2, 'center_x': 10.0, 'center_y': 10.0, 'width': 2.0, 'height': 1.0, 'component_type': 'Resistor'},
            {'count': 2, 'center_x': 20.0, 'center_y': 20.0, 'width': 2.0, 'height': 1.0, 'component_type': 'Resistor'},
            {'count': 8, 'center_x': 30.0, 'center_y': 30.0, 'width': 5.0, 'height': 5.0, 'component_type': 'SOP-8'},
            {'count': 1, 'center_x': 40.0, 'center_y': 40.0, 'width': 1.0, 'height': 1.0, 'component_type': 'Unknown'},
        ]
    
    def test_assign_refdes_resistors(self, sample_clusters):
        """测试电阻位号分配"""
        result = assign_refdes(sample_clusters)
        assert result[0]['refdes'] == 'R1'
        assert result[1]['refdes'] == 'R2'
    
    def test_assign_refdes_ic(self, sample_clusters):
        """测试 IC 位号分配"""
        result = assign_refdes(sample_clusters)
        assert result[2]['refdes'] == 'U1'
    
    def test_assign_refdes_unknown(self, sample_clusters):
        """测试未知元件位号"""
        result = assign_refdes(sample_clusters)
        assert result[3]['refdes'] == 'X1'
    
    def test_assign_refdes_no_mutation(self, sample_clusters):
        """测试不修改原始数据"""
        import copy
        original = copy.deepcopy(sample_clusters)
        result = assign_refdes(sample_clusters)
        
        for orig in original:
            assert 'refdes' not in orig
        
        for modified in result:
            assert 'refdes' in modified
    
    def test_assign_refdes_counters_reset(self):
        """测试计数器不会跨调用累积"""
        clusters1 = [
            {'count': 2, 'center_x': 10.0, 'center_y': 10.0, 'width': 2.0, 'height': 1.0, 'component_type': 'Resistor'},
        ]
        clusters2 = [
            {'count': 2, 'center_x': 10.0, 'center_y': 10.0, 'width': 2.0, 'height': 1.0, 'component_type': 'Resistor'},
        ]
        
        result1 = assign_refdes(clusters1)
        result2 = assign_refdes(clusters2)
        
        assert result1[0]['refdes'] == 'R1'
        assert result2[0]['refdes'] == 'R1'
    
    def test_estimate_rotation_wide(self):
        """测试宽元件旋转"""
        cluster = {'width': 5.0, 'height': 1.0}
        assert estimate_rotation(cluster) == 0
    
    def test_estimate_rotation_tall(self):
        """测试高元件旋转"""
        cluster = {'width': 1.0, 'height': 5.0}
        assert estimate_rotation(cluster) == 90
    
    def test_estimate_rotation_square(self):
        """测试方形元件旋转"""
        cluster = {'width': 2.0, 'height': 2.0}
        assert estimate_rotation(cluster) == 0
    
    def test_estimate_rotation_zero(self):
        """测试零尺寸元件旋转"""
        cluster = {'width': 0, 'height': 0}
        assert estimate_rotation(cluster) == 0
    
    def test_generate_pnp(self, sample_clusters):
        """测试生成 PNP 文件"""
        clusters_with_refdes = assign_refdes(sample_clusters)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            generate_pnp(clusters_with_refdes, [], csv_path)
            assert os.path.exists(csv_path)
            
            import csv
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 4
            assert rows[0]['Designator'] == 'R1'
            assert 'Mid X' in rows[0]
            assert 'Mid Y' in rows[0]
        finally:
            os.unlink(csv_path)
    
    def test_generate_pnp_simple(self, sample_clusters):
        """测试生成简易 PNP 文件"""
        clusters_with_refdes = assign_refdes(sample_clusters)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            generate_pnp_simple(clusters_with_refdes, csv_path)
            assert os.path.exists(csv_path)
            
            with open(csv_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 5
            assert 'Designator' in lines[0]
        finally:
            os.unlink(csv_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
