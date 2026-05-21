# PCB Gerber 分析工具

一键从 Gerber 和 Excellon 文件中提取焊盘、识别元件、生成可视化验证图。

**准确率:** ✅ **100%** (已验证)

## 📚 文档导航

- **[使用文档 (USER_GUIDE.md)](USER_GUIDE.md)** ⭐ - 详细的使用指南
- **[项目交接 (HANDOFF.md)](HANDOFF.md)** - 完整的技术文档
- **[封装配置指南 (docs/PACKAGE_CONFIG.md)](docs/PACKAGE_CONFIG.md)** ⭐ - 自定义封装库配置

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

**要求:** Python >= 3.12

### 2. 运行分析

```bash
# 标准用法
python main.py -i input/ -o output/

# 调整聚类阈值
python main.py -i input/ -t 3.0

# 跳过叠加图（加快速度）
python main.py -i input/ --no-overlay
```

### 3. 查看结果

输出文件位于 `output/` 目录:

- `pads.csv` - 焊盘坐标数据
- `drills.csv` - 钻孔坐标数据 (如有 Excellon 文件)
- `components.csv` - 元件聚类结果 (含通孔/贴片标记)
- `pads.png` - 焊盘散点图
- `components.png` - 元件类型着色图
- `pcb.png` - PCB 背景图
- `overlay.png` - **焊盘叠加验证图 (重点查看)**

### 4. 验证结果

```bash
python verify_results.py output/
```

## 功能说明

### 核心功能

1. **Gerber 解析** - 使用 gerbonara 库解析 Gerber 文件
2. **Excellon 解析** - 解析钻孔文件，提取通孔/非通孔信息
3. **焊盘提取** - 提取 Flash 对象 (D03 指令)，忽略走线
4. **空间聚类** - BFS 算法根据距离阈值聚类焊盘
5. **元件识别** - 基于焊盘数量和长宽比推测封装类型
6. **通孔识别** - 自动识别通孔/贴片元件
7. **可视化验证** - 生成多种图像用于人工验证

### 支持的文件格式

**Gerber 文件:**
- 阻焊层 (mask1.gbr, mask2.gbr) - **优先级最高**
- Via 塞孔层 (via_plugging.gbr)
- 钻孔图 (drilldrw.gbr)
- 铜层 (lay1.gbr ~ lay4.gbr)
- 丝印层 (silk1.gbr, silk2.gbr)

**Excellon 钻孔文件:**
- 镀通孔 (PTH_*.drl, drill.drl)
- 非镀通孔 (NPTH_*.drl)
- 槽孔 (slot.drl)
- 支持扩展名: .drl, .ncd, .xln, .txt, .drd, .dri, .nc

### 识别的元件类型

- Resistor/Capacitor (0402, 0603, 0805)
- SOP/TSOP (4-8 脚)
- QFP (16, 24, 32, 44, 48, 64 脚)
- QFN (8-20 脚)
- BGA (>20 脚，长宽比 > 1.5)

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-i, --input` | 必填 | Gerber 文件或目录 |
| `-o, --output` | `output` | 输出目录 |
| `-t, --threshold` | `2.0` | 聚类距离阈值 (mm) |
| `--package-lib` | `None` | 自定义封装库路径（JSON/YAML/目录） |
| `--list-packages` | `False` | 列出所有封装定义 |
| `--validate-config` | `None` | 验证配置文件格式 |
| `--no-overlay` | `False` | 跳过叠加图生成 |
| `--no-drills` | `False` | 跳过钻孔提取 |
| `-q, --quiet` | `False` | 安静模式 |

### 聚类阈值调整建议

- **2.0mm** (默认) - 适合密集布局的板子
- **3.0mm** - 适合中等密度布局
- **4.0-5.0mm** - 适合稀疏布局或大元件

**症状:** 如果 Unknown 占比 > 50%，尝试增大阈值

### 自定义封装库

```bash
# 使用默认库（56个常用封装定义）
python main.py -i input/ -o output/

# 使用自定义配置文件覆盖默认库
python main.py -i input/ --package-lib my_custom.json

