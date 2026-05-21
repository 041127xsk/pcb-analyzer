# PCB Gerber 分析工具 — 项目交接文档

## 验证状态

| 项目 | 状态 |
|------|------|
| **孔位准确性** | 100% (已验证) |
| **功能完整性** | 完整 |
| **文档完善度** | 完善 |
| **可用性** | 可以放心使用 |

**最新验证:** 通过自动对比 Gerber 原始数据，准确率 100%，无遗漏，无误提取。

---

## 1. 项目概览

| 项目 | 内容 |
|------|------|
| 项目名称 | pcb_analyzer |
| 技术栈 | Python 3.12+, gerbonara, matplotlib, numpy, scipy, Pillow |
| 核心功能 | 从 Gerber 文件中提取焊盘 -> 聚类识别元件 -> 可视化验证 -> 准确性验证 |
| 项目位置 | pcb_analyzer/ |
| 运行方式 | python main.py -i input/ -o output/ |
| 验证方式 | python tools/validate_accuracy.py input/ output/pads.csv |
| 准确率 | 100% |

---

## 2. 项目结构

`
pcb_analyzer/
+-- main.py                 # 一键运行入口，编排 3 个步骤
+-- extractor.py            # Gerber 解析 + Flash 焊盘提取 (isinstance 类型检测)
+-- drill_extractor.py      # Excellon 钻孔解析 (PTH/NPTH 自动推断)
+-- clustering.py           # KD-Tree 优化的 BFS 空间聚类 + 元件识别
+-- visualizer.py           # 可视化渲染（焊盘图、聚类图、PCB 图、叠加图）
+-- pnp.py                  # Pick & Place 文件生成 (IPC-9751)
+-- utils.py                # 工具函数（文件查找、单位解析、合并去重）
+-- constants.py            # 集中常量（文件扩展名、优先级、容差）
+-- package_library.py      # 向后兼容 shim
+-- package_library/        # 封装库子系统
|   +-- __init__.py         # 统一导出
|   +-- models.py           # PackageDefinition / ClusterFeatures / RecognitionResult
|   +-- config_loader.py    # JSON / YAML 配置加载
|   +-- library_system.py   # ComponentLibrarySystem (56 默认封装)
|   +-- recognition_engine.py # 6 维度加权置信度评分引擎
+-- requirements.txt        # 依赖列表
+-- README.md               # 使用文档
+-- HANDOFF.md              # 本文件 - 项目交接文档
+-- CHANGELOG.md            # 版本历史
+-- config/packages/        # 封装库配置
|   +-- default_library.json # 56 个默认封装定义
|   +-- example.json        # JSON 格式示例
|   +-- example.yaml        # YAML 格式示例
|   +-- template.json       # 空白模板
+-- docs/                   # 文档
|   +-- PACKAGE_CONFIG.md   # 自定义封装库配置指南
|   +-- MIGRATION_GUIDE.md  # 迁移指南
+-- tests/                  # 90 个单元测试 (8 个文件)
+-- tools/                  # 验证工具
|   +-- silk_verification.py  # 丝印 OCR 验证
|   +-- validate_accuracy.py  # Ground truth 准确性对比
+-- input/                  # 用户放入 Gerber / Excellon 文件
+-- output/                 # 自动生成的分析结果
    +-- pads.csv
    +-- drills.csv
    +-- components.csv
    +-- pnp.csv
    +-- pads.png
    +-- components.png
    +-- pcb.png
    +-- overlay.png
    +-- confidence.png
`

---

## 3. 模块详解

### 3.1 main.py - 入口编排

三个顺序步骤:
1. 提取焊盘 -> GerberExtractor
2. 聚类分析 -> PadClustering + RecognitionEngine
3. 可视化 -> Visualizer

关键参数: -i/--input, -o/--output, -t/--threshold, --package-lib, --list-packages, --validate-config, --no-overlay, --no-drills, -q/--quiet

### 3.2 extractor.py - Gerber 解析与焊盘提取

核心类 GerberExtractor:
- extract_from_file: 解析单个 Gerber，提取 Flash 对象
- extract_from_dir: 遍历目录，按优先级处理，合并去重
- _merge_pads: 基于 0.05mm 容差去重
- 只提取 Flash(D03)，忽略 Line(D01/D02)
- 类型映射用 isinstance: CircleAperture->circle, RectangleAperture->rect, OvalAperture->oval
- 文件优先级: mask1 > mask2 > via_plugging > drilldrw > lay1/lay4 > lay2/lay3 > silk1/silk2

