"""
丝印层对比验证 — 通过 OCR 提取丝印位号验证元件识别
使用 RapidOCR 进行文字识别，匹配聚类结果
"""

import sys, os, csv, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import warnings
from gerbonara import GerberFile


REFDES_PREFIX_MAP = {
    'R': 'resistor', 'RN': 'resistor', 'RP': 'resistor',
    'C': 'capacitor', 'CP': 'capacitor',
    'U': 'ic', 'IC': 'ic',
    'Q': 'transistor', 'T': 'transistor',
    'D': 'diode', 'DZ': 'diode',
    'J': 'connector', 'P': 'connector', 'CN': 'connector', 'CON': 'connector',
    'L': 'inductor', 'FB': 'ferrite',
    'Y': 'crystal', 'X': 'crystal',
    'F': 'fuse',
    'SW': 'switch',
    'LED': 'led',
}


def try_load_ocr():
    """尝试加载 Tesseract OCR，失败返回 None"""
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        # 测试是否可用
        import subprocess
        subprocess.run([pytesseract.pytesseract.tesseract_cmd, '--version'], capture_output=True, check=True)
        print("  Tesseract OCR ready")
        return pytesseract
    except Exception as e:
        print(f"[INFO] Tesseract not available: {e}")
        return None
    except Exception as e:
        print(f"[INFO] OCR init failed: {e}")
        return None
    except Exception as e:
        print(f"[INFO] PaddleOCR init failed: {e}")
        return None
    except Exception as e:
        print(f"[INFO] OCR init failed: {e}")
        return None


def render_silk_to_image(gerber_path):
    """渲染丝印层到 matplotlib 图像"""
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore')
        layer = GerberFile.open(str(gerber_path))
        bbox = layer.bounding_box()
    
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.set_xlim(bbox[0][0], bbox[1][0])
    ax.set_ylim(bbox[0][1], bbox[1][1])
    
    for obj in layer.objects:
        if type(obj).__name__ == 'Line':
            ax.plot([obj.p1[0], obj.p2[0]], [obj.p1[1], obj.p2[1]],
                   'k-', linewidth=0.15, alpha=0.6)
        elif type(obj).__name__ == 'Arc':
            pass
    
    ax.set_aspect('equal')
    ax.invert_yaxis()
    ax.axis('off')
    
    return fig, ax, bbox


