# 快速入门

> 从零开始搭建并运行 AIQuantification。

---

## 一、环境要求

- Python 3.13+
- uv 包管理器（推荐）或 pip

## 二、安装

```bash
# 1. 克隆项目
git clone <项目地址>
cd AIQuantification

# 2. 创建虚拟环境（推荐）
uv venv
source .venv/bin/activate

# 3. 安装依赖
uv sync

# 如果没有 uv，也可以用 pip（但建议用 uv）：
# pip install -e .
# pip install pandas numpy yfinance pandas-ta httpx openai akshare pyyaml
```

## 三、配置

```bash
# 1. 创建配置文件
cp config.yaml.example config.yaml

# 2. 编辑 config.yaml，填入你的 API Key
#    推荐使用 DeepSeek（性价比高）或 OpenAI
vim config.yaml
```

最低配置示例：

```yaml
llm:
  provider: deepseek
  model: deepseek-chat
  api_key: "sk-你的key"
```

完整配置示例：

```yaml
llm:
  provider: deepseek
  model: deepseek-chat
  api_key: "sk-xxx"
  temperature: 0.3
  max_tokens: 4096
  fallback:
    provider: openai
    model: gpt-4o-mini
    api_key: "sk-xxx"

memory:
  db_path: "~/.aiquantification/memory.db"

constitution:
  path: "AGENT_CONSTITUTION.md"

server:
  host: "0.0.0.0"
  port: 8000
  reload: true
```

> ⚠️ `config.yaml` 已在 `.gitignore` 中，不会提交到 Git。
> 如果配置了 fallback，主 LLM 不可用时自动切换。

## 四、启动服务

```bash
# 标准启动
uvicorn main:app --reload --port 8000

# 或使用 config.yaml 中的端口配置
uvicorn main:app --reload
```

启动成功看到：

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

## 五、验证

```bash
# 1. 健康检查
curl http://localhost:8000/health
# → {"status":"ok","agent":"QuantAgent"}

# 2. 服务信息
curl http://localhost:8000/
# → {"name":"AIQuantification", "version":"0.1.0", ...}

# 3. 可用工具
curl http://localhost:8000/agent/tools
# → {"tools": ["get_stock_quote", "get_klines", ...], "count": 13}
```

## 六、Web 界面

浏览器访问 `http://localhost:8000/chat`，即可使用暗色主题的聊天界面。

![Web Chat UI](images/chat-ui.png)（启动后在浏览器中查看）

## 七、API 文档

访问 `http://localhost:8000/docs` 查看 Swagger UI 交互式文档。

## 八、下一步

| 教程 | 描述 |
|------|------|
| [市场分析](tutorial-analysis.md) | 获取行情、技术分析、生成信号 |
| [策略回测](tutorial-backtest.md) | 编写策略、运行回测、结果解读 |

## 九、常见问题

### Q: `ModuleNotFoundError: No module named 'yaml'`

```bash
uv pip install pyyaml
```

### Q: `ValueError: Missing api_key for provider 'deepseek'`

检查 `config.yaml` 中是否正确配置了 `llm.api_key`。

### Q: LLM 返回空或错误

- 检查 API Key 是否有效
- 检查网络是否能访问 API 地址
- 检查 `config.yaml` 中 `provider` 字段是否正确
- 如果有 fallback 配置，会自动切换

### Q: 数据获取失败

- 美股数据: 无需配置，直接使用 yfinance
- A 股数据: 无需配置，直接使用 AKShare
- 如果被限流，等待几分钟后重试