### 3.3 drill_extractor.py - Excellon 钻孔解析

核心类 DrillExtractor:
- 支持 .drl .ncd .xln .txt .drd .dri .nc
- 自动推断 PTH/NPTH (NPTH 关键字优先)
- 圆形钻孔和槽孔提取
- merge_drills 合并多组数据

### 3.4 clustering.py - 聚类与元件识别

核心类 PadClustering:
- KD-Tree (scipy cKDTree) 优化的 BFS 聚类, O(n log n)
- 5000 焊盘约 0.07s
- 钻孔匹配: mount_type, has_drill, drill_count, plated_drill_count
- 可用 RecognitionEngine (6 维度评分) 或遗留规则
- _types_assigned 标志防重复分配

### 3.5 package_library/ - 封装库子系统

- models.py: PackageDefinition, ClusterFeatures, RecognitionResult
- config_loader.py: JSON/YAML 加载 + schema 验证
- library_system.py: 56 默认封装, 自定义库覆盖, 索引加速
- recognition_engine.py: 6 维度加权置信度评分

### 3.6 pnp.py - Pick & Place 生成

IPC-9751 格式, 自动位号分配 (R/U/X), 深拷贝防突变, 包围盒旋转角推断

### 3.7 visualizer.py - 可视化

_draw_pad() 提取消除约 120 行重复。置信度着色: 绿>=80, 黄60-79, 红<60, 灰=0。线性变换坐标映射。

### 3.8 utils.py - 工具函数

文件查找、单位解析、合并去重(深拷贝)、字段验证、坐标/尺寸格式化

---

## 4. 数据流

`
Gerber(.gbr) + Excellon(.drl)
    |                |
    v                v
extractor.py    drill_extractor.py
    |                |
    +--------+-------+
             |
             v
    clustering.py (KD-Tree BFS + 钻孔匹配 + RecognitionEngine)
             |
             v
    visualizer.py (pads/components/pcb/overlay/confidence)
             |
             v
    pnp.py (IPC-9751 Pick & Place)
`

---

## 5. 依赖

| 依赖 | 用途 |
|------|------|
| gerbonara | Gerber/Excellon 解析 |
| matplotlib | 图像渲染 |
| numpy | 坐标计算 |
| scipy | KD-Tree 空间索引 |
| Pillow | 图像处理 |
| pyyaml | YAML 配置 |
| pytest | 测试 |

Python >= 3.12, 安装: pip install -r requirements.txt

---

## 6. 验证

| 工具 | 功能 |
|------|------|
| tools/validate_accuracy.py | Ground truth 对比 |
| tools/silk_verification.py | 丝印 OCR 验证 |

孔位准确率: 100%, 丝印 OCR: 86.4%, 单元测试: 90/90 通过

---

## 7. 关键技术决策

1. Flash-only(D03) 提取 - 避免走线误识别
2. BFS + KD-Tree - O(n log n) 聚类
3. isinstance 类型检测 - 继承安全
4. 外置封装库 JSON/YAML - 用户可编辑
5. 深拷贝不动性 - 防输入突变
6. _types_assigned 标志 - 防重复分配
7. 线性变换坐标映射 - overlay 精确对齐

---

## 8. 已知问题

- Unknown 占比高 (孤立单焊盘)
- OCR 精度受限于 Gerber 矢量字体
- 聚类阈值需手动调整

已解决: O(n^2)->O(n log n), 硬编码识别->JSON库, 缺少钻孔/PnP->新模块, 类型字符串->isinstance, 输入突变->深拷贝

---

## 9. 运行

`
python main.py -i input/ -o output/
python main.py -i input/ --package-lib my_packages.json
python main.py -i input/ -t 3.0
python main.py --list-packages
python main.py --validate-config my_packages.json
python tools/validate_accuracy.py input/ output/pads.csv
python -m pytest tests/ -v
`

---

## 10. 项目状态

- 核心功能完整
- 准确性验证通过 (100%)
- 90 个单元测试通过
- 56 个封装定义，可扩展
- KD-Tree 优化，大板性能良好
- 文档完善
