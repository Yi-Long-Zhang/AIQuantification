"""
Multi-Agent System - Base Agent Module

This module provides the base class for all AI agents in the system.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional
from datetime import datetime

from agent.llm_client import LLMClient
from agent.tools.registry import get_tool_definitions, execute_tool

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Base class for all AI agents in the multi-agent system.

    Each agent has:
    - A unique name
    - An LLM client for reasoning
    - A set of available tools
    - A system prompt defining its role
    """

    def __init__(
        self,
        name: str,
        llm_client: LLMClient,
        tools: Optional[list[str]] = None,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the agent.

        Args:
            name: Unique identifier for this agent
            llm_client: LLM client for reasoning
            tools: List of tool names this agent can use
            system_prompt: Custom system prompt for this agent
        """
        self.name = name
        self.llm = llm_client
        self.tools = tools or []
        self.system_prompt = system_prompt or self._default_system_prompt()

        # Execution history
        self.execution_history: list[dict] = []

        logger.info(f"Initialized agent: {name} with {len(self.tools)} tools")

    def _default_system_prompt(self) -> str:
        """Generate default system prompt for this agent."""
        return f"""You are {self.name}, an AI agent in a quantitative trading system.

Your role: {self.__class__.__doc__ or 'Specialized trading agent'}

Available tools: {', '.join(self.tools) if self.tools else 'None'}

Guidelines:
1. Focus on your specific role
2. Use available tools to gather information
3. Provide structured, actionable outputs
4. Collaborate with other agents when needed
"""

    async def execute(self, task: dict) -> dict:
        """
        Execute a task assigned to this agent.

        Args:
            task: Task definition containing:
                - task_id: Unique task identifier
                - type: Task type
                - input: Task input data
                - context: Additional context

        Returns:
            dict: Task result containing:
                - task_id: Task identifier
                - agent: Agent name
                - status: SUCCESS/FAILED
                - output: Task output data
                - timestamp: Completion time
        """
        task_id = task.get('task_id', f"{self.name}_{datetime.now().timestamp()}")

        logger.info(f"Agent {self.name} executing task: {task_id}")

        try:
            # Prepare task context
            task_type = task.get('type', 'unknown')
            task_input = task.get('input', {})
            task_context = task.get('context', {})

            # Execute task based on type
            if task_type == 'analyze':
                output = await self._analyze(task_input, task_context)
            elif task_type == 'decide':
                output = await self._decide(task_input, task_context)
            elif task_type == 'evaluate':
                output = await self._evaluate(task_input, task_context)
            else:
                output = await self._custom_execute(task_type, task_input, task_context)

            result = {
                'task_id': task_id,
                'agent': self.name,
                'status': 'SUCCESS',
                'output': output,
                'timestamp': datetime.now().isoformat()
            }

            # Record execution
            self.execution_history.append({
                'task': task,
                'result': result
            })

            logger.info(f"Agent {self.name} completed task: {task_id}")
            return result

        except Exception as e:
            logger.error(f"Agent {self.name} failed task {task_id}: {e}")
            return {
                'task_id': task_id,
                'agent': self.name,
                'status': 'FAILED',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def _analyze(self, input_data: dict, context: dict) -> dict:
        """
        Analyze data and provide insights.

        To be overridden by specific agents.
        """
        raise NotImplementedError(f"Agent {self.name} must implement _analyze()")

    async def _decide(self, input_data: dict, context: dict) -> dict:
        """
        Make a decision based on analysis.

        To be overridden by specific agents.
        """
        raise NotImplementedError(f"Agent {self.name} must implement _decide()")

    async def _evaluate(self, input_data: dict, context: dict) -> dict:
        """
        Evaluate results or options.

        To be overridden by specific agents.
        """
        raise NotImplementedError(f"Agent {self.name} must implement _evaluate()")

    async def _custom_execute(self, task_type: str, input_data: dict, context: dict) -> dict:
        """
        Execute custom task types.

        Can be overridden by specific agents.
        """
        raise NotImplementedError(f"Agent {self.name} does not support task type: {task_type}")

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a tool and return its result.

        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            logger.warning(f"Agent {self.name} attempting to use unavailable tool: {tool_name}")

        try:
            logger.debug(f"Agent {self.name} calling tool: {tool_name}")
            result = await execute_tool(tool_name, **kwargs)
            logger.debug(f"Tool {tool_name} returned: {type(result)}")
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            raise

    async def ask_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Ask the LLM a question and get a response.

        Args:
            prompt: User prompt
            system_prompt: Optional override for system prompt

        Returns:
            LLM response text
        """
        messages = [
            {"role": "system", "content": system_prompt or self.system_prompt},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.llm.chat(messages)

            # Handle both dict and string responses
            if isinstance(response, dict):
                # Extract content from dict response
                if 'choices' in response and len(response['choices']) > 0:
                    return response['choices'][0]['message']['content']
                elif 'content' in response:
                    return response['content']
                else:
                    # Fallback: convert to string
                    return str(response)

            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    async def ask_llm_structured(
        self,
        prompt: str,
        schema: dict,
        system_prompt: Optional[str] = None
    ) -> dict:
        """
        Ask the LLM for a structured JSON response.

        Args:
            prompt: User prompt
            schema: JSON schema for expected response
            system_prompt: Optional override for system prompt

        Returns:
            Parsed JSON response
        """
        # Add JSON instruction to prompt
        json_prompt = f"""{prompt}

IMPORTANT: Respond with ONLY a valid JSON object matching this schema:
{json.dumps(schema, indent=2)}

Do not include any explanation, just the JSON object."""

        response = await self.ask_llm(json_prompt, system_prompt)

        # Parse JSON
        try:
            # Try to extract JSON if surrounded by other text
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Response: {response}")
            raise ValueError(f"LLM did not return valid JSON: {e}")

    def get_execution_summary(self) -> dict:
        """Get summary of agent's execution history."""
        total_tasks = len(self.execution_history)
        successful = sum(
            1 for h in self.execution_history
            if h['result']['status'] == 'SUCCESS'
        )
        failed = total_tasks - successful

        return {
            'agent': self.name,
            'total_tasks': total_tasks,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total_tasks if total_tasks > 0 else 0
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}, Tools: {len(self.tools)}>"
