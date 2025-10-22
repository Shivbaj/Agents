"""
Base Agent class - Foundation for all agents in the system
"""
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from uuid import uuid4

from langchain_core.language_models import BaseLanguageModel, BaseChatModel
from langchain_core.prompts import BasePromptTemplate
from langchain_core.tools import BaseTool
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

# Define BaseMemory locally for compatibility
from typing import Protocol, runtime_checkable

@runtime_checkable  
class BaseMemory(Protocol):
    """Base memory interface for compatibility"""
    pass

# Import memory with fallback
try:
    from langchain_community.memory import ConversationBufferWindowMemory
except ImportError:
    try:
        from langchain.memory import ConversationBufferWindowMemory
    except ImportError:
        ConversationBufferWindowMemory = None
from loguru import logger

from src.config.settings import get_settings


class AgentMessage:
    """Represents a message in an agent conversation"""
    
    def __init__(
        self,
        content: str,
        role: str = "assistant",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.role = role
        self.metadata = metadata or {}
        self.timestamp = datetime.now()


class AgentResponse:
    """Response from an agent"""
    
    def __init__(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now()


class BaseAgent(ABC):
    """
    Base class for all agents in the multi-agent system
    
    Provides common functionality and defines the interface that all agents must implement.
    Agents can be specialized for different tasks like text processing, vision, audio, etc.
    
    This agent integrates with LangChain for:
    - Language model abstraction
    - Memory management
    - Tool usage
    - Prompt templating
    - Callback handling
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        agent_type: str = "base",
        capabilities: Optional[List[str]] = None,
        llm: Optional[BaseLanguageModel] = None,
        memory: Optional[BaseMemory] = None,
        tools: Optional[List[BaseTool]] = None,
        prompt_template: Optional[BasePromptTemplate] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None,
        **kwargs
    ):
        self.id = agent_id or self._generate_agent_id()
        self.name = name or self.__class__.__name__
        self.description = description or "A base agent"
        self.agent_type = agent_type
        self.capabilities = capabilities or []
        
        # LangChain components
        self.llm = llm
        self.memory = memory or ConversationBufferWindowMemory(
            k=get_settings().agent_memory_size,
            return_messages=True
        )
        self.tools = tools or []
        self.prompt_template = prompt_template
        self.callbacks = callbacks or []
        
        # Configuration
        self.settings = get_settings()
        
        # Agent state
        self.is_initialized = False
        self.supports_streaming = False
        self.supports_multimodal = False
        self.supports_tools = len(self.tools) > 0
        
        # Legacy memory management (for backwards compatibility)
        self.conversations: Dict[str, List[AgentMessage]] = {}
        self.max_memory_size = self.settings.agent_memory_size
        
        # Performance tracking
        self.interaction_count = 0
        self.total_processing_time = 0.0
        
        logger.info(f"Created agent: {self.id} ({self.name})")
    
    def _generate_agent_id(self) -> str:
        """Generate a unique agent ID"""
        return f"{self.__class__.__name__.lower()}_{str(uuid4())[:8]}"
    
    async def initialize(self):
        """Initialize the agent (called when agent is loaded)"""
        try:
            logger.info(f"Initializing agent: {self.id}")
            
            # Perform any setup specific to the agent
            await self._initialize_agent()
            
            self.is_initialized = True
            logger.info(f"Agent initialized: {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.id}: {str(e)}")
            raise
    
    @abstractmethod
    async def _initialize_agent(self):
        """Agent-specific initialization logic (to be implemented by subclasses)"""
        pass
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AgentResponse:
        """
        Process a text message from a user
        
        Args:
            message: The input message
            session_id: Session identifier for conversation context
            context: Additional context information
            stream: Whether to return streaming response
            
        Returns:
            AgentResponse with the agent's reply
        """
        if not self.is_initialized:
            raise RuntimeError(f"Agent {self.id} is not initialized")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Add user message to conversation history
            user_msg = AgentMessage(content=message, role="user")
            self._add_to_conversation(session_id, user_msg)
            
            # Process the message
            if stream and self.supports_streaming:
                response_content = ""
                async for chunk in self.process_message_stream(message, session_id, context):
                    response_content += chunk
                response = AgentResponse(content=response_content)
            else:
                response = await self._process_message(message, session_id, context or {})
            
            # Add assistant response to conversation history
            assistant_msg = AgentMessage(content=response.content, role="assistant")
            self._add_to_conversation(session_id, assistant_msg)
            
            # Update performance tracking
            processing_time = asyncio.get_event_loop().time() - start_time
            self.interaction_count += 1
            self.total_processing_time += processing_time
            
            # Add performance metadata
            response.metadata.update({
                "processing_time": round(processing_time, 3),
                "agent_id": self.id,
                "session_id": session_id,
                "tools_used": [tool.name for tool in self.tools] if self.supports_tools else [],
                "llm_type": type(self.llm).__name__ if self.llm else "None",
                "memory_type": type(self.memory).__name__ if self.memory else "None"
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message in agent {self.id}: {str(e)}")
            raise
    
    @abstractmethod
    async def _process_message(
        self,
        message: str,
        session_id: str,
        context: Dict[str, Any]
    ) -> AgentResponse:
        """Process message logic (to be implemented by subclasses)"""
        pass
    
    async def process_message_stream(
        self,
        message: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process message with streaming response
        
        Default implementation - can be overridden by subclasses that support streaming
        """
        if not self.supports_streaming:
            raise NotImplementedError(f"Agent {self.id} does not support streaming")
        
        # Default implementation just yields the full response
        response = await self._process_message(message, session_id, context or {})
        yield response.content
    
    async def process_multimodal_message(
        self,
        message: str,
        files: List[Dict[str, Any]],
        session_id: str
    ) -> AgentResponse:
        """
        Process multimodal input (text + files)
        
        Args:
            message: Text message
            files: List of file data dictionaries
            session_id: Session identifier
            
        Returns:
            AgentResponse
        """
        if not self.supports_multimodal:
            raise NotImplementedError(f"Agent {self.id} does not support multimodal input")
        
        return await self._process_multimodal_message(message, files, session_id)
    
    async def _process_multimodal_message(
        self,
        message: str,
        files: List[Dict[str, Any]],
        session_id: str
    ) -> AgentResponse:
        """Multimodal processing logic (to be implemented by subclasses)"""
        raise NotImplementedError("Multimodal processing not implemented")
    
    def _add_to_conversation(self, session_id: str, message: AgentMessage):
        """Add a message to the conversation history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append(message)
        
        # Trim conversation if it exceeds max size
        if len(self.conversations[session_id]) > self.max_memory_size:
            # Keep the most recent messages
            self.conversations[session_id] = self.conversations[session_id][-self.max_memory_size:]
    
    def get_conversation_history(self, session_id: str) -> List[AgentMessage]:
        """Get conversation history for a session"""
        return self.conversations.get(session_id, [])
    
    def clear_conversation_history(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get agent performance statistics"""
        avg_processing_time = (
            self.total_processing_time / self.interaction_count
            if self.interaction_count > 0 else 0
        )
        
        return {
            "interaction_count": self.interaction_count,
            "total_processing_time": round(self.total_processing_time, 3),
            "average_processing_time": round(avg_processing_time, 3),
            "active_sessions": len(self.conversations),
            "total_messages": sum(len(conv) for conv in self.conversations.values())
        }
    
    async def cleanup(self):
        """Cleanup agent resources"""
        logger.info(f"Cleaning up agent: {self.id}")
        
        # Clear conversation history
        self.conversations.clear()
        
        # Perform agent-specific cleanup
        await self._cleanup_agent()
        
        self.is_initialized = False
        logger.info(f"Agent cleanup complete: {self.id}")
    
    async def _cleanup_agent(self):
        """Agent-specific cleanup logic (to be implemented by subclasses)"""
        pass
    
    # LangChain Integration Methods
    
    def add_tool(self, tool: BaseTool):
        """Add a tool to this agent's available tools"""
        self.tools.append(tool)
        self.supports_tools = True
        logger.info(f"Added tool '{tool.name}' to agent {self.id}")
    
    def remove_tool(self, tool_name: str):
        """Remove a tool by name"""
        self.tools = [tool for tool in self.tools if tool.name != tool_name]
        self.supports_tools = len(self.tools) > 0
        logger.info(f"Removed tool '{tool_name}' from agent {self.id}")
    
    def get_tool_by_name(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None
    
    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a tool by name with given input"""
        tool = self.get_tool_by_name(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in agent {self.id}")
        
        try:
            # Execute tool asynchronously if possible, otherwise sync
            if hasattr(tool, 'arun'):
                result = await tool.arun(tool_input)
            else:
                result = tool.run(tool_input)
            
            logger.info(f"Tool '{tool_name}' executed successfully in agent {self.id}")
            return result
        except Exception as e:
            logger.error(f"Tool '{tool_name}' failed in agent {self.id}: {str(e)}")
            raise
    
    def set_llm(self, llm: BaseLanguageModel):
        """Set or update the language model for this agent"""
        self.llm = llm
        logger.info(f"Updated LLM for agent {self.id}")
    
    def set_memory(self, memory: BaseMemory):
        """Set or update the memory for this agent"""
        self.memory = memory
        logger.info(f"Updated memory for agent {self.id}")
    
    def set_prompt_template(self, prompt_template: BasePromptTemplate):
        """Set or update the prompt template for this agent"""
        self.prompt_template = prompt_template
        logger.info(f"Updated prompt template for agent {self.id}")
    
    def add_callback(self, callback: BaseCallbackHandler):
        """Add a callback handler"""
        self.callbacks.append(callback)
        logger.info(f"Added callback handler to agent {self.id}")
    
    def messages_to_langchain(self, messages: List[AgentMessage]) -> List[BaseMessage]:
        """Convert internal messages to LangChain message format"""
        langchain_messages = []
        for msg in messages:
            if msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
            elif msg.role == "system":
                langchain_messages.append(SystemMessage(content=msg.content))
            else:
                # Default to human message for unknown roles
                langchain_messages.append(HumanMessage(content=msg.content))
        return langchain_messages
    
    def langchain_to_messages(self, messages: List[BaseMessage]) -> List[AgentMessage]:
        """Convert LangChain messages to internal message format"""
        agent_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, SystemMessage):
                role = "system"
            else:
                role = "assistant"  # Default fallback
            
            agent_messages.append(AgentMessage(
                content=msg.content,
                role=role,
                metadata=getattr(msg, 'additional_kwargs', {})
            ))
        return agent_messages
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"