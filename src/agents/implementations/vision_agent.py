"""
Vision Agent - Specialized agent for image analysis and multimodal tasks
"""
import base64
from typing import Dict, List, Optional, Any

from loguru import logger

from src.agents.base.agent import BaseAgent, AgentResponse
from src.services.model_manager import ModelManager


class VisionAgent(BaseAgent):
    """
    Specialized agent for vision and multimodal tasks
    
    This agent can analyze images, understand visual content, and provide
    detailed descriptions, answer questions about images, and perform
    various computer vision tasks.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="vision_agent",
            name="Vision Analyzer",
            description="Specialized in analyzing images, understanding visual content, and providing detailed descriptions and insights",
            agent_type="vision",
            capabilities=[
                "image_analysis",
                "visual_description",
                "object_detection",
                "scene_understanding",
                "text_extraction_from_images",
                "visual_question_answering",
                "image_comparison"
            ]
        )
        
        # Set agent metadata
        self.model_provider = "openai"
        self.model_name = "gpt-4-vision-preview"
        self.model_manager = None
        self.supports_multimodal = True
        self.supports_streaming = False  # Vision models typically don't stream
        
        # Vision-specific configurations
        self.max_image_size = 10 * 1024 * 1024  # 10MB
        self.supported_formats = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
    
    async def _initialize_agent(self):
        """Initialize the vision agent"""
        self.model_manager = ModelManager()
        logger.info(f"Vision agent initialized with {self.model_provider}/{self.model_name}")
    
    async def _process_message(
        self,
        message: str,
        session_id: str,
        context: Dict[str, Any]
    ) -> AgentResponse:
        """Process text-only message (no image)"""
        try:
            # For text-only messages, provide information about capabilities
            if any(keyword in message.lower() for keyword in ['image', 'picture', 'photo', 'visual']):
                response_text = """I'm a vision analysis agent specialized in understanding and analyzing images. I can help you with:

• **Image Description**: Provide detailed descriptions of images including objects, people, scenes, colors, and composition
• **Visual Question Answering**: Answer specific questions about image content
• **Text Extraction**: Read and extract text from images (OCR)
• **Object Detection**: Identify and locate objects within images
• **Scene Analysis**: Understand contexts, settings, and activities in images
• **Image Comparison**: Compare multiple images and highlight differences or similarities

To analyze an image, please use the multimodal endpoint and upload your image file along with your question or request.

What specific visual analysis task can I help you with?"""
            else:
                response_text = f"I received your message: '{message}'. However, I'm specifically designed for image analysis tasks. Please upload an image along with your question for me to analyze it effectively."
            
            return AgentResponse(
                content=response_text,
                metadata={
                    "message_type": "text_only",
                    "capabilities_mentioned": True
                }
            )
            
        except Exception as e:
            logger.error(f"Vision agent text processing failed: {str(e)}")
            return AgentResponse(
                content="I encountered an error processing your request. Please try again or upload an image for analysis.",
                metadata={"error": str(e)}
            )
    
    async def _process_multimodal_message(
        self,
        message: str,
        files: List[Dict[str, Any]],
        session_id: str
    ) -> AgentResponse:
        """Process message with image files"""
        try:
            # Validate files
            image_files = self._validate_and_filter_images(files)
            
            if not image_files:
                return AgentResponse(
                    content="No valid image files were provided. Please upload images in supported formats (JPG, PNG, GIF, BMP, WebP).",
                    metadata={"error": "no_valid_images"}
                )
            
            # Process the first image (can be extended for multiple images)
            image_file = image_files[0]
            
            # Analyze the image
            analysis_result = await self._analyze_image(
                image_data=image_file['content'],
                prompt=message,
                session_id=session_id
            )
            
            return AgentResponse(
                content=analysis_result,
                metadata={
                    "image_processed": True,
                    "image_filename": image_file['filename'],
                    "image_size": len(image_file['content']),
                    "content_type": image_file['content_type']
                }
            )
            
        except Exception as e:
            logger.error(f"Vision agent multimodal processing failed: {str(e)}")
            return AgentResponse(
                content="I encountered an error while analyzing the image. Please ensure the image is in a supported format and try again.",
                metadata={"error": str(e)}
            )
    
    def _validate_and_filter_images(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and filter image files"""
        valid_images = []
        
        for file in files:
            filename = file.get('filename', '').lower()
            content_type = file.get('content_type', '').lower()
            content = file.get('content')
            
            # Check file size
            if len(content) > self.max_image_size:
                logger.warning(f"Image {filename} too large: {len(content)} bytes")
                continue
            
            # Check file format by extension or content type
            is_valid_format = False
            
            if filename:
                extension = filename.split('.')[-1] if '.' in filename else ''
                if extension in self.supported_formats:
                    is_valid_format = True
            
            if content_type and 'image' in content_type:
                is_valid_format = True
            
            if is_valid_format:
                valid_images.append(file)
            else:
                logger.warning(f"Unsupported image format: {filename} ({content_type})")
        
        return valid_images
    
    async def _analyze_image(
        self, 
        image_data: bytes, 
        prompt: str,
        session_id: str
    ) -> str:
        """Analyze image using vision model"""
        try:
            # Build analysis prompt
            analysis_prompt = self._build_vision_prompt(prompt)
            
            # Use the model manager to process the image
            result = await self.model_manager.process_image(
                provider=self.model_provider,
                model_name=self.model_name,
                image_data=image_data,
                prompt=analysis_prompt,
                max_tokens=1000,
                temperature=0.4
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            raise
    
    def _build_vision_prompt(self, user_prompt: str) -> str:
        """Build an effective vision analysis prompt"""
        
        # Default analysis if no specific prompt
        if not user_prompt.strip() or user_prompt.strip().lower() in ['analyze', 'describe', 'what is this']:
            return """Please provide a comprehensive analysis of this image including:
            
1. **Main Subject**: What is the primary focus or subject of the image?
2. **Scene Description**: Describe the overall scene, setting, and environment
3. **Objects and Details**: List and describe key objects, people, or elements visible
4. **Colors and Composition**: Note dominant colors, lighting, and visual composition
5. **Context and Activity**: What's happening in the image? Any activities or interactions?
6. **Text Content**: If there's any text visible, please read and transcribe it
7. **Notable Features**: Any interesting, unusual, or significant aspects

Please be detailed and thorough in your analysis."""
        
        # Enhance user prompt with analysis guidance
        enhanced_prompt = f"""Please analyze this image with focus on the following request: {user_prompt}

In your analysis, please:
- Be specific and detailed in your observations
- Reference visual elements that support your analysis
- If describing objects or people, include their positions, appearances, and relationships
- If there's text in the image, read and include it in your response
- Provide context and interpretation where appropriate

User's specific request: {user_prompt}"""
        
        return enhanced_prompt
    
    async def _cleanup_agent(self):
        """Cleanup vision agent resources"""
        logger.info("Cleaning up vision agent resources")