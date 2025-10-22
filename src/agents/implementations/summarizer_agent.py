"""
Summarizer Agent - Specialized agent for document and text summarization
"""
from typing import Dict, List, Optional, Any

from loguru import logger

from src.agents.base.agent import BaseAgent, AgentResponse
from src.services.model_manager import ModelManager


class SummarizerAgent(BaseAgent):
    """
    Specialized agent for text summarization tasks
    
    This agent is designed to summarize various types of content including
    documents, articles, conversations, and other text-based materials.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="summarizer_agent",
            name="Document Summarizer",
            description="Specializes in summarizing documents, articles, and text content with high accuracy and conciseness",
            agent_type="text",
            capabilities=[
                "document_summarization", 
                "article_summarization",
                "conversation_summarization",
                "key_points_extraction",
                "executive_summary_generation"
            ]
        )
        
        # Set agent metadata
        self.model_provider = "openai"
        self.model_name = "gpt-4-turbo-preview"
        self.model_manager = None
        self.supports_streaming = True
        
        # Summarization-specific configurations
        self.max_summary_length = 500
        self.min_summary_length = 50
        self.summary_style = "professional"  # professional, casual, bullet_points, executive
    
    async def _initialize_agent(self):
        """Initialize the summarizer agent"""
        self.model_manager = ModelManager()
        logger.info(f"Summarizer agent initialized with {self.model_provider}/{self.model_name}")
    
    async def _process_message(
        self,
        message: str,
        session_id: str,
        context: Dict[str, Any]
    ) -> AgentResponse:
        """Process summarization request"""
        try:
            # Extract context parameters
            summary_length = context.get("summary_length", self.max_summary_length)
            summary_style = context.get("summary_style", self.summary_style)
            document_type = context.get("document_type", "general")
            
            # Build the summarization prompt
            prompt = self._build_summarization_prompt(
                message, 
                summary_length, 
                summary_style, 
                document_type
            )
            
            # Get conversation history for context
            history = self.get_conversation_history(session_id)
            messages = self._format_messages_for_model(prompt, history)
            
            # Generate summary using the model
            summary = await self.model_manager.generate_text(
                provider=self.model_provider,
                model_name=self.model_name,
                messages=messages,
                max_tokens=summary_length * 2,  # Give some buffer
                temperature=0.3  # Lower temperature for more consistent summaries
            )
            
            # Post-process the summary
            processed_summary = self._post_process_summary(summary, summary_style)
            
            metadata = {
                "summary_length": len(processed_summary.split()),
                "summary_style": summary_style,
                "document_type": document_type,
                "original_length": len(message.split()),
                "compression_ratio": len(message.split()) / len(processed_summary.split())
            }
            
            return AgentResponse(
                content=processed_summary,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            return AgentResponse(
                content="I apologize, but I encountered an error while summarizing the content. Please try again with a different text or check if the content is too long.",
                metadata={"error": str(e)}
            )
    
    def _build_summarization_prompt(
        self, 
        content: str, 
        max_length: int, 
        style: str, 
        document_type: str
    ) -> str:
        """Build an effective summarization prompt"""
        
        style_instructions = {
            "professional": "Write in a professional, formal tone suitable for business contexts.",
            "casual": "Write in a casual, conversational tone that's easy to understand.",
            "bullet_points": "Present the summary as clear, concise bullet points.",
            "executive": "Write an executive summary focusing on key decisions, outcomes, and actionable items."
        }
        
        document_instructions = {
            "academic": "Focus on methodology, findings, and conclusions.",
            "news": "Highlight the who, what, when, where, and why.",
            "technical": "Emphasize key technical details and implementation aspects.",
            "meeting": "Focus on decisions made, action items, and next steps.",
            "general": "Provide a balanced overview of the main points."
        }
        
        prompt = f"""You are an expert summarization specialist. Your task is to create a high-quality summary of the following content.

Requirements:
- Maximum length: approximately {max_length} words
- Style: {style_instructions.get(style, style_instructions['professional'])}
- Document type: {document_type} - {document_instructions.get(document_type, document_instructions['general'])}
- Focus on the most important and relevant information
- Maintain accuracy and avoid adding information not present in the original
- Ensure the summary is self-contained and understandable without the original text

Content to summarize:
{content}

Please provide your summary:"""
        
        return prompt
    
    def _format_messages_for_model(self, prompt: str, history: List) -> List[Dict[str, str]]:
        """Format messages for the model"""
        messages = [
            {
                "role": "system",
                "content": "You are a professional summarization expert. You excel at creating accurate, concise, and well-structured summaries that capture the essence of any text while maintaining clarity and readability."
            }
        ]
        
        # Add conversation history if available (last few exchanges for context)
        if history:
            recent_history = history[-4:]  # Last 2 exchanges
            for msg in recent_history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add current request
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        return messages
    
    def _post_process_summary(self, summary: str, style: str) -> str:
        """Post-process the generated summary"""
        # Remove any unwanted prefixes/suffixes
        summary = summary.strip()
        
        # Remove common AI response prefixes
        prefixes_to_remove = [
            "Here's a summary:",
            "Summary:",
            "Here is the summary:",
            "The summary is:",
        ]
        
        for prefix in prefixes_to_remove:
            if summary.startswith(prefix):
                summary = summary[len(prefix):].strip()
        
        # Ensure proper formatting for bullet points
        if style == "bullet_points" and not summary.startswith("•") and not summary.startswith("-"):
            # Convert to bullet points if not already formatted
            sentences = summary.split(". ")
            if len(sentences) > 1:
                summary = "\n".join([f"• {sentence.strip()}" for sentence in sentences if sentence.strip()])
        
        return summary
    
    async def _cleanup_agent(self):
        """Cleanup summarizer-specific resources"""
        logger.info("Cleaning up summarizer agent resources")
        # Add any specific cleanup logic here