def load_clusters(components_csv):
    """加载聚类结果"""
    clusters = []
    with open(components_csv, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            clusters.append({
                'center_x': float(row['center_x']),
                'center_y': float(row['center_y']),
                'component_type': row.get('component_type', 'Unknown'),
                'confidence': float(row.get('confidence', 0)),
                'pad_count': int(row.get('pad_count', 0)),
            })
    return clusters


def extract_silk_text_positions(silk_path):
    """
    从丝印层提取文本位置（通过 Tesseract OCR）
    返回 [(text, x, y), ...]
    """
    ocr = try_load_ocr()
    
    if ocr is None:
        print("[INFO] OCR not available. Using visual-only mode.")
        return None
    
    from PIL import Image, ImageEnhance
    import numpy as np
    
    fig, ax, bbox = render_silk_to_image(silk_path)
    
    temp_img_path = Path(__file__).parent.parent / 'output' / '_silk_temp.png'
    fig.savefig(str(temp_img_path), format='png', dpi=300, bbox_inches='tight',
                pad_inches=0, facecolor='white')
    plt.close(fig)
    
    img = Image.open(temp_img_path)
    width_px, height_px = img.size
    
    data = ocr.image_to_data(img, output_type=ocr.Output.DICT, lang='eng')
    
    results = []
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if not text or not text[0].isalpha():
            continue
        
        x_px = data['left'][i] + data['width'][i] / 2
        y_px = data['top'][i] + data['height'][i] / 2
        
        mm_range_x = bbox[1][0] - bbox[0][0]
        mm_range_y = bbox[1][1] - bbox[0][1]
        
        x_mm = bbox[0][0] + (x_px / width_px) * mm_range_x
        y_mm = bbox[0][1] + (y_px / height_px) * mm_range_y
        
        results.append((text.strip(), x_mm, y_mm))
    
    print(f"  OCR extracted: {len(results)} text labels")
    
    try:
        os.remove(temp_img_path)
    except:
        pass
    
    return results


def match_text_to_clusters(text_positions, clusters, threshold=3.0):
    """将 OCR 提取的文本匹配到最近的聚类"""
    if not text_positions:
        return []
    
    matches = []
    for text, tx, ty in text_positions:
        best_dist = float('inf')
        best_idx = -1
        
        for i, c in enumerate(clusters):
            dist = math.hypot(tx - c['center_x'], ty - c['center_y'])
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        
        if best_idx >= 0 and best_dist < threshold:
            refdes_prefix = ''.join(c for c in text if c.isalpha())
            expected_type = REFDES_PREFIX_MAP.get(refdes_prefix, 'unknown')
            recognized_type = clusters[best_idx]['component_type'].lower()
            
            matches.append({
                'silk_text': text,
                'silk_x': tx,
                'silk_y': ty,
                'cluster_idx': best_idx,
                'distance': best_dist,
                'expected_type': expected_type,
                'recognized_type': clusters[best_idx]['component_type'],
                'match': expected_type in recognized_type or recognized_type in expected_type,
                'confidence': clusters[best_idx]['confidence'],
            })
    
    return matches


def run_silk_verification(gerber_dir, components_csv, output_dir, verbose=True):
    """
    运行丝印层对比验证
    
    Args:
        gerber_dir: Gerber 文件目录
        components_csv: 聚类结果 CSV 路径
        output_dir: 输出目录
        verbose: 是否打印
    """
    gerber_dir = Path(gerber_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    silk_paths = [
        gerber_dir / 'silk1.gbr',
        gerber_dir / 'silk2.gbr',
    ]
    
    silk_path = None
    for sp in silk_paths:
        if sp.exists():
            silk_path = sp
            break
    
    if not silk_path:
        print("No silk screen file found")
        return
    
    clusters = load_clusters(components_csv)
    
    print("=" * 50)
    print("Silk Screen Verification")
    print("=" * 50)
    print(f"Silk screen: {silk_path.name}")
    print(f"Components:  {len(clusters)}")
    print()
    
    correct = 0
    total = 0
    accuracy = 0.0
    
    # Try OCR
    text_positions = extract_silk_text_positions(silk_path)
    
    if text_positions:
        matches = match_text_to_clusters(text_positions, clusters)
        
        correct = sum(1 for m in matches if m['match'])
        total = len(matches)
        accuracy = (correct / total * 100) if total > 0 else 0
        
        print(f"OCR extracted: {len(text_positions)} text labels")
        print(f"Matched to clusters: {total}")
        print(f"Correct: {correct}")
        print(f"Accuracy: {accuracy:.1f}%")
        print()
        
        if verbose:
            print(f"{'Text':<10} {'Expected':<15} {'Recognized':<20} {'Dist':>5} {'Conf':>5} {'Result'}")
            print("-" * 70)
            for m in matches[:30]:
                result = "OK" if m['match'] else "MISMATCH"
                print(f"{m['silk_text']:<10} {m['expected_type']:<15} {m['recognized_type']:<20} "
                      f"{m['distance']:>5.1f} {m['confidence']:>5.0f} {result}")
            if len(matches) > 30:
                print(f"... and {len(matches)-30} more")
        
        print(f"\nSummary: {correct}/{total} correct ({accuracy:.1f}%)")
    else:
        print("OCR not available — generating visual comparison instead")
        matches = []
        accuracy = 0
        total = 0
    
    # Generate visual comparison
    fig, ax, bbox = render_silk_to_image(silk_path)
    ax.set_title(f'PCB Silkscreen + Component Recognition', fontsize=13)
    
    for c in clusters:
        ct = c['component_type']
        conf = c['confidence']
        if conf >= 80:
            color = 'green'
        elif conf >= 60:
            color = 'orange'
        else:
            color = 'red'
        
        ax.plot(c['center_x'], c['center_y'], 'o', color=color, markersize=4, alpha=0.7)
        ax.annotate(ct, (c['center_x'], c['center_y']),
                   fontsize=4, ha='center', va='bottom', alpha=0.8,
                   bbox=dict(boxstyle='round,pad=0.1', facecolor='white', alpha=0.6))
    
    if text_positions:
        for text, tx, ty in text_positions:
            ax.plot(tx, ty, 'x', color='blue', markersize=5, alpha=0.5)
            ax.annotate(text, (tx, ty), fontsize=5, color='blue', alpha=0.6)
    
    viz_path = output_dir / 'silk_verification.png'
    fig.savefig(viz_path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"Visual saved: {viz_path}")
    
    # Generate report
    report_path = output_dir / 'silk_verification_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Silk Screen Verification Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total components: {len(clusters)}\n")
        if text_positions:
            f.write(f"OCR extracted: {len(text_positions)}\n")
            f.write(f"Matched: {total}\n")
            f.write(f"Correct: {correct}\n")
            f.write(f"Accuracy: {accuracy:.1f}%\n\n")
            for m in matches:
                result = "OK" if m['match'] else "FAIL"
                f.write(f"{result} | {m['silk_text']} -> expected={m['expected_type']} "
                       f"got={m['recognized_type']} dist={m['distance']:.1f}mm\n")
        else:
            f.write("OCR not available\n")
            f.write("Visual comparison image generated instead.\n")
        f.write(f"\nVisual: {viz_path}\n")
    
    print(f"Report saved: {report_path}")
    return {'accuracy': accuracy, 'total': total, 'correct': correct}


if __name__ == '__main__':
    base = Path(__file__).parent.parent
    run_silk_verification(
        gerber_dir=base / 'input',
        components_csv=base / 'output' / 'components.csv',
        output_dir=base / 'output',
    )
