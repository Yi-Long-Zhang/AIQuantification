#!/usr/bin/env python3
"""完整工具执行测试 - 测试所有35个工具"""
import asyncio
import sys
import json
from datetime import datetime

sys.path.insert(0, '.')


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def print_result(tool_name, success, result=None, error=None):
    status = "[OK]" if success else "[FAIL]"
    print(f"{status:6s} {tool_name:40s}", end='')
    if error:
        print(f" - {error}")
    elif result:
        print(f" - {result}")
    else:
        print()


async def test_all_tools():
    """测试所有工具"""
    print_header("工具执行测试 - 测试所有35个工具")

    # 导入所有工具模块
    from agent.tools import (
        alpha, backtest, constitution, crypto,
        hk_stock, market_data, news, risk, technical
    )
    from agent.tools.registry import get_tool_names, execute_tool

    tool_names = get_tool_names()
    print(f"\n总工具数: {len(tool_names)}")

    results = []

    # 为每个工具定义测试参数
    tool_params = {
        # Alpha 因子
        'compute_alpha_factors': {'factors': ['alpha001', 'alpha002'], 'market_data': {}},
        'evaluate_alpha_factors': {'factors': {'alpha001': 0.5}},
        'list_alpha_factors': {},

        # 回测
        'run_backtest': {'strategy': 'sma_cross', 'symbol': 'AAPL', 'start_date': '2024-01-01', 'end_date': '2024-12-31'},
        'compare_strategies': {'strategies': ['sma_cross', 'macd'], 'symbol': 'AAPL', 'period': '1y'},
        'monte_carlo_test': {'strategy': 'sma_cross', 'symbol': 'AAPL', 'runs': 100},
        'walk_forward_test': {'strategy': 'sma_cross', 'symbol': 'AAPL', 'window': 90},

        # 合规
        'check_constitution': {'action': 'buy', 'symbol': 'AAPL', 'quantity': 100},

        # 市场数据
        'get_stock_quote': {'symbol': 'AAPL', 'market': 'us_stock'},
        'get_klines': {'symbol': 'AAPL', 'market': 'us_stock', 'interval': '1d', 'period': '1mo'},
        'get_cn_klines': {'symbol': '600519', 'interval': 'daily', 'period': '1mo'},
        'get_market_overview': {'market': 'us_stock'},
        'get_global_macro': {'indicator': 'gdp'},
        'get_sector_rotation': {'top_n': 10},

        # 加密货币
        'get_crypto_klines': {'symbol': 'BTC', 'interval': '1d', 'period': '1mo'},
        'get_crypto_realtime': {'symbol': 'BTC'},
        'get_crypto_overview': {},

        # 港股
        'get_hk_realtime': {'symbols': ['00700']},
        'get_hk_klines': {'symbol': '00700', 'interval': '1d', 'period': '1mo'},

        # 新闻
        'get_market_news': {'category': 'general', 'limit': 5},
        'get_stock_news': {'symbol': 'AAPL', 'limit': 5},

        # 风险
        'calculate_var': {'returns': [0.01, -0.02, 0.015, -0.01], 'confidence': 0.95},
        'calculate_sharpe': {'returns': [0.01, -0.02, 0.015, -0.01], 'risk_free_rate': 0.02},
        'calculate_max_drawdown': {'equity_curve': [100, 110, 105, 120, 115]},
        'calculate_portfolio_risk': {'positions': [{'symbol': 'AAPL', 'weight': 0.6}, {'symbol': 'MSFT', 'weight': 0.4}]},

        # 技术指标
        'calculate_sma': {'prices': [100, 102, 101, 103, 105], 'period': 3},
        'calculate_ema': {'prices': [100, 102, 101, 103, 105], 'period': 3},
        'calculate_rsi': {'prices': [100, 102, 101, 103, 105, 104, 106], 'period': 6},
        'calculate_macd': {'prices': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 110, 112, 111]},
        'calculate_bollinger': {'prices': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 110], 'period': 5, 'std_dev': 2},
        'calculate_atr': {'high': [105, 107, 106], 'low': [100, 101, 100], 'close': [103, 104, 102], 'period': 2},
        'calculate_obv': {'close': [100, 102, 101], 'volume': [1000, 1500, 1200]},
        'calculate_stochastic': {'high': [105, 107, 106, 108, 107], 'low': [100, 101, 100, 102, 101], 'close': [103, 104, 102, 105, 103], 'period': 3},
        'calculate_adx': {'high': [105, 107, 106], 'low': [100, 101, 100], 'close': [103, 104, 102], 'period': 2},
        'calculate_cci': {'high': [105, 107, 106], 'low': [100, 101, 100], 'close': [103, 104, 102], 'period': 2},
    }

    print_header("开始测试各个工具")

    for tool_name in sorted(tool_names):
        params = tool_params.get(tool_name, {})

        try:
            result = await execute_tool(tool_name, **params)

            # 判断结果是否有效
            if result is None:
                success = False
                error = "返回 None"
            elif isinstance(result, dict) and result.get('error'):
                success = False
                error = result.get('error')
            elif isinstance(result, list) and len(result) == 0:
                # 空列表可能是正常的（如没有新闻）
                success = True
                error = "返回空列表"
            else:
                success = True
                error = None

            # 简化结果显示
            result_str = None
            if isinstance(result, dict):
                if 'symbol' in result:
                    result_str = f"symbol={result.get('symbol')}"
                elif 'total' in result:
                    result_str = f"total={result.get('total')}"
                elif len(result) > 0:
                    result_str = f"{len(result)} keys"
            elif isinstance(result, list):
                result_str = f"{len(result)} items"
            elif isinstance(result, (int, float)):
                result_str = f"value={result:.4f}" if isinstance(result, float) else f"value={result}"

            print_result(tool_name, success, result_str, error)
            results.append({
                'tool': tool_name,
                'success': success,
                'result': str(result)[:100] if result else None,
                'error': error
            })

        except Exception as e:
            print_result(tool_name, False, None, str(e)[:50])
            results.append({
                'tool': tool_name,
                'success': False,
                'result': None,
                'error': str(e)[:100]
            })

    return results


def generate_report(results):
    """生成报告"""
    print_header("测试结果汇总")

    total = len(results)
    passed = sum(1 for r in results if r['success'])
    failed = total - passed

    print(f"\n总计: {total} 个工具")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print(f"通过率: {passed/total*100:.1f}%")

    if failed > 0:
        print("\n失败的工具:")
        for r in results:
            if not r['success']:
                print(f"  - {r['tool']:40s}: {r['error']}")

    # 保存报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': f"{passed/total*100:.1f}%"
        },
        'results': results
    }

    with open('tool_execution_full_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n详细报告已保存到: tool_execution_full_report.json")

    return passed == total


async def main():
    print("="*70)
    print("  AI 量化交易系统 - 完整工具执行测试")
    print(f"  执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    results = await test_all_tools()
    success = generate_report(results)

    return success


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