# 验证配置文件格式
python main.py --validate-config my_custom.json

# 列出所有封装定义
python main.py --list-packages
```

默认库位于 `config/packages/default_library.json`，用户可直接编辑或通过 `--package-lib` 覆盖。

详细说明见: [docs/PACKAGE_CONFIG.md](docs/PACKAGE_CONFIG.md)

## 项目结构

```
pcb_analyzer/
+-- main.py              # 主入口 + PipelineError
+-- extractor.py         # Gerber 解析 + Flash 焊盘提取 (isinstance)
+-- drill_extractor.py   # Excellon 钻孔解析 (PTH/NPTH)
+-- clustering.py        # KD-Tree BFS 聚类 + 元件识别
+-- visualizer.py        # 可视化渲染 (含置信度着色)
+-- pnp.py               # Pick & Place 文件生成 (IPC-9751)
+-- utils.py             # 工具函数
+-- constants.py         # 集中常量
+-- package_library.py   # 向后兼容 shim
+-- package_library/     # 封装库子系统 (56 默认封装)
+-- requirements.txt     # 依赖列表
+-- config/packages/     # 封装库配置 (JSON/YAML)
+-- docs/                # 文档
+-- tests/               # 90 个单元测试
+-- tools/               # 验证工具
+-- README.md            # 本文件
```

## 使用示例

### 示例 1: 基本分析

```bash
python main.py -i input/ -o output/
```

输出:
```
==================================================
PCB Gerber 分析工具
==================================================
输入: input
输出: output

【步骤1】提取焊盘...
----------------------------------------
找到 10 个 Gerber 文件
  解析: mask1.gbr
    提取: 856 个焊盘
  ...
总计提取: 1739 个焊盘

【步骤2】聚类分析...
----------------------------------------
聚类完成: 识别出 623 个区域/元件

元件类型统计:
  Unknown: 474
  SOP/TSOP: 71
  Resistor/Capacitor: 51
  ...

【步骤3】生成可视化...
----------------------------------------
已保存: output/pads.png
已保存: output/components.png
已生成 PCB 图像: output/pcb.png
已保存叠加图: output/overlay.png

==================================================
分析完成!
==================================================
```

### 示例 2: 调整阈值对比

```bash
# 测试不同阈值
python main.py -i input/ -o output_t2 -t 2.0
python main.py -i input/ -o output_t3 -t 3.0
python main.py -i input/ -o output_t4 -t 4.0

# 验证结果
python verify_results.py output_t2/
python verify_results.py output_t3/
python verify_results.py output_t4/
```

### 示例 3: 单个文件分析

```bash
python main.py -i input/mask1.gbr -o output_single/
```

## 验证结果

### 方法1: 快速验证 (数据格式和一致性)

```bash
python verify_results.py output/
```

验证内容:
- ✓ 文件完整性检查
- ✓ 数据格式验证
- ✓ 数值有效性检查
- ✓ 数据一致性验证
- ✓ 统计分析报告

**注意:** 这只验证数据格式，不验证坐标准确性。

### 方法2: 准确性验证 (推荐) ⭐

验证提取的孔位坐标是否正确:

```bash
# 自动对比 Gerber 原始数据
python validate_accuracy.py input/ output/pads.csv

