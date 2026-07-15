#!/usr/bin/env python3
"""快速项目审计脚本"""
import sys
import os
from pathlib import Path

sys.path.insert(0, '.')

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_tool_registry():
    """测试工具注册表"""
    print_section("1. 工具注册表测试")

    try:
        # 导入所有工具模块
        from agent.tools import (
            alpha, backtest, constitution, crypto,
            hk_stock, market_data, news, risk, technical
        )
        from agent.tools.registry import get_tool_definitions, get_tool_names

        tools = get_tool_definitions()
        tool_names = get_tool_names()

        print(f"已注册工具总数: {len(tools)}")

        # 按类别统计
        categories = {}
        for name in tool_names:
            cat = name.split('_')[0]
            categories[cat] = categories.get(cat, 0) + 1

        print("\n工具分类统计 (Top 10):")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:10]:
            print(f"  - {cat:20s}: {count:2d} 个")

        print(f"\n工具示例 (前15个):")
        for i, name in enumerate(tool_names[:15], 1):
            print(f"  {i:2d}. {name}")

        return {'status': 'PASS', 'count': len(tools)}
    except Exception as e:
        print(f"[失败] {e}")
        return {'status': 'FAIL', 'error': str(e)}

def test_strategies():
    """测试策略注册表"""
    print_section("2. 策略注册表测试")

    try:
        from agent.strategies.registry import get_all_strategies

        strategies = get_all_strategies()
        print(f"已注册策略总数: {len(strategies)}")

        print("\n策略列表:")
        for i, strat in enumerate(strategies, 1):
            print(f"  {i}. {strat.name:30s}")

        return {'status': 'PASS', 'count': len(strategies)}
    except Exception as e:
        print(f"[失败] {e}")
        return {'status': 'FAIL', 'error': str(e)}

def check_code_structure():
    """检查代码结构"""
    print_section("3. 代码结构检查")

    try:
        # 统计 Python 文件
        py_files = list(Path('.').rglob('*.py'))
        py_files = [f for f in py_files if '.venv' not in str(f) and 'node_modules' not in str(f)]

        print(f"Python 文件总数: {len(py_files)}")

        # 按目录统计
        dirs = {}
        for f in py_files:
            dir_name = str(f.parent).split(os.sep)[0]
            dirs[dir_name] = dirs.get(dir_name, 0) + 1

        print("\n目录分布:")
        for d, count in sorted(dirs.items(), key=lambda x: -x[1])[:10]:
            print(f"  - {d:20s}: {count:3d} 个文件")

        # 检查关键目录
        key_dirs = ['agent', 'api', 'models', 'tests', 'web']
        print("\n关键目录:")
        for d in key_dirs:
            exists = Path(d).exists()
            print(f"  - {d:20s}: {'存在' if exists else '缺失'}")

        return {'status': 'PASS', 'count': len(py_files)}
    except Exception as e:
        print(f"[失败] {e}")
        return {'status': 'FAIL', 'error': str(e)}

def check_frontend():
    """检查前端项目"""
    print_section("4. 前端项目检查")

    try:
        web_dir = Path('web')

        if not web_dir.exists():
            print("[警告] web 目录不存在")
            return {'status': 'WARN', 'message': 'web directory missing'}

        # 统计 Vue/TS 文件
        vue_files = list(web_dir.rglob('*.vue'))
        ts_files = [f for f in web_dir.rglob('*.ts') if 'node_modules' not in str(f)]

        print(f"Vue 文件数量:  {len(vue_files)}")
        print(f"TS 文件数量:   {len(ts_files)}")
        print(f"总计:          {len(vue_files) + len(ts_files)}")

        # 检查关键文件
        package_json = web_dir / 'package.json'
        node_modules = web_dir / 'node_modules'
        vite_config = web_dir / 'vite.config.ts'

        print(f"\n关键文件:")
        print(f"  package.json:   {'存在' if package_json.exists() else '缺失'}")
        print(f"  node_modules:   {'已安装' if node_modules.exists() else '未安装'}")
        print(f"  vite.config.ts: {'存在' if vite_config.exists() else '缺失'}")

        if package_json.exists():
            import json
            with open(package_json, 'r', encoding='utf-8') as f:
                pkg = json.load(f)
                deps = pkg.get('dependencies', {})
                dev_deps = pkg.get('devDependencies', {})
                print(f"\n依赖包:")
                print(f"  dependencies:     {len(deps)}")
                print(f"  devDependencies:  {len(dev_deps)}")
                print(f"  总计:             {len(deps) + len(dev_deps)}")

        return {'status': 'PASS', 'vue_files': len(vue_files), 'ts_files': len(ts_files)}
    except Exception as e:
        print(f"[失败] {e}")
        return {'status': 'FAIL', 'error': str(e)}

