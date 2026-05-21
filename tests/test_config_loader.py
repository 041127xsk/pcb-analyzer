"""ConfigLoader 单元测试"""

import sys, json, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from package_library import ConfigLoader


def test_load_json_invalid(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{invalid json}", encoding='utf-8')
    try:
        ConfigLoader.load_json(str(p))
        assert False, "should raise"
    except json.JSONDecodeError:
        pass


def test_validate_config_valid():
    data = {
        "packages": [
            {
                "id": "TEST_1", "type": "resistor", "pad_count": 2,
                "width_min": 0.4, "width_max": 0.8,
                "height_min": 0.2, "height_max": 0.6,
            }
        ]
    }
    valid, errors = ConfigLoader.validate_config(data)
    assert valid, f"expected valid, got errors: {errors}"
    assert len(errors) == 0


def test_validate_config_missing_id():
    data = {
        "packages": [
            {
                "type": "resistor", "pad_count": 2,
                "width_min": 0.4, "width_max": 0.8,
                "height_min": 0.2, "height_max": 0.6,
            }
        ]
    }
    valid, errors = ConfigLoader.validate_config(data)
    assert not valid
    assert any('id' in err for err in errors)


def test_validate_config_missing_packages():
    data = {}
    valid, errors = ConfigLoader.validate_config(data)
    assert not valid
    assert any('packages' in err for err in errors)


def test_validate_config_wrong_type():
    data = {"packages": "not_a_list"}
    valid, errors = ConfigLoader.validate_config(data)
    assert not valid


def test_validate_config_width_mismatch():
    data = {
        "packages": [{
            "id": "T", "type": "resistor", "pad_count": 2,
            "width_min": 1.0, "width_max": 0.5,
            "height_min": 0.2, "height_max": 0.6,
        }]
    }
    valid, errors = ConfigLoader.validate_config(data)
    assert not valid


def test_scan_directory(tmp_path):
    (tmp_path / "test.json").write_text('{"packages":[]}', encoding='utf-8')
    (tmp_path / "test.yaml").write_text('packages: []', encoding='utf-8')
    (tmp_path / "readme.txt").write_text('hello', encoding='utf-8')

    files = ConfigLoader.scan_directory(str(tmp_path))
    assert len(files) == 2
    assert all(f.suffix in ('.json', '.yaml', '.yml') for f in files)


def test_load_json_file(tmp_path):
    p = tmp_path / "test.json"
    p.write_text('{"packages": [{"id":"X","type":"r","pad_count":2,"width_min":1,"width_max":2,"height_min":1,"height_max":2}]}', encoding='utf-8')
    data = ConfigLoader.load_file(str(p))
    assert 'packages' in data
    assert len(data['packages']) == 1


def test_load_file_unsupported(tmp_path):
    p = tmp_path / "test.txt"
    p.write_text("hello", encoding='utf-8')
    try:
        ConfigLoader.load_file(str(p))
        assert False, "should raise"
    except ValueError:
        pass
