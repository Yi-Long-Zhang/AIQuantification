"""
Multi-Agent System - Communication Module

This module provides the communication infrastructure for agents to interact.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages agents can send"""
    REQUEST = "REQUEST"           # Request for action/information
    RESPONSE = "RESPONSE"         # Response to a request
    NOTIFICATION = "NOTIFICATION" # One-way notification
    BROADCAST = "BROADCAST"       # Message to all agents
    ERROR = "ERROR"               # Error notification


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class AgentMessage:
    """
    Message structure for agent communication.

    Each message has:
    - Sender and receiver
    - Message type and priority
    - Content payload
    - Metadata and timestamp
    """
    from_agent: str
    to_agent: str
    message_type: MessageType
    content: dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    message_id: str | None = None
    correlation_id: str | None = None  # For request-response correlation
    timestamp: str | None = None

    def __post_init__(self):
        """Generate message ID and timestamp if not provided"""
        if self.message_id is None:
            self.message_id = f"{self.from_agent}_{datetime.now().timestamp()}"
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert message to dictionary"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        data['priority'] = self.priority.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> AgentMessage:
        """Create message from dictionary"""
        data['message_type'] = MessageType(data['message_type'])
        data['priority'] = MessagePriority(data['priority'])
        return cls(**data)

    def create_response(self, content: dict[str, Any]) -> AgentMessage:
        """Create a response message to this message"""
        return AgentMessage(
            from_agent=self.to_agent,
            to_agent=self.from_agent,
            message_type=MessageType.RESPONSE,
            content=content,
            priority=self.priority,
            correlation_id=self.message_id
        )

    def __repr__(self) -> str:
        return (
            f"<Message {self.message_id}: "
            f"{self.from_agent} → {self.to_agent} "
            f"[{self.message_type.value}, P{self.priority.value}]>"
        )


