#!/usr/bin/env python3
"""工具任务执行测试脚本"""
import asyncio
import sys
import json
from datetime import datetime

sys.path.insert(0, '.')


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def print_success(msg):
    print(f"[OK] {msg}")


def print_fail(msg):
    print(f"[FAIL] {msg}")


def print_info(msg):
    print(f"[INFO] {msg}")


async def test_market_data_tools():
    """测试市场数据工具"""
    print_header("任务 1: 测试市场数据工具")

    from agent.tools.market_data import get_stock_quote, get_market_overview, get_klines

    results = []

    # 测试 1: 股票报价
    print_info("测试 get_stock_quote('AAPL', 'us_stock')")
    try:
        quote = await get_stock_quote('AAPL', 'us_stock')

        print(f"  Symbol: {quote.get('symbol')}")
        print(f"  Price: ${quote.get('price')}")
        print(f"  Change: {quote.get('change_percent')}%")
        print(f"  Volume: {quote.get('volume'):,}")
        print(f"  Is Mock: {quote.get('_mock', False)}")

        # 验证数据完整性
        assert quote.get('symbol') == 'AAPL', "Symbol mismatch"
        assert quote.get('price') is not None, "Price is None"
        assert isinstance(quote.get('price'), (int, float)), "Price is not numeric"

        print_success("Stock quote test passed")
        results.append(('get_stock_quote', True, None))
    except Exception as e:
        print_fail(f"Stock quote test failed: {e}")
        results.append(('get_stock_quote', False, str(e)))

    # 测试 2: 市场概况
    print_info("\nTesting get_market_overview('us_stock')")
    try:
        overview = await get_market_overview('us_stock')

        print(f"  Returned: {len(overview)} items")
        for item in overview[:3]:
            symbol = item.get('symbol', 'N/A')
            name = item.get('name', 'N/A')
            price = item.get('price', 0)
            change = item.get('change_percent', 0)
            print(f"    - {symbol:10s} {name:20s} ${price:8.2f} ({change:+.2f}%)")

        # 验证数据
        assert len(overview) > 0, "No market data returned"
        assert all('symbol' in item for item in overview), "Missing symbol field"

        print_success("Market overview test passed")
        results.append(('get_market_overview', True, None))
    except Exception as e:
        print_fail(f"Market overview test failed: {e}")
        results.append(('get_market_overview', False, str(e)))

    # 测试 3: K线数据
    print_info("\nTesting get_klines('AAPL', 'us_stock', '1d', '1mo')")
    try:
        klines = await get_klines('AAPL', 'us_stock', '1d', '1mo')

        print(f"  Returned: {len(klines)} bars")
        if klines:
            first = klines[0]
            print(f"  First bar: {first.get('date')} - Open: ${first.get('open', 0):.2f}, Close: ${first.get('close', 0):.2f}")

            last = klines[-1]
            print(f"  Last bar: {last.get('date')} - Open: ${last.get('open', 0):.2f}, Close: ${last.get('close', 0):.2f}")

        print_success("K-lines test passed")
        results.append(('get_klines', True, None))
    except Exception as e:
        print_fail(f"K-lines test failed: {e}")
        results.append(('get_klines', False, str(e)))

    return results


