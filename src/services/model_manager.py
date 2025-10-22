"""
Model Manager Service - Manages LLM model providers and interactions
"""
import asyncio
import time
from typing import Dict, List, Optional, Any

from loguru import logger

from src.config.settings import get_settings
from src.models.providers.openai_provider import OpenAIProvider
from src.models.providers.anthropic_provider import AnthropicProvider
from src.models.providers.ollama_provider import OllamaProvider
from src.api.v1.schemas import ModelInfo, ModelTestResponse


class ModelManager:
    """
    Manages all model providers and their configurations
    
    Provides a unified interface for interacting with different LLM providers
    and handles model lifecycle, testing, and capabilities.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.providers: Dict[str, Any] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available model providers"""
        try:
            # Initialize OpenAI provider
            if self.settings.openai_api_key:
                self.providers["openai"] = OpenAIProvider(
                    api_key=self.settings.openai_api_key,
                    base_url=self.settings.openai_base_url
                )
            
            # Initialize Anthropic provider
            if self.settings.anthropic_api_key:
                self.providers["anthropic"] = AnthropicProvider(
                    api_key=self.settings.anthropic_api_key
                )
            
            # Initialize Ollama provider
            self.providers["ollama"] = OllamaProvider(
                base_url=self.settings.ollama_base_url,
                timeout=self.settings.ollama_timeout
            )
            
            logger.info(f"Initialized {len(self.providers)} model providers")
            
        except Exception as e:
            logger.error(f"Failed to initialize model providers: {str(e)}")
    
    async def list_models(
        self, 
        provider: Optional[str] = None, 
        model_type: Optional[str] = None
    ) -> List[ModelInfo]:
        """List all available models, optionally filtered by provider or type"""
        models = []
        
        providers_to_check = [provider] if provider else list(self.providers.keys())
        
        for provider_name in providers_to_check:
            if provider_name not in self.providers:
                continue
                
            try:
                provider_instance = self.providers[provider_name]
                provider_models = await provider_instance.list_models()
                
                # Filter by model type if specified
                if model_type:
                    provider_models = [
                        model for model in provider_models 
                        if model.model_type == model_type
                    ]
                
                models.extend(provider_models)
                
            except Exception as e:
                logger.error(f"Failed to list models for provider {provider_name}: {str(e)}")
        
        return models
    
    async def get_model_info(self, provider: str, model_name: str) -> Optional[ModelInfo]:
        """Get detailed information about a specific model"""
        if provider not in self.providers:
            return None
        
        try:
            provider_instance = self.providers[provider]
            return await provider_instance.get_model_info(model_name)
        except Exception as e:
            logger.error(f"Failed to get model info for {provider}/{model_name}: {str(e)}")
            return None
    
    async def test_model(
        self, 
        provider: str, 
        model_name: str, 
        test_message: str = "Hello, world!"
    ) -> ModelTestResponse:
        """Test a specific model with a test message"""
        start_time = time.time()
        
        try:
            if provider not in self.providers:
                return ModelTestResponse(
                    provider=provider,
                    model_name=model_name,
                    status="failed",
                    error=f"Provider '{provider}' not available",
                    latency=0.0
                )
            
            provider_instance = self.providers[provider]
            response = await provider_instance.generate_text(
                model_name=model_name,
                messages=[{"role": "user", "content": test_message}],
                max_tokens=50
            )
            
            latency = time.time() - start_time
            
            return ModelTestResponse(
                provider=provider,
                model_name=model_name,
                status="success",
                response=response,
                latency=round(latency, 3)
            )
            
        except Exception as e:
            latency = time.time() - start_time
            logger.error(f"Model test failed for {provider}/{model_name}: {str(e)}")
            
            return ModelTestResponse(
                provider=provider,
                model_name=model_name,
                status="failed",
                error=str(e),
                latency=round(latency, 3)
            )
    
    async def load_model(self, provider: str, model_name: str) -> bool:
        """Load a model (primarily for local providers like Ollama)"""
        if provider not in self.providers:
            return False
        
        try:
            provider_instance = self.providers[provider]
            if hasattr(provider_instance, 'load_model'):
                return await provider_instance.load_model(model_name)
            else:
                logger.warning(f"Provider '{provider}' does not support model loading")
                return True  # Consider it successful for cloud providers
        except Exception as e:
            logger.error(f"Failed to load model {provider}/{model_name}: {str(e)}")
            return False
    
    async def unload_model(self, provider: str, model_name: str) -> bool:
        """Unload a model (primarily for local providers like Ollama)"""
        if provider not in self.providers:
            return False
        
        try:
            provider_instance = self.providers[provider]
            if hasattr(provider_instance, 'unload_model'):
                return await provider_instance.unload_model(model_name)
            else:
                logger.warning(f"Provider '{provider}' does not support model unloading")
                return True  # Consider it successful for cloud providers
        except Exception as e:
            logger.error(f"Failed to unload model {provider}/{model_name}: {str(e)}")
            return False
    
    async def list_providers(self) -> List[str]:
        """List all available providers"""
        return list(self.providers.keys())
    
    def get_provider(self, provider_name: str):
        """Get a provider instance by name"""
        return self.providers.get(provider_name)
    
    async def generate_text(
        self,
        provider: str,
        model_name: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Generate text using a specific model"""
        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not available")
        
        provider_instance = self.providers[provider]
        return await provider_instance.generate_text(
            model_name=model_name,
            messages=messages,
            **kwargs
        )
    
    async def generate_text_stream(
        self,
        provider: str,
        model_name: str,
        messages: List[Dict[str, str]],
        **kwargs
    ):
        """Generate streaming text using a specific model"""
        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not available")
        
        provider_instance = self.providers[provider]
        if not hasattr(provider_instance, 'generate_text_stream'):
            raise ValueError(f"Provider '{provider}' does not support streaming")
        
        async for chunk in provider_instance.generate_text_stream(
            model_name=model_name,
            messages=messages,
            **kwargs
        ):
            yield chunk
    
    async def process_image(
        self,
        provider: str,
        model_name: str,
        image_data: bytes,
        prompt: str,
        **kwargs
    ) -> str:
        """Process image with text using a vision model"""
        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not available")
        
        provider_instance = self.providers[provider]
        if not hasattr(provider_instance, 'process_image'):
            raise ValueError(f"Provider '{provider}' does not support image processing")
        
        return await provider_instance.process_image(
            model_name=model_name,
            image_data=image_data,
            prompt=prompt,
            **kwargs
        )
    
    async def transcribe_audio(
        self,
        provider: str,
        model_name: str,
        audio_data: bytes,
        **kwargs
    ) -> str:
        """Transcribe audio using a speech-to-text model"""
        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not available")
        
        provider_instance = self.providers[provider]
        if not hasattr(provider_instance, 'transcribe_audio'):
            raise ValueError(f"Provider '{provider}' does not support audio transcription")
        
        return await provider_instance.transcribe_audio(
            model_name=model_name,
            audio_data=audio_data,
            **kwargs
        )