# PCB Gerber 分析工具 - 使用文档

## 📖 目录

1. [快速开始](#快速开始)
2. [安装配置](#安装配置)
3. [基本使用](#基本使用)
4. [高级功能](#高级功能)
5. [验证结果](#验证结果)
6. [参数说明](#参数说明)
7. [输出文件](#输出文件)
8. [常见问题](#常见问题)
9. [最佳实践](#最佳实践)
10. [故障排除](#故障排除)

---

## 快速开始

### 5 分钟上手

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 准备 Gerber 文件
# 将 Gerber 文件放入 input/ 目录

# 3. 运行分析
python main.py -i input/ -o output/

# 4. 查看结果
# 打开 output/overlay.png 查看叠加验证图
```

**就这么简单！** 🎉

---

## 安装配置

### 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows / Linux / macOS |
| Python 版本 | >= 3.12 |
| 内存 | >= 2GB |
| 磁盘空间 | >= 100MB |

### 安装步骤

#### 1. 检查 Python 版本

```bash
python --version
# 或
python3 --version
```

**要求:** Python 3.12 或更高版本

#### 2. 安装依赖

```bash
cd E:\openclaw\openclaw-main\pcb_analyzer
pip install -r requirements.txt
```

**依赖列表:**
- gerbonara (Gerber 文件解析)
- matplotlib (图像渲染)
- numpy (数值计算)
- pillow (图像处理)

#### 3. 验证安装

```bash
python main.py --help
```

如果显示帮助信息，说明安装成功！

---

## 基本使用

### 使用场景 1: 分析单个 Gerber 文件

```bash
python main.py -i input/mask1.gbr -o output/
```

**适用于:**
- 快速测试
- 单层分析
- 调试问题

### 使用场景 2: 分析整个 PCB (推荐)

```bash
python main.py -i input/ -o output/
```

**适用于:**
- 完整 PCB 分析
- 多层合并
- 生产使用

### 使用场景 3: 调整聚类阈值

```bash
python main.py -i input/ -o output/ -t 3.0
```

**适用于:**
- Unknown 占比过高
- 元件识别不准确
- 需要微调结果

### 使用场景 4: 快速分析 (跳过叠加图)

```bash
python main.py -i input/ -o output/ --no-overlay
```

**适用于:**
- 只需要数据
- 加快处理速度
- 批量处理

---

## 高级功能

### 1. 准确性验证

#### 验证孔位是否正确

```bash
python validate_accuracy.py input/ output/pads.csv
```

**输出示例:**
```
准确率: 100.0%
匹配成功: 1739/1739
遗漏: 0 个
误提取: 0 个

✅ 准确率优秀 (>= 95%)
```

**判断标准:**
- ≥ 95% → ✅ 优秀
- 85-95% → ✓ 良好
- < 85% → ⚠️ 需要检查

#### 生成可视化对比图

```bash
python visual_compare.py input/mask1.gbr output/pads.csv output/
```

**生成文件:**
- `comparison.png` - 三图对比
- `difference_map.png` - 差异分析图

**查看方式:**
```bash
# Windows
start output/comparison.png
start output/difference_map.png

# Linux/Mac
xdg-open output/comparison.png
open output/comparison.png
```

### 2. 数据格式验证

```bash
python verify_results.py output/
```

**验证内容:**
- 文件完整性
- 数据格式
- 数值有效性
- 数据一致性

### 3. 批量处理

```bash
# 处理多个项目
for dir in project1 project2 project3; do
    python main.py -i $dir/input/ -o $dir/output/
done
```

### 4. 自定义输出目录

```bash
# 按日期命名输出目录
python main.py -i input/ -o output_$(date +%Y%m%d)/
```

---

## 验证结果

### 方法 1: 目视检查 (最快)

**步骤:**
1. 打开 `output/overlay.png`
2. 检查红点是否与焊盘对齐
3. 检查是否有遗漏

**判断:**
- 红点对齐 → ✅ 准确
- 红点偏移 → ⚠️ 可能有问题

### 方法 2: 自动验证 (最准确)

**步骤:**
```bash
python validate_accuracy.py input/ output/pads.csv
```

**查看准确率:**
- 100% → ✅ 完美
- 95-99% → ✅ 优秀
- 85-95% → ✓ 良好
- < 85% → ⚠️ 需要检查

### 方法 3: 可视化对比 (最直观)

**步骤:**
```bash
python visual_compare.py input/mask1.gbr output/pads.csv output/
```

**查看图像:**
- `comparison.png` - 对比原始和提取
- `difference_map.png` - 查看差异

**判断:**
- 绿色多 → ✅ 匹配良好
- 蓝色多 → ⚠️ 有遗漏
- 红色多 → ⚠️ 有误提取

---

## 参数说明

### main.py 参数

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--input` | `-i` | 必填 | Gerber 文件或目录路径 |
| `--output` | `-o` | `output` | 输出目录 |
| `--threshold` | `-t` | `2.0` | 聚类距离阈值 (mm) |
| `--no-overlay` | - | `False` | 跳过叠加图生成 |
| `--quiet` | `-q` | `False` | 安静模式，减少输出 |

### 阈值调整指南

| 阈值 | 适用场景 | Unknown 占比 |
|------|----------|--------------|
| 1.5mm | 超密集布局 | 可能很高 |
| 2.0mm | 密集布局 (默认) | 中等 |
| 3.0mm | 中等密度 | 较低 |
| 4.0mm | 稀疏布局 | 很低 |
| 5.0mm | 大元件板 | 最低 |

**调整建议:**
- Unknown > 80% → 增大阈值
- Unknown < 30% → 可能阈值过大
- Unknown 50-70% → 阈值合适

---

## 输出文件

### 数据文件

#### 1. pads.csv
**内容:** 所有焊盘的坐标和属性

**格式:**
```csv
x,y,shape,width,height
423.0,283.0,circle,3.0,3.0
113.2,273.4,circle,3.0,3.0
236.0,214.5,rect,1.45,1.45
```

**字段说明:**
- `x, y` - 焊盘中心坐标 (mm)
- `shape` - 形状 (circle/rect/oval/unknown)
- `width, height` - 尺寸 (mm)

**用途:**
- 导入 CAD 软件
- 坐标验证
- 数据分析

#### 2. components.csv
**内容:** 识别的元件和聚类结果

**格式:**
```csv
component_type,pad_count,center_x,center_y,x_min,x_max,y_min,y_max
SOP/TSOP,4,184.58,235.8,183.65,185.5,234.7,236.95
Resistor/Capacitor,2,152.82,172.0,152.0,153.65,172.0,172.0
```

**字段说明:**
- `component_type` - 元件类型
- `pad_count` - 焊盘数量
- `center_x, center_y` - 元件中心坐标
- `x_min, x_max, y_min, y_max` - 包围盒

**用途:**
- BOM 生成
- 元件统计
- 布局分析

### 图像文件

#### 1. pads.png
**内容:** 焊盘散点图

**特点:**
- 蓝色 = 圆形焊盘
- 绿色 = 矩形焊盘
- 灰色 = 未知形状

**用途:** 快速查看焊盘分布

#### 2. components.png
**内容:** 元件类型着色图

**特点:**
- 不同颜色代表不同元件类型
- 相同颜色的焊盘属于同一元件

**用途:** 验证聚类结果

#### 3. pcb.png
**内容:** PCB 背景渲染图

**特点:**
- 高 DPI 渲染
- 保持 Gerber 坐标系

**用途:** 作为叠加图的背景

#### 4. overlay.png ⭐
**内容:** 焊盘叠加验证图

**特点:**
- PCB 背景 + 红点标记
- 红点 = 提取的焊盘位置

**用途:** **最重要的验证图像**

**如何验证:**
1. 打开 overlay.png
2. 检查红点是否在焊盘中心
3. 检查是否有遗漏的焊盘

#### 5. comparison.png (验证工具生成)
**内容:** 三图对比

**布局:**
- 左图: Gerber 原始 (蓝色)
- 中图: 提取结果 (红色)
- 右图: 叠加对比 (紫色=匹配)

**用途:** 对比原始数据和提取结果

#### 6. difference_map.png (验证工具生成)
**内容:** 差异分析图

**颜色含义:**
- 🟢 绿色: 匹配成功
- 🔵 蓝色: 遗漏 (Gerber 有但提取没有)
- 🔴 红色: 误提取 (提取有但 Gerber 没有)

**用途:** 定位具体的差异位置

---

## 常见问题

### Q1: 提取的焊盘数为 0

**原因:**
- Gerber 文件格式不支持
- 文件损坏
- 文件类型错误 (不是焊盘层)

**解决:**
```bash
# 1. 检查文件是否能打开
python -c "from gerbonara import GerberFile; GerberFile.open('input/mask1.gbr')"

# 2. 尝试其他层
python main.py -i input/mask2.gbr -o output/

# 3. 检查文件内容
head -20 input/mask1.gbr
```

### Q2: Unknown 占比过高 (> 80%)

**原因:**
- 聚类阈值过小
- 板子布局稀疏

**解决:**
```bash
# 尝试更大的阈值
python main.py -i input/ -o output_t3/ -t 3.0
python main.py -i input/ -o output_t4/ -t 4.0
python main.py -i input/ -o output_t5/ -t 5.0

# 对比结果
python verify_results.py output_t3/
python verify_results.py output_t4/
python verify_results.py output_t5/
```

### Q3: overlay.png 红点偏移

**原因:**
- 坐标系问题
- DPI 不匹配
- bbox 计算错误

**解决:**
```bash
# 1. 检查 Gerber 单位
python -c "from gerbonara import GerberFile; layer = GerberFile.open('input/mask1.gbr'); print(layer.unit)"

# 2. 尝试不同的 Gerber 层
python main.py -i input/mask2.gbr -o output/

# 3. 查看 pcb.png 是否正常
# 如果 pcb.png 正常但 overlay.png 偏移，可能是坐标映射问题
```

### Q4: 运行速度慢

**原因:**
- 大板子
- 高 DPI 渲染
- 生成叠加图耗时

**解决:**
```bash
# 跳过叠加图
python main.py -i input/ -o output/ --no-overlay

# 或降低 DPI (修改 visualizer.py)
# 将 dpi=200 改为 dpi=100
```

### Q5: 准确率低于 95%

**原因:**
- Gerber 文件格式问题
- 多层数据不一致
- 提取逻辑问题

**解决:**
```bash
# 1. 查看详细差异
python visual_compare.py input/mask1.gbr output/pads.csv output/

# 2. 检查 difference_map.png
# 蓝色多 → 有遗漏 → 检查提取逻辑
# 红色多 → 有误提取 → 检查去重逻辑

# 3. 单层验证
python validate_accuracy.py input/mask1.gbr output/pads.csv
```

---

## 最佳实践

### 1. 标准工作流程

```bash
# 步骤 1: 运行分析
python main.py -i input/ -o output/

# 步骤 2: 快速验证
# 打开 output/overlay.png 目视检查

# 步骤 3: 准确性验证 (重要项目)
python validate_accuracy.py input/ output/pads.csv

# 步骤 4: 生成对比图 (质量审核)
python visual_compare.py input/mask1.gbr output/pads.csv output/

# 步骤 5: 查看结果
# - output/pads.csv (数据)
# - output/components.csv (元件)
# - output/overlay.png (验证)
# - output/comparison.png (对比)
# - output/difference_map.png (差异)
```

### 2. 文件组织

```
project/
├── gerber_files/          # 原始 Gerber 文件
│   ├── mask1.gbr
│   ├── mask2.gbr
│   └── ...
├── analysis/              # 分析结果
│   ├── output/            # 主要输出
│   ├── output_t3/         # 阈值 3.0 测试
│   └── output_t4/         # 阈值 4.0 测试
└── reports/               # 验证报告
    ├── validation.txt
    └── comparison.png
```

### 3. 版本控制

```bash
# 保存分析结果
cp -r output/ archive/output_$(date +%Y%m%d_%H%M%S)/

# 或使用 git
git add output/*.csv output/*.png
git commit -m "PCB analysis results - $(date +%Y%m%d)"
```

### 4. 批量处理脚本

```bash
#!/bin/bash
# batch_analyze.sh

for project in project1 project2 project3; do
    echo "Processing $project..."
    
    # 运行分析
    python main.py -i $project/gerber/ -o $project/output/
    
    # 验证准确性
    python validate_accuracy.py $project/gerber/ $project/output/pads.csv > $project/validation.txt
    
    # 生成对比图
    python visual_compare.py $project/gerber/mask1.gbr $project/output/pads.csv $project/output/
    
    echo "$project completed!"
done
```

### 5. 数据导出

```python
# export_to_excel.py
import pandas as pd

# 读取 CSV
pads = pd.read_csv('output/pads.csv')
components = pd.read_csv('output/components.csv')

# 导出到 Excel
with pd.ExcelWriter('pcb_analysis.xlsx') as writer:
    pads.to_excel(writer, sheet_name='Pads', index=False)
    components.to_excel(writer, sheet_name='Components', index=False)

print("Exported to pcb_analysis.xlsx")
```

---

## 故障排除

### 问题诊断流程

```
1. 检查 Python 版本
   ↓
2. 检查依赖安装
   ↓
3. 检查 Gerber 文件
   ↓
4. 运行基本分析
   ↓
5. 查看输出日志
   ↓
6. 验证结果
```

### 常见错误信息

#### 错误 1: ModuleNotFoundError

```
ModuleNotFoundError: No module named 'gerbonara'
```

**解决:**
```bash
pip install gerbonara matplotlib numpy pillow
```

#### 错误 2: 文件不存在

```
FileNotFoundError: [Errno 2] No such file or directory: 'input/mask1.gbr'
```

**解决:**
```bash
# 检查文件路径
ls input/
# 或
dir input\

# 使用绝对路径
python main.py -i E:\openclaw\openclaw-main\pcb_analyzer\input\ -o output/
```

#### 错误 3: Gerber 解析错误

```
Ambiguous coordinate statement. Coordinate statement does not have an operation mode...
```

**解决:**
- 这是 Gerber 文件格式问题
- 通常不影响主要焊盘提取
- 如果影响结果，尝试其他层的文件

#### 错误 4: 内存不足

```
MemoryError: Unable to allocate array
```

**解决:**
```bash
# 跳过叠加图
python main.py -i input/ -o output/ --no-overlay

# 或降低 DPI
# 修改 visualizer.py 中的 dpi 参数
```

### 获取帮助

```bash
# 查看帮助信息
python main.py --help
python validate_accuracy.py --help
python visual_compare.py --help

# 查看文档
cat README.md
cat HANDOFF.md
cat ACCURACY_VALIDATION_GUIDE.md
```

---

## 附录

### A. 支持的 Gerber 文件类型

| 文件类型 | 扩展名 | 优先级 | 说明 |
|---------|--------|--------|------|
| 阻焊层 | mask1.gbr, mask2.gbr | 最高 | 主要焊盘来源 |
| Via 塞孔 | via_plugging.gbr | 高 | Via 焊盘 |
| 钻孔图 | drilldrw.gbr | 中 | 钻孔位置 |
| 铜层 | lay1~4.gbr | 中 | 铜层焊盘 |
| 丝印层 | silk1.gbr, silk2.gbr | 低 | 标记信息 |

### B. 元件识别规则

| 焊盘数 | 长宽比 | 识别类型 |
|--------|--------|----------|
| 2 | > 4 | Resistor 0402 |
| 2 | > 2.5 | Resistor/Capacitor 0603 |
| 2 | > 1.5 | Resistor/Capacitor 0805 |
| 2 | 其他 | Resistor/Capacitor |
| 4-8 | - | SOP/TSOP |
| 16 | - | QFP-16 |
| 24 | - | QFP-24 |
| 32 | - | QFP-32 |
| 8-20 | - | QFN |
| > 20 | > 1.5 | BGA |
| > 20 | ≤ 1.5 | QFN |
| 1, 3 | - | Unknown |

### C. 快速参考

```bash
# 基本分析
python main.py -i input/ -o output/

# 调整阈值
python main.py -i input/ -o output/ -t 3.0

# 验证准确性
python validate_accuracy.py input/ output/pads.csv

# 生成对比图
python visual_compare.py input/mask1.gbr output/pads.csv output/

# 数据验证
python verify_results.py output/
```

---

## 联系与支持

### 文档资源

- `README.md` - 快速开始
- `HANDOFF.md` - 项目交接文档
- `ACCURACY_VALIDATION_GUIDE.md` - 验证指南
- `FINAL_VALIDATION_REPORT.md` - 验证报告
- `PROJECT_SUMMARY.md` - 项目总结

### 问题反馈

如遇到问题，请提供:
1. Python 版本
2. 操作系统
3. 错误信息
4. Gerber 文件信息
5. 运行命令

---

**最后更新:** 2024年  
**版本:** 1.0  
**状态:** ✅ 已验证 (准确率 100%)