class MessageBroker:
    """
    Message broker for agent communication.

    Handles:
    - Message routing between agents
    - Priority-based message queues
    - Asynchronous message delivery
    - Message history tracking
    """

    def __init__(self):
        """Initialize message broker"""
        # Agent-specific message queues
        self.queues: dict[str, asyncio.PriorityQueue] = {}

        # Monotonic counter used as tiebreaker in priority queue
        # so AgentMessage objects are never compared directly
        self._counter: int = 0

        # Message history for debugging
        self.message_history: list[AgentMessage] = []
        self.max_history = 1000

        # Registered agents
        self.agents: set[str] = set()

        # Statistics
        self.stats = {
            'total_messages': 0,
            'messages_by_type': {},
            'messages_by_agent': {}
        }

        logger.info("MessageBroker initialized")

    def register_agent(self, agent_name: str):
        """
        Register an agent with the broker.

        Args:
            agent_name: Name of the agent to register
        """
        if agent_name not in self.agents:
            self.agents.add(agent_name)
            self.queues[agent_name] = asyncio.PriorityQueue()
            logger.info(f"Registered agent: {agent_name}")

    def unregister_agent(self, agent_name: str):
        """
        Unregister an agent from the broker.

        Args:
            agent_name: Name of the agent to unregister
        """
        if agent_name in self.agents:
            self.agents.remove(agent_name)
            if agent_name in self.queues:
                del self.queues[agent_name]
            logger.info(f"Unregistered agent: {agent_name}")

    async def send(self, message: AgentMessage):
        """
        Send a message to an agent.

        Args:
            message: Message to send
        """
        # Handle broadcast messages
        if message.message_type == MessageType.BROADCAST:
            await self._broadcast(message)
            return

        # Validate recipient
        if message.to_agent not in self.agents:
            logger.warning(f"Agent {message.to_agent} not registered, auto-registering")
            self.register_agent(message.to_agent)

        # Add to recipient's queue with priority
        # Tuple: (negated_priority, counter, message) — counter breaks ties
        # so AgentMessage objects are never compared by heapq.
        priority = -message.priority.value
        self._counter += 1
        await self.queues[message.to_agent].put((priority, self._counter, message))

        # Update statistics
        self._update_stats(message)

        # Store in history
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)

        logger.debug(f"Sent message: {message}")

    async def _broadcast(self, message: AgentMessage):
        """
        Broadcast message to all agents except sender.

        Args:
            message: Broadcast message
        """
        recipients = [agent for agent in self.agents if agent != message.from_agent]

        for recipient in recipients:
            # Create individual message for each recipient
            individual_msg = AgentMessage(
                from_agent=message.from_agent,
                to_agent=recipient,
                message_type=MessageType.NOTIFICATION,
                content=message.content,
                priority=message.priority
            )
            await self.send(individual_msg)

        logger.debug(f"Broadcast message to {len(recipients)} agents")

    async def receive(self, agent_name: str, timeout: float | None = None) -> AgentMessage | None:
        """
        Receive a message for an agent.

        Args:
            agent_name: Name of the agent receiving
            timeout: Optional timeout in seconds

        Returns:
            Message if available, None if timeout
        """
        if agent_name not in self.queues:
            logger.warning(f"Agent {agent_name} not registered")
            self.register_agent(agent_name)

        try:
            if timeout:
                priority, _seq, message = await asyncio.wait_for(
                    self.queues[agent_name].get(),
                    timeout=timeout
                )
            else:
                priority, _seq, message = await self.queues[agent_name].get()

            logger.debug(f"Agent {agent_name} received: {message}")
            return message

        except asyncio.TimeoutError:
            return None

    async def request_response(
        self,
        from_agent: str,
        to_agent: str,
        content: dict[str, Any],
        timeout: float = 30.0,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> dict[str, Any] | None:
        """
        Send a request and wait for response.

        Args:
            from_agent: Sender agent name
            to_agent: Target agent name
            content: Request content
            timeout: Timeout in seconds
            priority: Message priority

        Returns:
            Response content if received, None if timeout
        """
        # Send request
        request = AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.REQUEST,
            content=content,
            priority=priority
        )
        await self.send(request)

        # Wait for response with correlation ID
        start_time = asyncio.get_event_loop().time()
        while True:
            remaining = timeout - (asyncio.get_event_loop().time() - start_time)
            if remaining <= 0:
                logger.warning(f"Request from {from_agent} to {to_agent} timed out")
                return None

            response = await self.receive(from_agent, timeout=remaining)
            if response is None:
                return None

            # Check if this is the response we're waiting for
            if (response.message_type == MessageType.RESPONSE and
                response.correlation_id == request.message_id):
                return response.content

            # Not our response, put it back (this is simplified, real impl would handle better)
            logger.debug(f"Received non-matching message, continuing to wait")

    def get_queue_size(self, agent_name: str) -> int:
        """
        Get the number of pending messages for an agent.

        Args:
            agent_name: Agent name

        Returns:
            Number of messages in queue
        """
        if agent_name in self.queues:
            return self.queues[agent_name].qsize()
        return 0

    def get_stats(self) -> dict:
        """Get broker statistics"""
        return {
            'registered_agents': len(self.agents),
            'agents': list(self.agents),
            'total_messages': self.stats['total_messages'],
            'messages_by_type': self.stats['messages_by_type'],
            'messages_by_agent': self.stats['messages_by_agent'],
            'queue_sizes': {
                agent: self.get_queue_size(agent)
                for agent in self.agents
            }
        }

    def get_message_history(
        self,
        agent_name: str | None = None,
        limit: int = 100
    ) -> list[AgentMessage]:
        """
        Get message history.

        Args:
            agent_name: Filter by agent (sender or receiver)
            limit: Maximum number of messages

        Returns:
            List of messages
        """
        if agent_name:
            filtered = [
                msg for msg in self.message_history
                if msg.from_agent == agent_name or msg.to_agent == agent_name
            ]
            return filtered[-limit:]
        return self.message_history[-limit:]

    def _update_stats(self, message: AgentMessage):
        """Update statistics"""
        self.stats['total_messages'] += 1

        # By type
        msg_type = message.message_type.value
        self.stats['messages_by_type'][msg_type] = \
            self.stats['messages_by_type'].get(msg_type, 0) + 1

        # By agent
        for agent in [message.from_agent, message.to_agent]:
            self.stats['messages_by_agent'][agent] = \
                self.stats['messages_by_agent'].get(agent, 0) + 1

    def clear_history(self):
        """Clear message history"""
        self.message_history.clear()
        logger.info("Message history cleared")

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_messages': 0,
            'messages_by_type': {},
            'messages_by_agent': {}
        }
        logger.info("Statistics reset")
