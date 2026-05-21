# 迁移指南 (MIGRATION GUIDE)

## 从 v0.x (旧版) 升级到 v1.0

### 破坏性变更

无。v1.0 保持 100% 向后兼容。

### 新增依赖

```bash
pip install pyyaml pytest
```

### 新增功能

1. **封装库系统** — 新增 `package_library.py`，默认库位于 `config/packages/default_library.json`
   - 旧版硬编码识别逻辑保留为 `_guess_component_type_legacy()` 兜底
   - 不传 `--package-lib` 时自动加载默认库，行为与旧版一致

2. **CSV 输出扩展** — 使用新引擎时，`components.csv` 新增 3 列：
   - `confidence` — 置信度 (0-100)
   - `category` — 分类 (passive/ic/connector/discrete)
   - `package_id` — 匹配的封装 ID
   - 不使用新引擎时，输出格式与旧版完全一致

3. **PNP 文件生成** — 新增 `pnp.py` 和 `validate_pnp.py`

4. **置信度可视化** — 新增 `confidence.png`，按绿/黄/红三色显示识别置信度

### 命令行变化

新增参数（向后兼容）：

| 参数 | 说明 |
|------|------|
| `--package-lib PATH` | 自定义封装库路径 |
| `--list-packages` | 列出所有封装定义 |
| `--validate-config PATH` | 验证配置文件格式 |

### 验证步骤

```bash
# 1. 安装新依赖
pip install -r requirements.txt

# 2. 验证旧版脚本不受影响
python main.py -i input/ -o output_test_legacy/

# 3. 验证新版功能
python main.py --list-packages
python main.py --validate-config config/packages/default_library.json

# 4. 运行单元测试
python -m pytest tests/ -v
```
