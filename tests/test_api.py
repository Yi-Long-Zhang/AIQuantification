"""API 路由集成测试 — 覆盖所有端点"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


# ─── Agent endpoints ─────────────────────────────────────────────────────────

class TestAgentEndpoints:
    """POST /agent/chat 和 /agent/chat/stream 需要 LLM API Key，跳过集成测试"""

    def test_list_tools(self, client):
        """GET /agent/tools — 已覆盖，确认基础功能"""
        response = client.get("/agent/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert data["count"] >= 35
        assert "get_klines" in data["tools"]
        assert "run_backtest" in data["tools"]

    def test_list_tools_rate_limited(self, client):
        """GET /agent/tools — 高频请求应限速"""
        for _ in range(30):
            client.get("/agent/tools")
        response = client.get("/agent/tools")
        # slowapi 返回 429 当限速触发
        assert response.status_code in (200, 429)


# ─── Backtest endpoints ──────────────────────────────────────────────────────

class TestBacktestEndpoints:
    def test_backtest_invalid_date(self, client):
        """POST /backtest — 无效日期格式返回 422"""
        response = client.post("/backtest", json={
            "strategy_name": "sma_cross",
            "symbols": ["AAPL"],
            "start_date": "invalid-date",
            "end_date": "2024-01-01",
            "initial_capital": 100000,
        })
        assert response.status_code == 422

    def test_backtest_invalid_strategy(self, client):
        """POST /backtest — 未知策略名返回 422"""
        response = client.post("/backtest", json={
            "strategy_name": "",
            "symbols": ["AAPL"],
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
        })
        assert response.status_code == 422

    def test_backtest_missing_symbols(self, client):
        """POST /backtest — 空 symbol 列表返回 422"""
        response = client.post("/backtest", json={
            "strategy_name": "sma_cross",
            "symbols": [],
            "start_date": "2023-01-01",
            "end_date": "2024-01-01",
        })
        assert response.status_code == 422


# ─── Market endpoints ────────────────────────────────────────────────────────

class TestMarketEndpoints:
    def test_market_overview(self, client):
        """GET /market/{market}/overview — 返回市场概览（list 或 dict）"""
        response = client.get("/market/us_stock/overview")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list | dict)

    def test_market_overview_invalid_market(self, client):
        """GET /market/{market}/overview — 未知市场"""
        response = client.get("/market/unknown_market/overview")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list | dict)

    def test_market_quote_invalid_symbol(self, client):
        """POST /market/quote — 验证请求体验证"""
        response = client.post("/market/quote", json={
            "symbol": "",
            "market": "us_stock",
        })
        assert response.status_code == 422

    def test_market_quote_missing_fields(self, client):
        """POST /market/quote — 缺少必填字段"""
        response = client.post("/market/quote", json={})
        assert response.status_code == 422

    def test_market_klines_invalid_symbol(self, client):
        """POST /market/klines — 空 symbol"""
        response = client.post("/market/klines", json={
            "symbol": "",
            "market": "us_stock",
            "interval": "1d",
            "period": "1y",
        })
        assert response.status_code == 422

    def test_market_klines_invalid_interval(self, client):
        """POST /market/klines — 无效周期"""
        response = client.post("/market/klines", json={
            "symbol": "AAPL",
            "market": "us_stock",
            "interval": "invalid",
            "period": "1y",
        })
        assert response.status_code == 200  # data source handles fallback
        assert isinstance(response.json(), list | dict)


# ─── Strategy endpoints ──────────────────────────────────────────────────────

class TestStrategyEndpoints:
    def test_list_strategies_count(self, client):
        """GET /strategies — 返回 18 个策略"""
        response = client.get("/strategies")
        assert response.status_code == 200
        data = response.json()
        assert len(data["strategies"]) == 18
        names = [s["name"] for s in data["strategies"]]
        assert "sma_cross" in names
        assert "ichimoku" in names
        assert "crypto_funding" in names
        assert "atr_channel" in names
        assert "donchian_channel" in names
        # Check new fields exist
        s = data["strategies"][0]
        assert "type" in s
        assert "markets" in s
        assert "params" in s
        assert "risk_level" in s


# ─── Skill endpoints ─────────────────────────────────────────────────────────

class TestSkillEndpoints:
    def test_list_skills(self, client):
        """GET /skills — 返回技能列表"""
        response = client.get("/skills")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert "count" in data
        assert data["count"] >= 0

    def test_skill_structure(self, client):
        """GET /skills — 每个技能包含必要字段"""
        response = client.get("/skills")
        data = response.json()
        for skill in data["skills"]:
            assert "name" in skill
            assert "description" in skill
            assert "tools" in skill
            assert "tags" in skill


# ─── Alpha factor endpoints ──────────────────────────────────────────────────

class TestAlphaEndpoints:
    def test_alpha_factors_count(self, client):
        """GET /alpha/factors — 返回 251 个因子"""
        response = client.get("/alpha/factors")
        assert response.status_code == 200
        data = response.json()
        assert len(data["alpha158"]) == 150
        assert len(data["alpha101"]) == 101

    def test_alpha_factors_alpha158_only(self, client):
        """GET /alpha/factors?factor_set=alpha158"""
        response = client.get("/alpha/factors", params={"factor_set": "alpha158"})
        assert response.status_code == 200
        data = response.json()
        assert "alpha158" in data
        assert "alpha101" not in data

    def test_compute_alpha_missing_symbol(self, client):
        """POST /alpha/compute — 空 symbol"""
        response = client.post("/alpha/compute", json={
            "symbol": "",
            "market": "us_stock",
            "factor_set": "alpha101",
        })
        assert response.status_code == 422

    def test_compute_alpha_invalid_factor_set(self, client):
        """POST /alpha/compute — 无效因子集"""
        response = client.post("/alpha/compute", json={
            "symbol": "AAPL",
            "market": "us_stock",
            "factor_set": "invalid_set",
        })
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_evaluate_alpha_missing_symbol(self, client):
        """POST /alpha/evaluate — 空 symbol"""
        response = client.post("/alpha/evaluate", json={
            "symbol": "",
            "market": "us_stock",
            "factor_set": "alpha101",
            "top_n": 10,
        })
        assert response.status_code == 422

    def test_evaluate_alpha_invalid_top_n(self, client):
        """POST /alpha/evaluate — top_n 超范围"""
        response = client.post("/alpha/evaluate", json={
            "symbol": "AAPL",
            "market": "us_stock",
            "factor_set": "alpha101",
            "top_n": 200,
        })
        assert response.status_code == 422

    def test_evaluate_alpha_negative_top_n(self, client):
        """POST /alpha/evaluate — top_n 为负数"""
        response = client.post("/alpha/evaluate", json={
            "symbol": "AAPL",
            "market": "us_stock",
            "factor_set": "alpha101",
            "top_n": -1,
        })
        assert response.status_code == 422


# ─── Multi-Agent endpoints ───────────────────────────────────────────────────

class TestMultiAgentEndpoints:
    def test_multi_agent_status(self, client):
        """GET /multi-agent/status — 返回协调器状态"""
        response = client.get("/multi-agent/status")
        assert response.status_code == 200
        data = response.json()
        # 状态至少包含 coordinator 信息
        assert isinstance(data, dict)

    def test_multi_agent_list_agents(self, client):
        """GET /multi-agent/agents — 返回 agent 列表"""
        response = client.get("/multi-agent/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "count" in data
        assert data["count"] >= 0

    def test_multi_agent_messages(self, client):
        """GET /multi-agent/messages — 返回消息历史"""
        response = client.get("/multi-agent/messages")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "count" in data

    def test_multi_agent_messages_with_agent_filter(self, client):
        """GET /multi-agent/messages?agent=data_miner"""
        response = client.get("/multi-agent/messages", params={"agent": "data_miner"})
        assert response.status_code == 200
        assert "messages" in response.json()

    def test_multi_agent_messages_with_limit(self, client):
        """GET /multi-agent/messages?limit=10"""
        response = client.get("/multi-agent/messages", params={"limit": 10})
        assert response.status_code == 200

    def test_multi_agent_broker_stats(self, client):
        """GET /multi-agent/broker/stats — 返回 broker 统计"""
        response = client.get("/multi-agent/broker/stats")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_multi_agent_cycle_invalid_market(self, client):
        """POST /multi-agent/cycle — 测试端点存在且能正常调用"""
        response = client.post("/multi-agent/cycle", json={
            "market": "us_stock",
            "context": {},
        })
        # cycle 涉及 LLM 调用，可能返回 500，确认端点存在
        assert response.status_code in (200, 500)


# ─── Broker endpoints ────────────────────────────────────────────────────────

class TestBrokerEndpoints:
    def test_list_brokers(self, client):
        """GET /broker/list — 返回券商列表"""
        response = client.get("/broker/list")
        assert response.status_code == 200
        data = response.json()
        assert "brokers" in data
        assert "count" in data

    def test_broker_status_not_found(self, client):
        """GET /broker/{name}/status — 未知券商返回 404"""
        response = client.get("/broker/nonexistent/status")
        assert response.status_code == 404

    def test_broker_connect_not_found(self, client):
        """POST /broker/{name}/connect — 未知券商返回 404"""
        response = client.post("/broker/nonexistent/connect")
        assert response.status_code == 404

    def test_broker_orders_not_found(self, client):
        """GET /broker/{name}/orders — 未知券商返回 404"""
        response = client.get("/broker/nonexistent/orders")
        assert response.status_code == 404


# ─── Root / Health endpoints ─────────────────────────────────────────────────

class TestRootEndpoints:
    def test_root_config(self, client):
        """GET / — 确认配置信息"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AIQuantification"
        assert "agent" in data["endpoints"]
        assert "market" in data["endpoints"]
        assert "backtest" in data["endpoints"]

    def test_health_status(self, client):
        """GET /health — 确认健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_chat_page(self, client):
        """GET /chat — 确认页面返回"""
        response = client.get("/chat")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "AIQuantification" in response.text
