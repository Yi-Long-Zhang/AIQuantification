#!/usr/bin/env python3
"""项目审计和工具测试脚本"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, '.')

def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

async def test_tool_registry():
    """测试工具注册表"""
    print_section("1. 工具注册表测试")

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

    print("\n工具分类统计:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:10]:
        print(f"  - {cat:20s}: {count:2d} 个")

    print(f"\n前15个工具:")
    for i, name in enumerate(tool_names[:15], 1):
        print(f"  {i:2d}. {name}")

    return len(tools), tool_names

async def test_market_data():
    """测试市场数据工具"""
    print_section("2. 市场数据工具测试")

    from agent.tools.market_data import get_stock_quote, get_market_overview

    # 测试股票报价
    print("\n[测试] get_stock_quote('AAPL', 'us_stock')")
    try:
        quote = await get_stock_quote('AAPL', 'us_stock')
        print(f"  股票代码: {quote.get('symbol')}")
        print(f"  当前价格: ${quote.get('price')}")
        print(f"  涨跌幅:   {quote.get('change_percent')}%")
        print(f"  成交量:   {quote.get('volume'):,}")
        print(f"  模拟数据: {'是' if quote.get('_mock') else '否'}")
        print("  [通过] 股票报价测试成功")
        quote_pass = True
    except Exception as e:
        print(f"  [失败] 错误: {e}")
        quote_pass = False

    # 测试市场概况
    print("\n[测试] get_market_overview('us_stock')")
    try:
        overview = await get_market_overview('us_stock')
        print(f"  返回数量: {len(overview)} 个股票/指数")
        print("  前3个标的:")
        for item in overview[:3]:
            symbol = item.get('symbol', 'N/A')
            name = item.get('name', 'N/A')
            price = item.get('price', 0)
            change = item.get('change_percent', 0)
            print(f"    - {symbol:10s} {name:20s} ${price:8.2f} ({change:+.2f}%)")
        print("  [通过] 市场概况测试成功")
        overview_pass = True
    except Exception as e:
        print(f"  [失败] 错误: {e}")
        overview_pass = False

    return quote_pass and overview_pass

async def test_strategies():
    """测试策略注册表"""
    print_section("3. 策略注册表测试")

    from agent.strategies.registry import get_all_strategies

    strategies = get_all_strategies()
    print(f"已注册策略总数: {len(strategies)}")

    print("\n策略列表:")
    for i, strat in enumerate(strategies, 1):
        print(f"  {i}. {strat.name:30s} - {strat.description}")

    return len(strategies)

def check_frontend():
    """检查前端项目状态"""
    print_section("4. 前端项目检查")

    web_dir = Path('web')

    if not web_dir.exists():
        print("[失败] web 目录不存在")
        return False

    # 统计 Vue/TS 文件
    vue_files = list(web_dir.rglob('*.vue'))
    ts_files = [f for f in web_dir.rglob('*.ts') if 'node_modules' not in str(f)]

    print(f"Vue 文件数量:  {len(vue_files)}")
    print(f"TS 文件数量:   {len(ts_files)}")
    print(f"总计:          {len(vue_files) + len(ts_files)}")

    # 检查关键文件
    package_json = web_dir / 'package.json'
    node_modules = web_dir / 'node_modules'

    print(f"\n关键文件/目录:")
    print(f"  package.json:  {'存在' if package_json.exists() else '缺失'}")
    print(f"  node_modules:  {'已安装' if node_modules.exists() else '未安装'}")

    if package_json.exists():
        import json
        with open(package_json, 'r', encoding='utf-8') as f:
            pkg = json.load(f)
            deps = pkg.get('dependencies', {})
            print(f"  依赖包数量:    {len(deps)}")

    # 列出页面文件
    pages = list((web_dir / 'src' / 'pages').glob('*.vue')) if (web_dir / 'src' / 'pages').exists() else []
    print(f"\n页面文件 ({len(pages)}):")
    for page in pages:
        print(f"  - {page.name}")

    return True

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
        if status:
            print("\n修改的文件:")
            for line in status.split('\n')[:10]:
                if line:
                    print(f"  {line}")
        else:
            print("工作目录干净，无未提交的修改")

        # 最近的提交
        log = subprocess.check_output(['git', 'log', '-3', '--oneline'],
                                     encoding='utf-8')
        print("\n最近3次提交:")
        for line in log.split('\n'):
            if line:
                print(f"  {line}")

        return True
    except Exception as e:
        print(f"[失败] 无法获取 Git 状态: {e}")
        return False

async def main():
    """主测试流程"""
    print("="*60)
    print("  AI 量化交易系统 - 项目审计报告")
    print("="*60)

    results = {}

    # 1. 工具注册表测试
    try:
        tool_count, tool_names = await test_tool_registry()
        results['tools'] = {'status': 'PASS', 'count': tool_count}
    except Exception as e:
        print(f"\n[错误] 工具注册表测试失败: {e}")
        results['tools'] = {'status': 'FAIL', 'error': str(e)}

    # 2. 市场数据测试
    try:
        market_pass = await test_market_data()
        results['market_data'] = {'status': 'PASS' if market_pass else 'FAIL'}
    except Exception as e:
        print(f"\n[错误] 市场数据测试失败: {e}")
        results['market_data'] = {'status': 'FAIL', 'error': str(e)}

    # 3. 策略测试
    try:
        strategy_count = await test_strategies()
        results['strategies'] = {'status': 'PASS', 'count': strategy_count}
    except Exception as e:
        print(f"\n[错误] 策略测试失败: {e}")
        results['strategies'] = {'status': 'FAIL', 'error': str(e)}

    # 4. 前端检查
    try:
        frontend_ok = check_frontend()
        results['frontend'] = {'status': 'PASS' if frontend_ok else 'FAIL'}
    except Exception as e:
        print(f"\n[错误] 前端检查失败: {e}")
        results['frontend'] = {'status': 'FAIL', 'error': str(e)}

    # 5. Git 状态
    try:
        git_ok = check_git_status()
        results['git'] = {'status': 'PASS' if git_ok else 'FAIL'}
    except Exception as e:
        print(f"\n[错误] Git 检查失败: {e}")
        results['git'] = {'status': 'FAIL', 'error': str(e)}

    # 汇总报告
    print_section("审计结果汇总")

    passed = sum(1 for r in results.values() if r['status'] == 'PASS')
    total = len(results)

    print(f"\n测试项目: {total}")
    print(f"通过:     {passed}")
    print(f"失败:     {total - passed}")
    print(f"通过率:   {passed/total*100:.1f}%")

    print("\n详细结果:")
    for test_name, result in results.items():
        status_icon = "✓" if result['status'] == 'PASS' else "✗"
        count_info = f" ({result.get('count', 0)} 项)" if 'count' in result else ""
        print(f"  [{status_icon}] {test_name:20s} - {result['status']}{count_info}")

    print("\n" + "="*60)
    if passed == total:
        print("  审计结果: 全部通过 ✓")
    else:
        print(f"  审计结果: {total - passed} 项失败")
    print("="*60)

    return passed == total

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
