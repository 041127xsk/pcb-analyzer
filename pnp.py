"""
Pick & Place (PNP) 文件生成模块
从聚类结果生成 SMT 贴片机标准坐标文件
"""

from pathlib import Path
import csv
import copy


TYPE_PREFIX = {
    'Resistor': 'R',
    'Capacitor': 'C',
    'SOP': 'U',
    'TSOP': 'U',
    'QFP': 'U',
    'QFN': 'U',
    'BGA': 'U',
}

SPECIAL_TYPES = {
    'Resistor 0402': 'R',
    'Resistor/Capacitor 0603': 'R',
    'Resistor/Capacitor 0805': 'R',
    'Resistor/Capacitor': 'R',
}


def estimate_rotation(cluster):
    """简单估算元件旋转角度（基于长宽方向）"""
    w = cluster['width']
    h = cluster['height']
    eps = 0.01
    if abs(w - h) < eps or w < eps or h < eps:
        return 0
    if w > h:
        return 0
    else:
        return 90


def assign_refdes(clusters):
    """
    为每个聚类分配参考位号 (R1, C2, U3, ...)
    相同类型连续编号
    
    Args:
        clusters: 聚类列表（每个 cluster 需含 component_type）
    
    Returns:
        list: 新的聚类列表，添加了 refdes（不修改原始数据）
    """
    counters = {}
    result = []
    
    for c in clusters:
        c_copy = copy.deepcopy(c)
        ct = c_copy.get('component_type', 'Unknown')
        
        if ct in SPECIAL_TYPES:
            prefix = SPECIAL_TYPES[ct]
        else:
            matched = False
            for key, val in TYPE_PREFIX.items():
                if key in ct:
                    prefix = val
                    matched = True
                    break
            if not matched:
                prefix = 'X'
        
        counters.setdefault(prefix, 0)
        counters[prefix] += 1
        c_copy['refdes'] = f"{prefix}{counters[prefix]}"
        result.append(c_copy)
    
    return result


def generate_pnp(clusters, pads, output_path, top_layer='TOP'):
    """
    生成 PNP 文件 (IPC-9751 / 标准贴片机 CSV 格式)
    
    输出列：
      Designator, Mid X, Mid Y, Layer, Rotation, Comment, Pad Count
    
    Args:
        clusters: 聚类列表（需含 refdes）
        pads: 焊盘列表
        output_path: 输出文件路径
        top_layer: 顶层名称
    
    Returns:
        str: 输出文件路径
    """
    fieldnames = ['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation', 'Footprint', 'Pad Count']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in clusters:
            rotation = estimate_rotation(c)
            writer.writerow({
                'Designator': c.get('refdes', '?'),
                'Mid X': round(c['center_x'], 3),
                'Mid Y': round(c['center_y'], 3),
                'Layer': top_layer,
                'Rotation': rotation,
                'Footprint': c.get('component_type', 'Unknown'),
                'Pad Count': c['count'],
            })
    
    print(f"已生成 PNP 文件: {output_path}")
    return str(output_path)


def generate_pnp_simple(clusters, output_path):
    """
    生成简易 PNP 文件（贴片机通用格式）
    格式：Designator,X,Y,Rotation,Layer,Footprint
    
    Args:
        clusters: 聚类列表（需含 refdes）
        output_path: 输出文件路径
    """
    lines = ['Designator,X,Y,Rotation,Layer,Footprint']
    for c in clusters:
        rotation = estimate_rotation(c)
        lines.append(
            f"{c.get('refdes', '?')},"
            f"{round(c['center_x'], 3):.3f},"
            f"{round(c['center_y'], 3):.3f},"
            f"{rotation},"
            f"TOP,"
            f"{c.get('component_type', 'Unknown')}"
        )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    
    print(f"已生成简易 PNP 文件: {output_path}")
    return str(output_path)


def visualize_pnp(clusters, pads, output_path):
    """
    生成 PNP 验证图 — 在元件中心标注位号
    
    Args:
        clusters: 聚类列表（需含 refdes）
        pads: 焊盘列表
        output_path: 输出文件路径
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    
    fig, ax = plt.subplots(figsize=(14, 10))
    
    for pad in pads:
        if pad['shape'] == 'rect':
            w, h = pad.get('width', 1), pad.get('height', 1)
            rect = patches.Rectangle(
                (pad['x'] - w/2, pad['y'] - h/2), w, h,
                linewidth=0.3, edgecolor='black',
                facecolor='#3498db', alpha=0.5
            )
            ax.add_patch(rect)
        else:
            r = pad.get('width', 1) / 2
            circle = patches.Circle(
                (pad['x'], pad['y']), r,
                linewidth=0.3, edgecolor='black',
                facecolor='#3498db', alpha=0.5
            )
            ax.add_patch(circle)
    
    for c in clusters:
        refdes = c.get('refdes', '?')
        ax.plot(c['center_x'], c['center_y'], 'r+', markersize=8, markeredgewidth=2)
        ax.annotate(refdes, (c['center_x'], c['center_y']),
                    fontsize=6, ha='center', va='bottom',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.7))
    
    xs = [p['x'] for p in pads]
    ys = [p['y'] for p in pads]
    margin = 5
    ax.set_xlim(min(xs) - margin, max(xs) + margin)
    ax.set_ylim(min(ys) - margin, max(ys) + margin)
    
    ax.set_aspect('equal')
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_title(f'Pick & Place — {len(clusters)} 个元件')
    ax.grid(True, alpha=0.2)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"已保存 PNP 验证图: {output_path}")


def run_pnp_generation(clusters, pads, output_dir='output', verbose=True):
    """
    一键生成 PNP 文件 + 验证图
    
    Args:
        clusters: 聚类列表
        pads: 焊盘列表
        output_dir: 输出目录
        verbose: 是否打印
    
    Returns:
        dict: 生成的文件路径
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    clusters_with_refdes = assign_refdes(clusters)
    
    results = {}
    
    results['pnp_csv'] = generate_pnp(clusters_with_refdes, pads, output_dir / 'pick_and_place.csv')
    
    results['pnp_simple'] = generate_pnp_simple(clusters_with_refdes, output_dir / 'pnp_simple.csv')
    
    results['pnp_png'] = None
    visualize_pnp(clusters_with_refdes, pads, output_dir / 'pnp_verification.png')
    results['pnp_png'] = str(output_dir / 'pnp_verification.png')
    
    if verbose:
        print(f"\nPNP 文件生成完成")
        print(f"  - IPC 标准: {results['pnp_csv']}")
        print(f"  - 简易格式: {results['pnp_simple']}")
        print(f"  - 验证图:   {results['pnp_png']}")
    
    return results


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2:
        import csv as csv_mod
        with open(sys.argv[1], 'r') as f:
            reader = csv_mod.DictReader(f)
            pads = list(reader)
            for p in pads:
                p['x'] = float(p['x'])
                p['y'] = float(p['y'])
                p['width'] = float(p.get('width', 0))
                p['height'] = float(p.get('height', 0))
        
        with open(sys.argv[2], 'r') as f:
            reader = csv_mod.DictReader(f)
            clusters = list(reader)
            for c in clusters:
                c['count'] = int(c['pad_count'])
                c['center_x'] = float(c['center_x'])
                c['center_y'] = float(c['center_y'])
                c['width'] = float(c.get('x_max', 0)) - float(c.get('x_min', 0))
                c['height'] = float(c.get('y_max', 0)) - float(c.get('y_min', 0))
        
        run_pnp_generation(clusters, pads)
    else:
        print("用法: python pnp.py <pads.csv> <components.csv>")