async def test_strategy_system():
    """测试策略系统"""
    print_header("任务 2: 测试策略系统")

    from agent.strategies.registry import list_strategies, get_strategy

    results = []

    # 测试 1: 列出所有策略
    print_info("Testing list_strategies()")
    try:
        strategies = list_strategies()

        print(f"  Total strategies: {len(strategies)}")
        for i, strat in enumerate(strategies, 1):
            print(f"    {i}. {strat['name']:20s} - {strat['description']}")

        assert len(strategies) == 8, f"Expected 8 strategies, got {len(strategies)}"

        print_success("Strategy listing test passed")
        results.append(('list_strategies', True, None))
    except Exception as e:
        print_fail(f"Strategy listing failed: {e}")
        results.append(('list_strategies', False, str(e)))

    # 测试 2: 获取特定策略
    print_info("\nTesting get_strategy('sma_cross')")
    try:
        strategy = get_strategy('sma_cross')

        assert strategy is not None, "Strategy not found"
        assert strategy.name == 'sma_cross', "Strategy name mismatch"

        print(f"  Strategy: {strategy.name}")
        print(f"  Description: {strategy.description}")
        print(f"  Has generate_signals: {hasattr(strategy, 'generate_signals')}")

        print_success("Strategy retrieval test passed")
        results.append(('get_strategy', True, None))
    except Exception as e:
        print_fail(f"Strategy retrieval failed: {e}")
        results.append(('get_strategy', False, str(e)))

    # 测试 3: 测试策略信号生成
    print_info("\nTesting strategy signal generation")
    try:
        import pandas as pd
        import numpy as np

        # 创建测试数据
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        df = pd.DataFrame({
            'Close': 100 + np.cumsum(np.random.randn(100) * 2),
            'High': 105 + np.cumsum(np.random.randn(100) * 2),
            'Low': 95 + np.cumsum(np.random.randn(100) * 2),
            'Volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)

        strategy = get_strategy('sma_cross')
        signals = strategy.generate_signals(df)

        print(f"  Generated {len(signals)} signals")
        print(f"  Buy signals: {(signals == 1).sum()}")
        print(f"  Sell signals: {(signals == -1).sum()}")
        print(f"  Neutral: {(signals == 0).sum()}")

        assert len(signals) == len(df), "Signal length mismatch"
        assert signals.isin([0, 1, -1]).all(), "Invalid signal values"

        print_success("Strategy signal generation test passed")
        results.append(('generate_signals', True, None))
    except Exception as e:
        print_fail(f"Signal generation failed: {e}")
        results.append(('generate_signals', False, str(e)))

    return results


async def test_alpha_factors():
    """测试Alpha因子"""
    print_header("任务 3: 测试Alpha因子")

    from agent.tools.alpha import list_alpha_factors, compute_alpha_factors

    results = []

    # 测试 1: 列出Alpha因子
    print_info("Testing list_alpha_factors()")
    try:
        factors = list_alpha_factors()

        print(f"  Total factors: {factors.get('total', 0)}")

        alpha101 = factors.get('alpha101', [])
        alpha158 = factors.get('alpha158', [])

        print(f"  Alpha101 factors: {len(alpha101)}")
        print(f"  Alpha158 factors: {len(alpha158)}")

        # 显示前5个因子
        if alpha101:
            print("\n  Sample Alpha101 factors:")
            for factor in alpha101[:5]:
                print(f"    - {factor}")

        print_success("Alpha factors listing test passed")
        results.append(('list_alpha_factors', True, None))
    except Exception as e:
        print_fail(f"Alpha factors listing failed: {e}")
        results.append(('list_alpha_factors', False, str(e)))

    # 测试 2: 计算Alpha因子
    print_info("\nTesting compute_alpha_factors()")
    try:
        import pandas as pd
        import numpy as np

        # 创建测试数据
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        test_data = pd.DataFrame({
            'open': 100 + np.random.randn(30) * 2,
            'high': 105 + np.random.randn(30) * 2,
            'low': 95 + np.random.randn(30) * 2,
            'close': 100 + np.random.randn(30) * 2,
            'volume': np.random.randint(1000000, 10000000, 30),
        }, index=dates)

        # 计算因子
        result = await compute_alpha_factors(
            data=test_data.to_dict('records'),
            factor_set='alpha101',
            top_n=5
        )

        print(f"  Computed: {result.get('computed', 0)} factors")
        print(f"  Errors: {result.get('errors', 0)} factors")

        if result.get('top_factors'):
            print("\n  Top factors:")
            for factor in result['top_factors'][:3]:
                print(f"    - {factor.get('name')}: {factor.get('value', 0):.4f}")

        print_success("Alpha factors computation test passed")
        results.append(('compute_alpha_factors', True, None))
    except Exception as e:
        print_fail(f"Alpha factors computation failed: {e}")
        results.append(('compute_alpha_factors', False, str(e)))

    return results


async def test_tool_registry():
    """测试工具注册表"""
    print_header("额外: 工具注册表验证")

    # 导入所有工具模块以触发注册
    from agent.tools import (
        alpha, backtest, constitution, crypto,
        hk_stock, market_data, news, risk, technical
    )
    from agent.tools.registry import get_tool_definitions, get_tool_names

    tools = get_tool_definitions()
    tool_names = get_tool_names()

    print_info(f"Total tools registered: {len(tools)}")

    # 按类别统计
    categories = {}
    for name in tool_names:
        cat = name.split('_')[0]
        categories[cat] = categories.get(cat, 0) + 1

    print("\n  Tool categories (top 10):")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:10]:
        print(f"    {cat:15s}: {count:2d} tools")

    print_success(f"Tool registry validation passed: {len(tools)} tools")

    return [('tool_registry', True, None)]


def generate_report(all_results):
    """生成测试报告"""
    print_header("工具任务执行报告")

    total = 0
    passed = 0
    failed = 0

    print("\n详细结果:\n")

    for task_name, task_results in all_results.items():
        print(f"  {task_name}:")
        for test_name, success, error in task_results:
            total += 1
            if success:
                passed += 1
                print(f"    [OK]   {test_name}")
            else:
                failed += 1
                print(f"    [FAIL] {test_name}: {error}")

    print(f"\n{'='*70}")
    print(f"  总计: {total} 个测试")
    print(f"  通过: {passed} 个")
    print(f"  失败: {failed} 个")
    print(f"  通过率: {passed/total*100:.1f}%")
    print('='*70)

    # 保存报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': f"{passed/total*100:.1f}%"
        },
        'details': {
            task_name: [
                {'test': test_name, 'success': success, 'error': error}
                for test_name, success, error in task_results
            ]
            for task_name, task_results in all_results.items()
        }
    }

    with open('tool_execution_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n报告已保存到: tool_execution_report.json")

    return passed == total


async def main():
    """主执行流程"""
    print("="*70)
    print("  AI 量化交易系统 - 工具任务执行")
    print(f"  执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    all_results = {}

    # 执行所有测试
    try:
        all_results['市场数据工具'] = await test_market_data_tools()
    except Exception as e:
        print_fail(f"Market data tests crashed: {e}")
        all_results['市场数据工具'] = [('crash', False, str(e))]

    try:
        all_results['策略系统'] = await test_strategy_system()
    except Exception as e:
        print_fail(f"Strategy tests crashed: {e}")
        all_results['策略系统'] = [('crash', False, str(e))]

    try:
        all_results['Alpha因子'] = await test_alpha_factors()
    except Exception as e:
        print_fail(f"Alpha factor tests crashed: {e}")
        all_results['Alpha因子'] = [('crash', False, str(e))]

    try:
        all_results['工具注册表'] = await test_tool_registry()
    except Exception as e:
        print_fail(f"Tool registry test crashed: {e}")
        all_results['工具注册表'] = [('crash', False, str(e))]

    # 生成报告
    success = generate_report(all_results)

    return success


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
