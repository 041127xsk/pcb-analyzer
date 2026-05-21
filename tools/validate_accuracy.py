"""
准确率验证工具
对比识别结果与 ground truth，生成分类别准确率报告
"""

import sys, csv, os
from pathlib import Path
from collections import defaultdict


def load_csv(path):
    """加载 CSV 文件"""
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def validate_accuracy(components_csv, ground_truth_csv, output_path=None, verbose=True):
    """
    验证识别准确率
    
    Args:
        components_csv: 识别结果 CSV (含 component_type)
        ground_truth_csv: 人工标注的 ground truth CSV (含 component_type)
        output_path: 可选报告输出路径
        verbose: 是否打印
    
    Returns:
        dict: 准确率统计
    """
    results = load_csv(components_csv)
    truths = load_csv(ground_truth_csv)
    
    if len(results) != len(truths):
        print(f"[WARN] 条目数不匹配: 识别 {len(results)}, ground truth {len(truths)}")
    
    total = min(len(results), len(truths))
    correct = 0
    by_type = defaultdict(lambda: {'total': 0, 'correct': 0})
    
    for i in range(total):
        pred = results[i].get('component_type', 'Unknown').strip()
        truth = truths[i].get('component_type', 'Unknown').strip()
        
        by_type[truth]['total'] += 1
        
        # 支持部分匹配：比如 "SOP-8" 匹配 "SOP" 前缀
        if pred == truth or truth in pred or pred in truth:
            correct += 1
            by_type[truth]['correct'] += 1
    
    overall = (correct / total * 100) if total > 0 else 0
    
    if verbose:
        print(f"\n准确率验证报告")
        print("=" * 50)
        print(f"总条目: {total}")
        print(f"正确:   {correct}")
        print(f"准确率: {overall:.1f}%")
        print()
        print(f"{'类型':<30} {'总数':>6} {'正确':>6} {'准确率':>8}")
        print("-" * 50)
        for t, stats in sorted(by_type.items(), key=lambda x: -x[1]['total']):
            rate = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"{t:<30} {stats['total']:>6} {stats['correct']:>6} {rate:>7.1f}%")
    
    result = {
        'total': total,
        'correct': correct,
        'accuracy': overall,
        'by_type': dict(by_type),
    }
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("准确率验证报告\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"总条目: {total}\n")
            f.write(f"正确:   {correct}\n")
            f.write(f"准确率: {overall:.1f}%\n\n")
            f.write(f"{'Type':<30} {'Total':>6} {'Correct':>6} {'Rate':>8}\n")
            f.write("-" * 50 + "\n")
            for t, stats in sorted(by_type.items(), key=lambda x: -x[1]['total']):
                rate = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
                f.write(f"{t:<30} {stats['total']:>6} {stats['correct']:>6} {rate:>7.1f}%\n")
        print(f"\n报告已保存: {output_path}")
    
    return result


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python validate_accuracy.py <components.csv> <ground_truth.csv> [output_report.txt]")
        sys.exit(1)
    
    output = sys.argv[3] if len(sys.argv) > 3 else None
    validate_accuracy(sys.argv[1], sys.argv[2], output)
