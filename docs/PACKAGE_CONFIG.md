# 封装配置文件指南 (Package Configuration Guide)

## 概述

本工具支持通过外部 JSON/YAML 文件定义元件封装库。
默认库位于 `config/packages/default_library.json`，用户可通过 `--package-lib` 加载自定义库覆盖默认定义。

---

## 文件格式

支持 JSON 和 YAML 两种格式：

```json
{
  "packages": [
    { "id": "R_0402", "type": "resistor", "pad_count": 2, ... }
  ]
}
```

```yaml
packages:
  - id: "R_0402"
    type: "resistor"
    pad_count: 2
    ...
```

---

## 字段说明

### 必填字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | string | 封装唯一标识 | `"R_0402"` |
| `type` | string | 封装类型 | `"resistor"`, `"ic_sop"`, `"connector_pin"` |
| `pad_count` | int | 焊盘数量 | `2`, `8`, `44` |
| `width_min` | float | 包围盒最小宽度 (mm) | `0.4` |
| `width_max` | float | 包围盒最大宽度 (mm) | `0.8` |
| `height_min` | float | 包围盒最小高度 (mm) | `0.2` |
| `height_max` | float | 包围盒最大高度 (mm) | `0.6` |

### 可选字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `aspect_ratio_min` | float | `0.0` | 最小长宽比 |
| `aspect_ratio_max` | float | `999.0` | 最大长宽比 |
| `category` | string | `"unknown"` | 分类：`passive`, `ic`, `connector`, `discrete`, `other` |
| `hierarchy` | string | `"generic"` | 层级：`generic`(通用), `specific`(具体型号) |
| `pad_pitch_min` | float | null | 最小引脚间距 (mm) |
| `pad_pitch_max` | float | null | 最大引脚间距 (mm) |
| `pad_shape` | string | `"any"` | 焊盘形状：`any`, `circle`, `rect`, `oval` |
| `pad_width_min` | float | null | 焊盘最小宽度 (mm) |
| `pad_width_max` | float | null | 焊盘最大宽度 (mm) |
| `pad_height_min` | float | null | 焊盘最小高度 (mm) |
| `pad_height_max` | float | null | 焊盘最大高度 (mm) |
| `layout_pattern` | string | `"any"` | 布局模式：`any`, `single`, `dual`, `quad`, `grid` |
| `description` | string | `""` | 描述文本 |
| `aliases` | array | `[]` | 别名列表 |

---

## type 有效值

| 值 | 说明 | 示例封装 |
|-----|------|----------|
| `resistor` | 电阻 | R_0402, R_0603 |
| `capacitor` | 电容 | C_TANT_A |
| `ic_sop` | SOP 系列 IC | SOP-8, SOP-16 |
| `ic_tsop` | TSOP 系列 IC | TSOP-32, TSOP-48 |
| `ic_qfp` | QFP 系列 IC | QFP-44, QFP-64 |
| `ic_qfn` | QFN 系列 IC | QFN-32, QFN-48 |
| `ic_bga` | BGA 系列 IC | BGA-100, BGA-144 |
| `connector_pin` | 排针连接器 | Pin Header 2P~40P |
| `connector_usb` | USB 连接器 | USB-A, USB-C |
| `connector_eth` | 网络连接器 | RJ45 |
| `connector_hdmi` | HDMI 连接器 | HDMI |
| `diode` | 二极管 | SOD-123, SOD-323 |
| `transistor` | 三极管/晶体管 | SOT-23, SOT-223 |
| `other` | 其他 | — |

---

## category 有效值

| 值 | 包含类型 |
|-----|----------|
| `passive` | resistor, capacitor |
| `ic` | ic_sop, ic_tsop, ic_qfp, ic_qfn, ic_bga |
| `connector` | connector_pin, connector_usb, etc. |
| `discrete` | diode, transistor |
| `other` | 其他 |

---

## 布局模式 (layout_pattern)

| 模式 | 说明 | 典型封装 |
|------|------|----------|
| `single` | 一排焊盘 | 排针 |
| `dual` | 两排焊盘（对边） | SOP, TSOP |
| `quad` | 四边焊盘 | QFP, QFN |
| `grid` | 网格排列 | BGA |

---

## 配置示例

### 1. 自定义电阻封装

```json
{
  "id": "MY_RES_0402",
  "type": "resistor",
  "pad_count": 2,
  "width_min": 0.5,
  "width_max": 0.7,
  "height_min": 0.25,
  "height_max": 0.55,
  "aspect_ratio_min": 1.5,
  "aspect_ratio_max": 3.0,
  "category": "passive",
  "pad_shape": "rect",
  "description": "Custom 0402 Resistor"
}
```

### 2. 覆盖默认库定义

创建 `my_custom.json`，指定相同 `id` 即可覆盖：

```json
{
  "packages": [
    {
      "id": "SOP_8",
      "type": "ic_sop",
      "pad_count": 8,
      "width_min": 3.5,
      "width_max": 5.5,
      "height_min": 3.0,
      "height_max": 4.5,
      "aspect_ratio_min": 1.0,
      "aspect_ratio_max": 1.8,
      "category": "ic",
      "layout_pattern": "dual",
      "pad_shape": "rect",
      "pad_pitch_min": 1.2,
      "pad_pitch_max": 1.3,
      "description": "Custom SOP-8"
    }
  ]
}
```

---

## 使用命令

```bash
# 使用默认库
python main.py -i input/ -o output/

# 加载自定义库（覆盖默认）
python main.py -i input/ --package-lib my_custom.json

# 加载目录中的所有配置文件
python main.py -i input/ --package-lib ./config/my_packages/

# 验证配置文件格式
python main.py --validate-config my_custom.json

# 列出当前库的所有封装定义
python main.py --list-packages
```

---

## 置信度评分说明

识别引擎基于加权评分匹配封装：

| 维度 | 权重 | 说明 |
|------|------|------|
| 焊盘数量 | 30% | 精确匹配 100%，偏差 ±2 得 50% |
| 封装尺寸 | 25% | 完全在范围内得 100% |
| 长宽比 | 15% | 在范围内得 100% |
| 引脚间距 | 15% | 需要配置 pad_pitch |
| 焊盘形状 | 10% | circle/rect 匹配 |
| 布局模式 | 5% | quad/dual/grid 匹配 |

阈值：**60 分以上**认定为匹配成功，否则返回 `Unknown`。