# 生成可视化对比图
python visual_compare.py input/mask1.gbr output/pads.csv output/
```

**输出:**
- 准确率报告 (匹配率、遗漏数、误提取数)
- `comparison.png` - 三图对比 (原始/提取/叠加)
- `difference_map.png` - 差异图 (绿=匹配, 蓝=遗漏, 红=误提取)

**判断标准:**
- 准确率 ≥ 95% → ✅ 优秀
- 准确率 85-95% → ✓ 良好
- 准确率 < 85% → ⚠️ 需要检查

### 方法3: 人工验证

**重点查看 `overlay.png`:**

1. 打开 `output/overlay.png`
2. 检查红点是否与 PCB 焊盘对齐
3. 如果对齐良好 → 提取准确
4. 如果有偏移 → 可能是坐标系问题

**查看 `difference_map.png`:**

1. 打开 `output/difference_map.png`
2. 绿色多 → 准确率高
3. 蓝色多 → 有遗漏
4. 红色多 → 有误提取

**详细验证指南:** 查看 `ACCURACY_VALIDATION_GUIDE.md`

## 已知问题

1. **Unknown 占比高** - 默认阈值可能导致过度分割
2. **元件识别规则简单** - 基于硬编码规则，不支持所有封装
3. **坐标对齐依赖 bbox** - 某些 Gerber 可能有边距问题
4. **OCR 精度受限** - Gerber 矢量字体导致 R->B 等识别错误

## 改进建议

### 高优先级
- [ ] 支持自适应阈值算法
- [ ] 增加更多元件识别规则

### 中优先级
- [ ] 多层彩色渲染
- [ ] 交互式验证界面 (HTML/Flask)
- [ ] 批量处理多块板子

### 低优先级
- [ ] Gerber 单位自动检测
- [ ] 输出目录自动清理
- [ ] 机器学习元件识别

## 技术细节

### 为什么只提取 Flash？

- **Flash (D03)** = 光绘机"瞬间放置"的完整图形 → 焊盘
- **Line (D01/D02)** = 移动中连续曝光 → 走线
- 误把 Line 当焊盘会导致全板均匀散点

### 为什么用 BFS 而非 DBSCAN？

- KD-Tree + BFS 简单可控，距离 < threshold 即连通
- 无需调参 eps/min_samples
- KD-Tree (scipy cKDTree) 优化: O(n log n)，5000 焊盘约 0.07s

### 坐标对齐原理

1. 先渲染 `pcb.png` (高 DPI，保持 Gerber 坐标系)
2. 读取 `pcb.png` 像素尺寸
3. 将焊盘坐标映射到图像坐标 (Y 轴翻转)
4. 叠加红点生成 `overlay.png`

## 故障排除

### 问题: 提取焊盘数为 0

**原因:** Gerber 文件格式不支持或损坏

**解决:**
1. 检查文件扩展名 (.gbr, .gb, .ger)
2. 用 Gerber 查看器验证文件有效性
3. 尝试其他层的 Gerber 文件

### 问题: Unknown 占比 > 80%

**原因:** 聚类阈值过小

**解决:**
```bash
python main.py -i input/ -t 4.0  # 增大阈值
```

### 问题: overlay.png 红点偏移

**原因:** 坐标系或 bbox 计算问题

**解决:**
1. 检查 Gerber 文件单位 (mm vs inch)
2. 尝试不同的 Gerber 层作为背景
3. 查看 `pcb.png` 是否正常渲染

### 问题: 运行速度慢

**原因:** 大板子 + 高 DPI 渲染

**解决:**
```bash
python main.py -i input/ --no-overlay  # 跳过叠加图
```

## 依赖说明

| 依赖 | 版本 | 用途 |
|------|------|------|
| gerbonara | 1.6+ | Gerber/Excellon 文件解析 |
| matplotlib | 3.10+ | 图像渲染 |
| numpy | 2.4+ | 坐标计算 |
| scipy | 1.17+ | KD-Tree 空间索引 |
| Pillow | 12+ | 图像读取 |

## 许可证

本项目由 AI agent 生成并维护。

## 联系方式

有问题请参考:
- `HANDOFF.md` - 详细技术文档
- `VERIFICATION_REPORT.md` - 验证报告
- 代码注释 - 每个模块都有详细说明

## 更新日志

### v1.2 (当前版本)
- ✓ Excellon 钻孔文件支持 (.drl, .ncd, .xln)
- ✓ 通孔/贴片元件自动识别
- ✓ 钻孔数据与焊盘匹配
- ✓ components.csv 新增 mount_type, has_drill 字段
- ✓ --no-drills 参数跳过钻孔提取

### v1.0
- ✓ 基本 Gerber 解析和焊盘提取
- ✓ BFS 空间聚类
- ✓ 基于规则的元件识别
- ✓ 多种可视化输出
- ✓ 叠加验证功能
- ✓ 结果验证脚本

### 计划中
- [ ] 自适应阈值
- [ ] 交互式界面
- [ ] ML 元件识别