def check_git_status():
    """检查 Git 状态"""
    print_section("5. Git 状态检查")

    import subprocess

    try:
        # 检查当前分支
        branch = subprocess.check_output(['git', 'branch', '--show-current'],
                                        encoding='utf-8').strip()
        print(f"当前分支: {branch}")

        # 检查修改状态
        status = subprocess.check_output(['git', 'status', '--short'],
                                        encoding='utf-8')

        modified = [line for line in status.split('\n') if line.startswith(' M')]
        untracked = [line for line in status.split('\n') if line.startswith('??')]

        print(f"\n文件状态:")
        print(f"  修改的文件:   {len(modified)}")
        print(f"  未跟踪文件:   {len(untracked)}")

        if modified:
            print("\n修改的文件:")
            for line in modified[:5]:
                print(f"  {line}")
            if len(modified) > 5:
                print(f"  ... 还有 {len(modified)-5} 个文件")

        # 最近的提交
        log = subprocess.check_output(['git', 'log', '-3', '--oneline'],
                                     encoding='utf-8')
        print("\n最近3次提交:")
        for line in log.split('\n'):
            if line:
                print(f"  {line}")

        return {'status': 'PASS', 'modified': len(modified), 'untracked': len(untracked)}
    except Exception as e:
        print(f"[失败] {e}")
        return {'status': 'FAIL', 'error': str(e)}

def check_documentation():
    """检查文档"""
    print_section("6. 文档检查")

    try:
        # 统计 Markdown 文件
        md_files = list(Path('.').glob('*.md'))
        docs_md = list(Path('docs').glob('*.md')) if Path('docs').exists() else []

        print(f"根目录 .md 文件: {len(md_files)}")
        print(f"docs/ 目录文件:  {len(docs_md)}")
        print(f"总计:            {len(md_files) + len(docs_md)}")

        print("\n根目录文档:")
        for f in sorted(md_files)[:10]:
            print(f"  - {f.name}")

        if len(md_files) > 10:
            print(f"  ... 还有 {len(md_files)-10} 个文件")

        return {'status': 'PASS', 'count': len(md_files) + len(docs_md)}
    except Exception as e:
        print(f"[失败] {e}")
        return {'status': 'FAIL', 'error': str(e)}

def main():
    """主测试流程"""
    print("="*60)
    print("  AI 量化交易系统 - 快速审计报告")
    print("  " + "2026-07-15")
    print("="*60)

    results = {}

    # 执行所有测试
    results['工具注册表'] = test_tool_registry()
    results['策略注册表'] = test_strategies()
    results['代码结构'] = check_code_structure()
    results['前端项目'] = check_frontend()
    results['Git状态'] = check_git_status()
    results['文档'] = check_documentation()

    # 汇总报告
    print_section("审计结果汇总")

    passed = sum(1 for r in results.values() if r['status'] == 'PASS')
    warned = sum(1 for r in results.values() if r['status'] == 'WARN')
    failed = sum(1 for r in results.values() if r['status'] == 'FAIL')
    total = len(results)

    print(f"\n测试项目: {total}")
    print(f"通过:     {passed}")
    print(f"警告:     {warned}")
    print(f"失败:     {failed}")
    print(f"通过率:   {passed/total*100:.1f}%")

    print("\n详细结果:")
    for test_name, result in results.items():
        status = result['status']
        icon = "✓" if status == 'PASS' else ("!" if status == 'WARN' else "✗")
        extra = ""
        if 'count' in result:
            extra = f" ({result['count']} 项)"
        elif 'vue_files' in result:
            extra = f" ({result['vue_files']} Vue, {result['ts_files']} TS)"
        print(f"  [{icon}] {test_name:15s} - {status:4s}{extra}")

    print("\n" + "="*60)
    if failed == 0:
        print("  审计结果: 全部通过 ✓")
    else:
        print(f"  审计结果: {failed} 项失败")
    print("="*60)

    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
