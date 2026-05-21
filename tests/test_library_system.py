"""ComponentLibrarySystem 单元测试"""

import sys, os, tempfile, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from package_library import ComponentLibrarySystem, PackageDefinition


def test_default_library_loaded():
    lib = ComponentLibrarySystem()
    pkgs = lib.get_all_packages()
    assert len(pkgs) > 0
    assert all(isinstance(p, PackageDefinition) for p in pkgs)


def test_default_library_has_resistors():
    lib = ComponentLibrarySystem()
    pkgs = lib.find_packages_by_pad_count(2)
    resistors = [p for p in pkgs if p.type == 'resistor']
    assert len(resistors) >= 4


def test_default_library_has_sop():
    lib = ComponentLibrarySystem()
    pkgs = lib.find_packages_by_pad_count(8)
    sop = [p for p in pkgs if 'sop' in p.type]
    assert len(sop) >= 1


def test_get_package_by_id():
    lib = ComponentLibrarySystem()
    pkg = lib.get_package_by_id('R_0402')
    assert pkg is not None
    assert pkg.type == 'resistor'
    assert pkg.pad_count == 2


def test_get_package_by_id_not_found():
    lib = ComponentLibrarySystem()
    pkg = lib.get_package_by_id('NONEXISTENT')
    assert pkg is None


def test_find_packages_by_pad_count_exact():
    lib = ComponentLibrarySystem()
    pkgs = lib.find_packages_by_pad_count(8)
    assert all(p.pad_count == 8 for p in pkgs)


def test_find_packages_by_pad_count_with_tolerance():
    lib = ComponentLibrarySystem()
    pkgs = lib.find_packages_by_pad_count(7, tolerance=1)
    assert all(6 <= p.pad_count <= 8 for p in pkgs)


def test_custom_library_override(tmp_path):
    custom = tmp_path / "custom.json"
    custom.write_text(json.dumps({
        "packages": [{
            "id": "R_0402",
            "type": "resistor",
            "pad_count": 2,
            "width_min": 0.3, "width_max": 0.9,
            "height_min": 0.1, "height_max": 0.7,
            "aspect_ratio_min": 1.0, "aspect_ratio_max": 5.0,
            "category": "passive",
            "description": "Custom override 0402"
        }]
    }), encoding='utf-8')

    lib = ComponentLibrarySystem(custom_lib_path=str(custom))
    pkg = lib.get_package_by_id('R_0402')
    assert pkg is not None
    assert pkg.width_min == 0.3


def test_custom_library_add_new(tmp_path):
    custom = tmp_path / "new.json"
    custom.write_text(json.dumps({
        "packages": [{
            "id": "MY_CUSTOM_CHIP",
            "type": "other",
            "pad_count": 2,
            "width_min": 1.0, "width_max": 2.0,
            "height_min": 1.0, "height_max": 2.0,
            "category": "other",
            "description": "Custom chip"
        }]
    }), encoding='utf-8')

    lib = ComponentLibrarySystem(custom_lib_path=str(custom))
    pkg = lib.get_package_by_id('MY_CUSTOM_CHIP')
    assert pkg is not None
    assert pkg.pad_count == 2


def test_library_index_built():
    lib = ComponentLibrarySystem()
    assert hasattr(lib, '_pad_count_index')
    assert 2 in lib._pad_count_index
    assert 8 in lib._pad_count_index


def test_library_category_index():
    lib = ComponentLibrarySystem()
    assert 'passive' in lib._category_index
    assert 'ic' in lib._category_index
    assert 'connector' in lib._category_index


def test_list_packages_output(capsys):
    lib = ComponentLibrarySystem()
    lib.list_packages()
    captured = capsys.readouterr()
    assert 'R_0402' in captured.out
    assert 'Total:' in captured.out


def test_list_packages_filter_by_category(capsys):
    lib = ComponentLibrarySystem()
    lib.list_packages(category='passive')
    captured = capsys.readouterr()
    assert 'R_0402' in captured.out
    assert 'SOP_8' not in captured.out
