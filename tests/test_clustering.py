"""
PadClustering 单元测试
"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from clustering import PadClustering


class TestPadClustering:
    """PadClustering 测试类"""
    
    @pytest.fixture
    def sample_pads(self):
        return [
            {'x': 10.0, 'y': 10.0, 'shape': 'circle', 'width': 1.0, 'height': 1.0},
            {'x': 10.5, 'y': 10.0, 'shape': 'circle', 'width': 1.0, 'height': 1.0},
            {'x': 11.0, 'y': 10.0, 'shape': 'circle', 'width': 1.0, 'height': 1.0},
            {'x': 50.0, 'y': 50.0, 'shape': 'rect', 'width': 2.0, 'height': 1.5},
            {'x': 50.5, 'y': 50.0, 'shape': 'rect', 'width': 2.0, 'height': 1.5},
        ]
    
    def test_fit_empty_pads(self):
        """测试空焊盘列表"""
        clusterer = PadClustering(verbose=False)
        result = clusterer.fit([])
        assert result == []
    
    def test_fit_single_pad(self):
        """测试单个焊盘"""
        pads = [{'x': 10.0, 'y': 10.0, 'shape': 'circle', 'width': 1.0, 'height': 1.0}]
        clusterer = PadClustering(verbose=False)
        clusters = clusterer.fit(pads)
        assert len(clusters) == 1
        assert clusters[0]['count'] == 1
    
    def test_fit_clusters_nearby_pads(self, sample_pads):
        """测试邻近焊盘聚类"""
        clusterer = PadClustering(threshold=2.0, verbose=False)
        clusters = clusterer.fit(sample_pads)
        
        assert len(clusters) == 2
        assert clusters[0]['count'] == 3
        assert clusters[1]['count'] == 2
    
    def test_fit_separate_clusters(self):
        """测试分离的聚类"""
        pads = [
            {'x': 0.0, 'y': 0.0, 'shape': 'circle', 'width': 1.0, 'height': 1.0},
            {'x': 100.0, 'y': 100.0, 'shape': 'circle', 'width': 1.0, 'height': 1.0},
        ]
        clusterer = PadClustering(threshold=2.0, verbose=False)
        clusters = clusterer.fit(pads)
        assert len(clusters) == 2
    
    def test_add_component_type_no_duplicate(self, sample_pads):
        """测试 add_component_type 不重复执行"""
        clusterer = PadClustering(threshold=2.0, verbose=False)
        clusters = clusterer.fit(sample_pads)
        
        clusterer.add_component_type()
        first_types = [c.get('component_type') for c in clusters]
        
        clusterer.add_component_type()
        second_types = [c.get('component_type') for c in clusters]
        
        assert first_types == second_types
    
    def test_guess_component_type_legacy_2_pads(self):
        """测试遗留逻辑 2 焊盘识别"""
        clusterer = PadClustering(verbose=False)
        
        cluster = {'count': 2, 'width': 5.0, 'height': 1.0}
        result = clusterer._guess_component_type_legacy(cluster)
        assert 'Resistor' in result or 'Capacitor' in result
    
    def test_guess_component_type_legacy_1_pad(self):
        """测试遗留逻辑 1 焊盘识别"""
        clusterer = PadClustering(verbose=False)
        
        cluster = {'count': 1, 'width': 1.0, 'height': 1.0}
        result = clusterer._guess_component_type_legacy(cluster)
        assert result == 'Unknown'
    
    def test_guess_component_type_legacy_3_pads(self):
        """测试遗留逻辑 3 焊盘识别"""
        clusterer = PadClustering(verbose=False)
        
        cluster = {'count': 3, 'width': 2.0, 'height': 1.0}
        result = clusterer._guess_component_type_legacy(cluster)
        assert result == 'Unknown'
    
    def test_guess_component_type_legacy_qfp(self):
        """测试遗留逻辑 QFP 识别"""
        clusterer = PadClustering(verbose=False)
        
        cluster = {'count': 32, 'width': 10.0, 'height': 10.0}
        result = clusterer._guess_component_type_legacy(cluster)
        assert result == 'QFP-32'
    
    def test_save_csv(self, sample_pads):
        """测试保存 CSV"""
        clusterer = PadClustering(threshold=2.0, verbose=False)
        clusterer.fit(sample_pads)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            clusterer.save_csv(csv_path)
            assert os.path.exists(csv_path)
            
            import csv
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2
            assert 'component_type' in rows[0]
            assert 'pad_count' in rows[0]
        finally:
            os.unlink(csv_path)
    
    def test_get_summary(self, sample_pads):
        """测试获取统计摘要"""
        clusterer = PadClustering(threshold=2.0, verbose=False)
        clusterer.fit(sample_pads)
        clusterer.add_component_type()
        
        summary = clusterer.get_summary()
        assert isinstance(summary, dict)
        assert sum(summary.values()) == 2
    
    def test_get_summary_empty(self):
        """测试空聚类统计"""
        clusterer = PadClustering(verbose=False)
        assert clusterer.get_summary() == {}
    
    def test_match_drills_to_cluster(self, sample_pads):
        """测试钻孔匹配"""
        drills = [
            {'x': 10.0, 'y': 10.0, 'diameter': 0.8, 'plated': 'plated', 'type': 'round'},
        ]
        
        clusterer = PadClustering(threshold=2.0, verbose=False, drills=drills)
        clusterer.fit(sample_pads)
        
        first_cluster = clusterer.clusters[0]
        assert first_cluster.get('has_drill') is True
        assert first_cluster.get('mount_type') == 'through-hole'
    
    def test_no_drills_means_smd(self, sample_pads):
        """测试无钻孔时为贴片"""
        clusterer = PadClustering(threshold=2.0, verbose=False)
        clusterer.fit(sample_pads)
        
        for cluster in clusterer.clusters:
            assert cluster.get('mount_type') is None or cluster.get('mount_type') == 'smd'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
