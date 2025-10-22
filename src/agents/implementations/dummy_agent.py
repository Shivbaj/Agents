"""
Dummy Agent - A simple test agent for demonstration and testing purposes
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import random
import asyncio
import logging

from src.agents.base.agent import BaseAgent, AgentResponse

logger = logging.getLogger(__name__)


class DummyAgent(BaseAgent):
    """
    A simple dummy agent for testing and demonstration
    
    This agent provides basic functionality for testing the agent system
    without requiring complex model integrations or external services.
    """
    
    def __init__(self, agent_id: str = "dummy_agent", capabilities=None, **kwargs):
        default_capabilities = [
            "echo", 
            "random_facts", 
            "math_calculations",
            "greeting",
            "system_info"
        ]
        
        super().__init__(
            agent_id=agent_id,
            name="Dummy Test Agent",
            description="A simple test agent for demonstration and system testing",
            agent_type="dummy",
            capabilities=capabilities or default_capabilities,
            **kwargs
        )
        
        # Set agent metadata
        self.model_provider = "built-in"
        self.model_name = "dummy_v1.0"
        
        # Dummy agent specific configuration
        self.personality = "friendly"
        self.response_templates = {
            "greeting": [
                "Hello! I'm a dummy agent. How can I help you test the system?",
                "Hi there! I'm here for testing purposes. What would you like me to do?",
                "Welcome! I'm a simple test agent ready to assist with system validation."
            ],
            "farewell": [
                "Goodbye! Thanks for testing with me!",
                "See you later! Hope the testing went well!",
                "Farewell! I'm always here for more testing!"
            ],
            "random_facts": [
                "Did you know? Octopuses have three hearts!",
                "Fun fact: Honey never spoils - it can last thousands of years!",
                "Interesting: A group of flamingos is called a 'flamboyance'!",
                "Cool fact: Bananas are berries, but strawberries aren't!",
                "Amazing: There are more possible games of chess than atoms in the observable universe!"
            ]
        }
        
    async def _initialize_agent(self):
        """Initialize the dummy agent"""
        logger.info(f"Initializing {self.name}")
        
        # Simulate initialization work
        await asyncio.sleep(0.1)
        
        # Set some dummy stats
        self.interaction_count = 0
        self.total_processing_time = 0.0
        self.initialized_at = datetime.now()
        
        logger.info(f"✓ {self.name} initialized successfully")
    
    async def _process_message(self, message: str, session_id: str, context: Dict[str, Any]) -> AgentResponse:
        """Process message with dummy agent logic"""
        logger.info(f"Dummy agent processing: {message}")
        
        # Increment interaction counter
        self.interaction_count += 1
        start_time = datetime.now()
        
        # Simple message processing logic
        message_lower = message.lower().strip()
        
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "greetings"]):
            response_content = random.choice(self.response_templates["greeting"])
            
        elif any(farewell in message_lower for farewell in ["bye", "goodbye", "see you", "farewell"]):
            response_content = random.choice(self.response_templates["farewell"])
            
        elif "fact" in message_lower or "random" in message_lower:
            response_content = random.choice(self.response_templates["random_facts"])
            
        elif "echo" in message_lower:
            # Extract text to echo (everything after "echo")
            echo_text = message[message_lower.find("echo") + 4:].strip()
            response_content = f"Echo: {echo_text}" if echo_text else "Echo: (no text provided)"
            
        elif any(math_word in message_lower for math_word in ["calculate", "math", "+", "-", "*", "/"]):
            response_content = self._handle_math(message)
            
        elif "status" in message_lower or "info" in message_lower:
            response_content = self._get_system_info()
            
        elif "help" in message_lower:
            response_content = self._get_help_message()
            
        else:
            # Default response for unrecognized input
            responses = [
                f"I received your message: '{message}'. As a dummy agent, I can help with greetings, facts, echo, math, status, or help commands.",
                f"Thanks for the message '{message}'! I'm a test agent. Try asking for a fact, saying hello, or asking for help!",
                f"Message received: '{message}'. I'm a dummy agent for testing. Ask me for help to see what I can do!"
            ]
            response_content = random.choice(responses)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        self.total_processing_time += processing_time
        
        # Simulate some processing delay
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        return AgentResponse(
            content=response_content,
            metadata={
                "processing_time": processing_time,
                "interaction_number": self.interaction_count,
                "agent_type": "dummy",
                "capabilities_used": self._detect_capabilities_used(message_lower),
                "timestamp": datetime.now().isoformat(),
                "model_used": "dummy-model-v1.0",
                "provider": "internal",
                "agent_id": self.id,
                "session_id": session_id
            }
        )
    
    def _handle_math(self, message: str) -> str:
        """Handle basic math operations"""
        try:
            # Simple math expression evaluation (be careful in production!)
            # Only allow basic operations for safety
            import re
            
            # Extract numbers and basic operators
            math_expression = re.sub(r'[^0-9+\-*/.() ]', '', message)
            
            if math_expression.strip():
                # Very basic evaluation - only for demo purposes
                # In production, use a proper math parser
                allowed_chars = set('0123456789+-*/.() ')
                if all(c in allowed_chars for c in math_expression):
                    try:
                        result = eval(math_expression)  # NOTE: Never use eval() in production!
                        return f"Math result: {math_expression} = {result}"
                    except:
                        return "Sorry, I couldn't calculate that. Try simple expressions like '2 + 2' or '10 * 5'."
                else:
                    return "Please use only numbers and basic operators (+, -, *, /) for math."
            else:
                return "I didn't find a math expression. Try something like 'calculate 2 + 2'."
                
        except Exception as e:
            return f"Math calculation error: {str(e)}"
    
    def _get_system_info(self) -> str:
        """Get dummy system information"""
        uptime = (datetime.now() - self.initialized_at).total_seconds()
        avg_processing_time = self.total_processing_time / max(self.interaction_count, 1)
        
        return f"""Dummy Agent System Info:
        • Agent ID: {self.id}
        • Status: Active
        • Interactions: {self.interaction_count}
        • Uptime: {uptime:.1f} seconds
        • Average processing time: {avg_processing_time:.3f} seconds
        • Capabilities: {', '.join(self.capabilities)}
        • Personality: {self.personality}
        """
    
    def _get_help_message(self) -> str:
        """Get help message with available commands"""
        return """Dummy Agent Help:
        
        I'm a test agent that can help with:
        • Greetings: Say 'hello', 'hi', or 'hey'
        • Random facts: Ask for a 'fact' or something 'random'
        • Echo: Say 'echo [your text]' to repeat text
        • Math: Ask me to 'calculate 2 + 2' or use basic math
        • Status: Ask for 'status' or 'info' to see my stats
        • Help: Ask for 'help' to see this message
        • Farewell: Say 'bye' or 'goodbye'
        
        I'm here for testing and demonstration purposes!
        """
    
    def _detect_capabilities_used(self, message: str) -> List[str]:
        """Detect which capabilities were used in processing"""
        used_capabilities = []
        
        if any(word in message for word in ["hello", "hi", "hey", "bye", "goodbye"]):
            used_capabilities.append("greeting")
        if "fact" in message or "random" in message:
            used_capabilities.append("random_facts")
        if "echo" in message:
            used_capabilities.append("echo")
        if any(word in message for word in ["calculate", "math", "+", "-", "*", "/"]):
            used_capabilities.append("math_calculations")
        if "status" in message or "info" in message or "help" in message:
            used_capabilities.append("system_info")
            
        return used_capabilities or ["general"]
    
    async def _cleanup_agent(self):
        """Cleanup dummy agent resources"""
        logger.info(f"Cleaning up {self.name}")
        logger.info(f"Final stats: {self.interaction_count} interactions, "
                        f"{self.total_processing_time:.2f}s total processing time")