"""RecognitionEngine 单元测试"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from package_library import (
    ComponentLibrarySystem, RecognitionEngine,
    ClusterFeatures, PackageDefinition
)


def _make_lib():
    """创建一个最小测试库"""
    return ComponentLibrarySystem()


def _make_cluster(pad_count=2, width=1.0, height=0.5):
    return {
        'count': pad_count,
        'width': width,
        'height': height,
        'indices': list(range(pad_count)),
    }


def _make_pads(count=2, shape='rect'):
    pads = []
    for i in range(count):
        pads.append({
            'x': float(i) * 0.5,
            'y': 0.0,
            'shape': shape,
            'width': 0.3,
            'height': 0.3,
        })
    return pads


def test_engine_initialization():
    lib = _make_lib()
    engine = RecognitionEngine(lib)
    assert engine is not None


def test_extract_features():
    lib = _make_lib()
    engine = RecognitionEngine(lib)
    cluster = _make_cluster(2, 1.0, 0.5)
    pads = _make_pads(2)
    features = engine.extract_features(cluster, pads)
    assert features.pad_count == 2
    assert features.width == 1.0
    assert features.height == 0.5
    assert features.aspect_ratio == 2.0
    assert features.layout_pattern is not None


def test_match_package_resistor():
    lib = _make_lib()
    engine = RecognitionEngine(lib)
    cluster = _make_cluster(2, 0.6, 0.4)
    pads = _make_pads(2)
    features = engine.extract_features(cluster, pads)
    matches = engine.match_package(features)
    assert len(matches) > 0
    best_pkg, best_conf = matches[0]
    assert best_conf > 0


def test_select_best_match_high_confidence():
    lib = _make_lib()
    engine = RecognitionEngine(lib)
    features = ClusterFeatures(pad_count=2, width=0.6, height=0.4, aspect_ratio=1.5)
    pkg = PackageDefinition(
        id="TEST", type="resistor", pad_count=2,
        width_min=0.4, width_max=0.8, height_min=0.2, height_max=0.6,
        aspect_ratio_min=1.0, aspect_ratio_max=3.0,
        category="passive",
    )
    matches = [(pkg, 85.0)]
    result = engine.select_best_match(matches, threshold=60)
    assert result.confidence == 85.0
    assert result.matched_package_id == "TEST"


def test_select_best_match_low_confidence():
    lib = _make_lib()
    engine = RecognitionEngine(lib)
    pkg = PackageDefinition(
        id="TEST", type="resistor", pad_count=2,
        width_min=0.4, width_max=0.8, height_min=0.2, height_max=0.6,
        aspect_ratio_min=1.0, aspect_ratio_max=3.0,
        category="passive",
    )
    matches = [(pkg, 30.0)]
    result = engine.select_best_match(matches, threshold=60)
    assert result.component_type == "Unknown"


def test_recognize_full_flow():
    lib = _make_lib()
    engine = RecognitionEngine(lib)
    cluster = _make_cluster(8, 4.0, 3.0)
    pads = _make_pads(8)
    result = engine.recognize(cluster, pads)
    assert result is not None
    assert result.confidence >= 0


def test_layout_detection_single():
    lib = _make_lib()
    engine = RecognitionEngine(lib)
    pads = _make_pads(1)
    cluster = _make_cluster(1, 0.5, 0.5)
    features = engine.extract_features(cluster, pads[:1])
    assert features.layout_pattern == 'single'
