import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AIQuantification"
    assert "endpoints" in data
    assert "config" in data


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["agent"] == "QuantAgent"


def test_list_tools_endpoint(client):
    response = client.get("/agent/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert "count" in data
    assert data["count"] > 0
    assert "get_klines" in data["tools"]
    assert "run_backtest" in data["tools"]


def test_list_strategies_endpoint(client):
    response = client.get("/strategies")
    assert response.status_code == 200
    data = response.json()
    assert "strategies" in data
    assert len(data["strategies"]) >= 8
    strategy_names = [s["name"] for s in data["strategies"]]
    assert "sma_cross" in strategy_names
    assert "crypto_funding" in strategy_names


def test_chat_page(client):
    response = client.get("/chat")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_alpha_factors_list(client):
    response = client.get("/alpha/factors")
    assert response.status_code == 200
    data = response.json()
    assert "alpha158" in data
    assert "alpha101" in data
    assert len(data["alpha158"]) == 150
    assert len(data["alpha101"]) == 101


def test_alpha_factors_tools_count(client):
    response = client.get("/agent/tools")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 35
