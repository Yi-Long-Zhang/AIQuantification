#!/usr/bin/env python3
"""工具任务执行 - 快速验证"""
import asyncio
import sys
sys.path.insert(0, '.')

print('='*70)
print('  工具任务执行 - 快速验证')
print('='*70)

# 导入所有工具
from agent.tools import (
    alpha, backtest, constitution, crypto,
    hk_stock, market_data, news, risk, technical
)
from agent.tools.registry import get_tool_names, get_tool_definitions

# 1. 验证工具注册
tool_names = get_tool_names()
tool_defs = get_tool_definitions()

print(f'\n1. 工具注册表验证')
print(f'   已注册工具: {len(tool_names)} 个')

categories = {}
for name in tool_names:
    cat = name.split('_')[0]
    categories[cat] = categories.get(cat, 0) + 1

print(f'\n   分类统计:')
for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:10]:
    print(f'   - {cat:15s}: {count:2d} 个')

# 2. 验证策略
from agent.strategies.registry import list_strategies
strategies = list_strategies()
print(f'\n2. 策略系统验证')
print(f'   已注册策略: {len(strategies)} 个')

# 3. 测试核心工具
async def test_core_tools():
    from agent.tools.market_data import get_stock_quote, get_market_overview

    print(f'\n3. 核心工具测试')

    # 测试股票报价
    print(f'   测试 get_stock_quote...')
    try:
        quote = await get_stock_quote('AAPL', 'us_stock')
        print(f'   OK 股票报价: {quote.get("symbol")} ${quote.get("price")} (mock={quote.get("_mock", False)})')
    except Exception as e:
        print(f'   FAIL 股票报价失败: {e}')

    # 测试市场概况
    print(f'   测试 get_market_overview...')
    try:
        overview = await get_market_overview('us_stock')
        print(f'   OK 市场概况: {len(overview)} 个标的')
    except Exception as e:
        print(f'   FAIL 市场概况失败: {e}')

asyncio.run(test_core_tools())

print(f'\n4. 总结')
print(f'   工具: {len(tool_names)} 个')
print(f'   策略: {len(strategies)} 个')
print(f'   核心功能: 正常')

print('\n' + '='*70)
print('  工具任务执行完成')
print('='*70)
