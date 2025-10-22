"""
Enhanced General Assistant Agent implementation with LangChain integration
"""
from typing import Dict, List, Optional, Any
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.base.agent import BaseAgent, AgentResponse
from src.models.providers.openai_provider import OpenAIProvider
from src.prompts.manager import PromptManager
from src.memory.conversation import MemoryManager
from src.tools.base_tools import get_tool
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class GeneralAssistant(BaseAgent):
    """
    Enhanced general-purpose assistant agent with LangChain integration
    
    Features:
    - LangChain LLM integration
    - Tool usage capabilities
    - Enhanced memory management
    - Prompt template system
    - Conversation context awareness
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        use_tools: bool = True,
        use_web_search: bool = True,
        **kwargs
    ):
        # Initialize LangChain components
        settings = get_settings()
        
        # Create LLM provider
        llm = None
        if settings.openai_api_key:
            provider = OpenAIProvider(api_key=settings.openai_api_key)
            llm = provider.create_llm(
                model_name=settings.openai_default_model,
                temperature=0.7
            )
        
        # Initialize tools
        tools = []
        if use_tools:
            try:
                tools.append(get_tool("calculator"))
                if use_web_search:
                    tools.append(get_tool("web_search"))
                tools.append(get_tool("file_processor"))
            except Exception as e:
                logger.warning(f"Could not initialize some tools: {e}")
        
        # Initialize memory manager
        memory_manager = MemoryManager()
        
        super().__init__(
            agent_id=agent_id,
            name="General Assistant",
            description="An enhanced versatile assistant for general questions, tasks, and research",
            agent_type="general_assistant",
            capabilities=[
                "text_generation", 
                "question_answering", 
                "task_assistance",
                "web_search",
                "calculations",
                "file_processing"
            ],
            llm=llm,
            tools=tools,
            **kwargs
        )
        
        self.memory_manager = memory_manager
        self.prompt_manager = PromptManager()
        self.supports_streaming = True
        
        # Enhanced capabilities
        self.use_tools = use_tools
        self.use_web_search = use_web_search
    
    async def _initialize_agent(self):
        """Initialize the enhanced general assistant"""
        # Load prompt templates
        try:
            # The prompt manager will auto-load templates from files
            pass
        except Exception as e:
            logger.warning(f"Could not load prompt templates: {e}")
        
        logger.info(f"General Assistant initialized with {len(self.tools)} tools")
    
    async def _process_message(
        self,
        message: str,
        session_id: str,
        context: Dict[str, Any]
    ) -> AgentResponse:
        """Process a message using the enhanced general assistant"""
        
        try:
            # Get or create hybrid memory for this session
            memory = self.memory_manager.create_hybrid_memory(
                session_id=session_id,
                llm=self.llm
            )
            
            # Get enhanced context (conversation + relevant information)
            enhanced_context = await memory.get_enhanced_context(
                current_query=message,
                conversation_limit=10,
                context_limit=3
            )
            
            # Determine if we need to use tools
            needs_calculation = any(word in message.lower() for word in 
                                  ['calculate', 'compute', 'math', '+', '-', '*', '/', '='])
            needs_search = any(word in message.lower() for word in 
                             ['search', 'find', 'look up', 'latest', 'current', 'news'])
            
            response_content = ""
            tools_used = []
            
            # Use tools if needed and available
            if self.use_tools:
                if needs_calculation and self.get_tool_by_name("calculator"):
                    try:
                        # Extract mathematical expressions (simplified)
                        import re
                        math_expressions = re.findall(r'[\d+\-*/().]+', message)
                        if math_expressions:
                            calc_result = await self.execute_tool("calculator", {"expression": math_expressions[0]})
                            response_content += f"Calculation result: {calc_result.get('result', 'Error')}\n\n"
                            tools_used.append("calculator")
                    except Exception as e:
                        logger.warning(f"Calculator tool error: {e}")
                
                if needs_search and self.use_web_search and self.get_tool_by_name("web_search"):
                    try:
                        search_results = await self.execute_tool("web_search", {"query": message})
                        if isinstance(search_results, list) and search_results:
                            response_content += "Here's what I found online:\n"
                            for i, result in enumerate(search_results[:3], 1):
                                if "error" not in result:
                                    response_content += f"{i}. {result.get('title', 'N/A')}\n"
                                    response_content += f"   {result.get('snippet', 'No description available')}\n\n"
                            tools_used.append("web_search")
                    except Exception as e:
                        logger.warning(f"Web search tool error: {e}")
            
            # Get prompt template
            try:
                prompt_text = await self.prompt_manager.get_prompt(
                    "general_assistant",
                    {
                        "user_input": message,
                        "context": self._format_context(enhanced_context)
                    }
                )
            except Exception as e:
                # Fallback prompt if template system fails
                conversation_history = enhanced_context.get("conversation_history", [])
                context_str = self._format_conversation_history(conversation_history[-5:])
                
                prompt_text = [
                    SystemMessage(content=f"""You are a helpful, knowledgeable AI assistant. 
                    Provide accurate, informative responses. Be concise but thorough.
                    
                    {context_str}
                    
                    Tools used: {', '.join(tools_used) if tools_used else 'None'}
                    {response_content if response_content else ''}"""),
                    HumanMessage(content=message)
                ]
            
            # Generate response using LLM
            if self.llm:
                if isinstance(prompt_text, list):
                    llm_response = await self.llm.ainvoke(prompt_text)
                    ai_response = llm_response.content
                else:
                    ai_response = await self.llm.ainvoke(prompt_text)
                
                # Combine tool results with LLM response
                full_response = response_content + ai_response
            else:
                # Fallback response if no LLM is available
                full_response = response_content + f"I understand you're asking about: '{message}'. As a general assistant, I'm here to help with various tasks and questions."
            
            # Add to memory
            await memory.add_message("user", message, context)
            await memory.add_message("assistant", full_response, {
                "tools_used": tools_used,
                "session_id": session_id
            })
            
            return AgentResponse(
                content=full_response,
                metadata={
                    "tools_used": tools_used,
                    "context_sources": len(enhanced_context.get("relevant_context", [])),
                    "conversation_length": len(enhanced_context.get("conversation_history", [])),
                    "capabilities_used": ["text_generation", "question_answering"] + tools_used
                }
            )
            
        except Exception as e:
            error_response = f"I apologize, but I encountered an error processing your request: {str(e)}"
            return AgentResponse(
                content=error_response,
                metadata={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
    
    def _format_context(self, enhanced_context: Dict[str, Any]) -> str:
        """Format enhanced context for prompt"""
        context_parts = []
        
        # Add conversation history
        history = enhanced_context.get("conversation_history", [])
        if history:
            context_parts.append("Recent conversation:")
            context_parts.append(self._format_conversation_history(history[-3:]))
        
        # Add relevant context
        relevant = enhanced_context.get("relevant_context", [])
        if relevant:
            context_parts.append("Relevant information:")
            for item in relevant[:2]:  # Top 2 most relevant
                context_parts.append(f"- {item.get('content', '')[:200]}...")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _format_conversation_history(self, messages) -> str:
        """Format conversation history for context"""
        formatted = []
        for msg in messages:
            if hasattr(msg, 'content'):
                role = "User" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
                formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)
    
    async def _cleanup_agent(self):
        """Cleanup agent resources"""
        # Cleanup any resources
        for tool in self.tools:
            if hasattr(tool, 'cleanup'):
                try:
                    await tool.cleanup()
                except Exception:
                    pass