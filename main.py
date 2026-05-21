#!/usr/bin/env python3
"""
PCB 分析工具 - 主入口
一键完成 Gerber 解析、焊盘提取、聚类、可视化
"""

import argparse
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from extractor import GerberExtractor
from drill_extractor import DrillExtractor
from clustering import PadClustering
from visualizer import Visualizer
from pnp import run_pnp_generation
from utils import ensure_output_dir, get_gerber_files


class PipelineError(Exception):
    """Pipeline 执行错误"""
    pass


def run_pipeline(input_path, output_dir='output', threshold=2.0, 
                 create_overlay=True, verbose=True, package_lib_path=None,
                 extract_drills=True):
    """
    运行完整的 PCB 分析 Pipeline
    
    Args:
        input_path: Gerber 文件或目录路径
        output_dir: 输出目录
        threshold: 聚类距离阈值
        create_overlay: 是否创建叠加图
        verbose: 是否打印详细信息
        extract_drills: 是否提取钻孔数据
    
    Returns:
        dict: 运行结果
    
    Raises:
        PipelineError: 当关键步骤失败时
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        'input': str(input_path),
        'output_dir': str(output_dir),
        'pads_count': 0,
        'clusters_count': 0,
        'files': {},
        'success': False
    }
    
    print("=" * 60)
    print("PCB Gerber 分析工具")
    print("=" * 60)
    print(f"输入: {input_path}")
    print(f"输出: {output_dir}")
    print()
    
    # ========== 步骤1: 提取焊盘 ==========
    print("【步骤1】提取焊盘...")
    print("-" * 40)
    
    extractor = GerberExtractor(verbose=verbose)
    
    try:
        if input_path.is_file():
            pads = extractor.extract_from_file(input_path)
            extractor.pads = pads
        elif input_path.is_dir():
            extractor.extract_from_dir(input_path)
        else:
            raise PipelineError(f"无效输入: {input_path}")
    except PipelineError:
        raise
    except Exception as e:
        raise PipelineError(f"焊盘提取失败: {e}") from e
    
    if not extractor.pads:
        raise PipelineError("未提取到任何焊盘，请检查 Gerber 文件")
    
    pads = extractor.pads
    results['pads_count'] = len(pads)
    
    csv_path = output_dir / 'pads.csv'
    extractor.save_csv(csv_path)
    results['files']['pads_csv'] = str(csv_path)
    
    print()
    
    # ========== 步骤1.5: 提取钻孔 (可选) ==========
    drills = []
    if extract_drills and input_path.is_dir():
        print("【步骤1.5】提取钻孔...")
        print("-" * 40)
        
        drill_extractor = DrillExtractor(verbose=verbose)
        drills = drill_extractor.extract_from_dir(input_path)
        
        if drills:
            csv_path = output_dir / 'drills.csv'
            drill_extractor.save_csv(csv_path)
            results['files']['drills_csv'] = str(csv_path)
        else:
            print("  未找到钻孔文件，跳过")
        
        print()
    
    # ========== 步骤2: 聚类分析 ==========
    print("【步骤2】聚类分析...")
    print("-" * 40)
    
    library_system = None
    from package_library import ComponentLibrarySystem
    try:
        library_system = ComponentLibrarySystem(
            custom_lib_path=package_lib_path,
        )
        if verbose:
            print(f"封装库已加载: {len(library_system.get_all_packages())} 个定义")
            print(f"  (默认库: config/packages/default_library.json", end='')
            if package_lib_path:
                print(f" + 自定义: {package_lib_path})")
            else:
                print(")")
    except Exception as e:
        if verbose:
            print(f"封装库加载失败: {e}")
    
    clusterer = PadClustering(threshold=threshold, verbose=verbose, library_system=library_system, drills=drills)
    clusters = clusterer.fit(pads)
    clusterer.add_component_type()
    
    if drills:
        th_count = sum(1 for c in clusters if c.get('mount_type') == 'through-hole')
        smd_count = sum(1 for c in clusters if c.get('mount_type') == 'smd')
        print(f"\n安装类型: 通孔={th_count}, 贴片={smd_count}")
    
    clusters_csv = output_dir / 'components.csv'
    clusterer.save_csv(clusters_csv)
    results['files']['components_csv'] = str(clusters_csv)
    results['clusters_count'] = len(clusters)
    
    summary = clusterer.get_summary()
    print(f"\n元件类型统计（共 {sum(summary.values())} 个）:")
    for comp_type, count in sorted(summary.items(), key=lambda x: -x[1]):
        print(f"  {comp_type}: {count}")
    
    if library_system and hasattr(clusterer, 'recognition_engine'):
        confidences = [c.get('confidence', 0) for c in clusters]
        high = sum(1 for c in confidences if c >= 80)
        mid = sum(1 for c in confidences if 60 <= c < 80)
        low = sum(1 for c in confidences if 0 < c < 60)
        none = sum(1 for c in confidences if c == 0)
        print(f"\n置信度分布:")
        print(f"  高 (>=80): {high}")
        print(f"  中 (60-79): {mid}")
        print(f"  低 (<60): {low}")
        print(f"  未知: {none}")
    
    print()
    
    # ========== 步骤3: 可视化 ==========
    print("【步骤3】生成可视化...")
    print("-" * 40)
    
    viz = Visualizer()
    
    viz.plot_pads(pads, output_dir / 'pads.png', title="PCB Pads")
    results['files']['pads_png'] = str(output_dir / 'pads.png')
    
    viz.plot_with_clusters(pads, clusters, output_dir / 'components.png', title="PCB Components")
    results['files']['components_png'] = str(output_dir / 'components.png')
    
    if library_system:
        viz.plot_with_confidence(pads, clusters, output_dir / 'confidence.png', 
                                  title="Recognition Confidence")
        results['files']['confidence_png'] = str(output_dir / 'confidence.png')
    
    if create_overlay and input_path.is_dir():
        gerber_files = get_gerber_files(input_path)
        gerber_file = None
        priority_names = ['mask1.gbr', 'mask2.gbr', 'lay1.gbr']
        for name in priority_names:
            for gf in gerber_files:
                if gf.name.lower() == name:
                    gerber_file = gf
                    break
            if gerber_file:
                break
        
        if not gerber_file:
            for gf in gerber_files:
                if 'top' in gf.name.lower() or 'mask' in gf.name.lower():
                    gerber_file = gf
                    break
        
        if gerber_file:
            pcb_path = output_dir / 'pcb.png'
            pcb_info = viz.generate_pcb_image(gerber_file, pcb_path, dpi=200)
            results['files']['pcb_png'] = str(pcb_path)
            
            if (output_dir / 'pads.csv').exists():
                overlay_path = output_dir / 'overlay.png'
                viz.create_verification_overlay(pcb_path, output_dir / 'pads.csv', 
                                                 overlay_path, marker_size=3)
                results['files']['overlay_png'] = str(overlay_path)
    
    print()
    
    # ========== 步骤4: 生成 PNP 文件 ==========
    print("【步骤4】生成 Pick & Place 文件...")
    print("-" * 40)
    
    pnp_results = run_pnp_generation(clusters, pads, str(output_dir), verbose=verbose)
    for key, val in pnp_results.items():
        if val:
            results['files'][f'pnp_{key}'] = val
    
    print()
    
    # ========== 完成 ==========
    results['success'] = True
    print("=" * 60)
    print("分析完成!")
    print("=" * 60)
    print(f"\n提取焊盘: {results['pads_count']} 个")
    print(f"识别元件: {results['clusters_count']} 个")
    print(f"\n输出文件:")
    for name, path in results['files'].items():
        print(f"  {name}: {path}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='PCB Gerber 分析工具 - 一键提取焊盘、聚类分析、可视化',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py --input ./input/top.gbr
  python main.py --input ./gerber_folder --output ./results
  python main.py -i ./gerber -t 3.0
        """
    )
    
    parser.add_argument('-i', '--input', required=True,
                       help='Gerber 文件或目录路径')
    parser.add_argument('-o', '--output', default='output',
                       help='输出目录 (默认: output)')
    parser.add_argument('-t', '--threshold', type=float, default=2.0,
                       help='聚类距离阈值 mm (默认: 2.0)')
    parser.add_argument('--package-lib', default=None,
                       help='自定义封装库配置文件或目录路径')
    parser.add_argument('--validate-config', default=None,
                       help='验证配置文件格式')
    parser.add_argument('--list-packages', action='store_true',
                       help='列出所有封装定义')
    parser.add_argument('--no-overlay', action='store_true',
                       help='不生成 Gerber 叠加图')
    parser.add_argument('--no-drills', action='store_true',
                       help='不提取钻孔数据')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='安静模式，减少输出')
    
    args = parser.parse_args()
    
    verbose = not args.quiet
    
    # 处理 --validate-config
    if args.validate_config:
        from package_library import ComponentLibrarySystem
        lib = ComponentLibrarySystem(custom_lib_path=args.package_lib)
        lib.validate_config_file(args.validate_config)
        return
    
    # 处理 --list-packages
    if args.list_packages:
        from package_library import ComponentLibrarySystem
        lib = ComponentLibrarySystem(custom_lib_path=args.package_lib)
        lib.list_packages()
        return
    
    run_pipeline(
        input_path=args.input,
        output_dir=args.output,
        threshold=args.threshold,
        create_overlay=not args.no_overlay,
        verbose=verbose,
        package_lib_path=args.package_lib,
        extract_drills=not args.no_drills,
    )


if __name__ == '__main__':
    main()