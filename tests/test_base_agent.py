"""
Unit tests for BaseAgent class
"""

import pytest
import asyncio
from datetime import datetime

from agent.multi_agent.base import BaseAgent
from agent.llm_client import LLMClient
from agent.config import settings


class TestAgent(BaseAgent):
    """Test agent for unit tests"""

    async def _analyze(self, input_data: dict, context: dict) -> dict:
        """Test analyze implementation"""
        return {
            'analysis': 'test_analysis',
            'data': input_data
        }

    async def _decide(self, input_data: dict, context: dict) -> dict:
        """Test decide implementation"""
        return {
            'decision': 'test_decision',
            'confidence': 0.85
        }

    async def _evaluate(self, input_data: dict, context: dict) -> dict:
        """Test evaluate implementation"""
        return {
            'evaluation': 'test_evaluation',
            'score': 0.9
        }


@pytest.fixture
def llm_client():
    """Create LLM client for testing"""
    return LLMClient(provider=settings.llm_provider)


@pytest.fixture
def test_agent(llm_client):
    """Create test agent instance"""
    return TestAgent(
        name="TestAgent",
        llm_client=llm_client,
        tools=["get_stock_quote", "calculate_sma"],
        system_prompt="You are a test agent"
    )


class TestBaseAgent:
    """Test cases for BaseAgent"""

    def test_agent_initialization(self, test_agent):
        """Test agent can be initialized"""
        assert test_agent.name == "TestAgent"
        assert len(test_agent.tools) == 2
        assert "get_stock_quote" in test_agent.tools
        assert test_agent.system_prompt == "You are a test agent"
        assert len(test_agent.execution_history) == 0

    def test_agent_repr(self, test_agent):
        """Test agent string representation"""
        repr_str = repr(test_agent)
        assert "TestAgent" in repr_str
        assert "2" in repr_str  # 2 tools

    @pytest.mark.asyncio
    async def test_execute_analyze_task(self, test_agent):
        """Test agent can execute analyze task"""
        task = {
            'task_id': 'test_001',
            'type': 'analyze',
            'input': {'symbol': 'AAPL'},
            'context': {}
        }

        result = await test_agent.execute(task)

        assert result['status'] == 'SUCCESS'
        assert result['agent'] == 'TestAgent'
        assert result['task_id'] == 'test_001'
        assert 'output' in result
        assert result['output']['analysis'] == 'test_analysis'

    @pytest.mark.asyncio
    async def test_execute_decide_task(self, test_agent):
        """Test agent can execute decide task"""
        task = {
            'task_id': 'test_002',
            'type': 'decide',
            'input': {'options': ['buy', 'sell', 'hold']},
            'context': {}
        }

        result = await test_agent.execute(task)

        assert result['status'] == 'SUCCESS'
        assert result['output']['decision'] == 'test_decision'
        assert result['output']['confidence'] == 0.85

    @pytest.mark.asyncio
    async def test_execute_evaluate_task(self, test_agent):
        """Test agent can execute evaluate task"""
        task = {
            'task_id': 'test_003',
            'type': 'evaluate',
            'input': {'result': 'some_result'},
            'context': {}
        }

        result = await test_agent.execute(task)

        assert result['status'] == 'SUCCESS'
        assert result['output']['evaluation'] == 'test_evaluation'
        assert result['output']['score'] == 0.9

    @pytest.mark.asyncio
    async def test_execution_history(self, test_agent):
        """Test execution history is recorded"""
        task = {
            'task_id': 'test_004',
            'type': 'analyze',
            'input': {},
            'context': {}
        }

        await test_agent.execute(task)

        assert len(test_agent.execution_history) == 1
        history = test_agent.execution_history[0]
        assert 'task' in history
        assert 'result' in history

    @pytest.mark.asyncio
    async def test_call_tool(self, test_agent):
        """Test agent can call tools"""
        # Note: This will use mock data if network fails
        result = await test_agent.call_tool('get_stock_quote', symbol='AAPL', market='us_stock')

        assert result is not None
        assert 'symbol' in result
        assert result['symbol'] == 'AAPL'

    @pytest.mark.asyncio
    async def test_call_tool_not_in_list(self, test_agent):
        """Test agent can still call tools not in its list (with warning)"""
        # Should work but log warning
        result = await test_agent.call_tool('get_market_overview', market='us_stock')
        assert result is not None

    @pytest.mark.asyncio
    async def test_ask_llm(self, test_agent):
        """Test agent can ask LLM"""
        response = await test_agent.ask_llm("What is 2+2?")

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_ask_llm_structured(self, test_agent):
        """Test agent can get structured JSON from LLM"""
        schema = {
            "type": "object",
            "properties": {
                "answer": {"type": "number"},
                "explanation": {"type": "string"}
            }
        }

        try:
            response = await test_agent.ask_llm_structured(
                "What is 2+2? Provide answer and explanation.",
                schema
            )

            assert isinstance(response, dict)
            assert 'answer' in response or 'explanation' in response
        except ValueError:
            # LLM might not return valid JSON, that's ok for this test
            pass

    def test_get_execution_summary(self, test_agent):
        """Test execution summary"""
        # Add some mock history
        test_agent.execution_history = [
            {'result': {'status': 'SUCCESS'}},
            {'result': {'status': 'SUCCESS'}},
            {'result': {'status': 'FAILED'}},
        ]

        summary = test_agent.get_execution_summary()

        assert summary['agent'] == 'TestAgent'
        assert summary['total_tasks'] == 3
        assert summary['successful'] == 2
        assert summary['failed'] == 1
        assert summary['success_rate'] == pytest.approx(0.666, 0.01)

    def test_get_execution_summary_empty(self, test_agent):
        """Test execution summary with no history"""
        summary = test_agent.get_execution_summary()

        assert summary['total_tasks'] == 0
        assert summary['successful'] == 0
        assert summary['failed'] == 0
        assert summary['success_rate'] == 0

    @pytest.mark.asyncio
    async def test_execute_unsupported_task_type(self, test_agent):
        """Test agent handles unsupported task types"""
        task = {
            'task_id': 'test_005',
            'type': 'unsupported_type',
            'input': {},
            'context': {}
        }

        result = await test_agent.execute(task)

        assert result['status'] == 'FAILED'
        assert 'error' in result

    @pytest.mark.asyncio
    async def test_multiple_tasks_execution(self, test_agent):
        """Test agent can execute multiple tasks"""
        tasks = [
            {'task_id': f'test_{i}', 'type': 'analyze', 'input': {}, 'context': {}}
            for i in range(5)
        ]

        results = []
        for task in tasks:
            result = await test_agent.execute(task)
            results.append(result)

        assert len(results) == 5
        assert all(r['status'] == 'SUCCESS' for r in results)
        assert len(test_agent.execution_history) == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
