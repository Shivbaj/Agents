"""
Model-related API endpoints
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from loguru import logger

from src.api.v1.schemas import (
    ModelListResponse,
    ModelInfo,
    ModelTestRequest,
    ModelTestResponse,
)
from src.services.model_manager import ModelManager

router = APIRouter()


def get_model_manager(request: Request) -> ModelManager:
    """Get model manager from app state"""
    # For now, create a new instance - in production this should be injected
    return ModelManager()


@router.get("/list", response_model=ModelListResponse)
async def list_models(
    provider: Optional[str] = None,
    model_type: Optional[str] = None,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    List all available models
    
    Optionally filter by provider or model type.
    
    Example usage:
    ```bash
    curl -X GET "http://localhost:8000/api/v1/models/list"
    curl -X GET "http://localhost:8000/api/v1/models/list?provider=openai&model_type=text"
    ```
    """
    try:
        models = await model_manager.list_models(provider=provider, model_type=model_type)
        return ModelListResponse(
            models=models,
            total=len(models)
        )
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list models")


@router.get("/{provider}/{model_name}", response_model=ModelInfo)
async def get_model_info(
    provider: str,
    model_name: str,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Get detailed information about a specific model
    
    Example usage:
    ```bash
    curl -X GET "http://localhost:8000/api/v1/models/openai/gpt-4-turbo-preview"
    ```
    """
    try:
        model_info = await model_manager.get_model_info(provider, model_name)
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return model_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get model info")


@router.post("/test", response_model=ModelTestResponse)
async def test_model(
    request: ModelTestRequest,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Test a specific model with a message
    
    Useful for checking if a model is working correctly and measuring latency.
    
    Example usage:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/models/test" \
      -H "Content-Type: application/json" \
      -d '{
        "provider": "openai",
        "model_name": "gpt-3.5-turbo",
        "test_message": "Hello, how are you?"
      }'
    ```
    """
    try:
        result = await model_manager.test_model(
            provider=request.provider,
            model_name=request.model_name,
            test_message=request.test_message
        )
        return result
    except Exception as e:
        logger.error(f"Model test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model test failed: {str(e)}")


@router.post("/{provider}/{model_name}/load")
async def load_model(
    provider: str,
    model_name: str,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Load a specific model (for local models like Ollama)
    
    Example usage:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/models/ollama/llama3.2:1b/load"
    ```
    """
    try:
        success = await model_manager.load_model(provider, model_name)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to load model")
        
        return {"message": f"Model '{provider}/{model_name}' loaded successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load model")


@router.delete("/{provider}/{model_name}/unload")
async def unload_model(
    provider: str,
    model_name: str,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Unload a specific model (for local models like Ollama)
    
    Example usage:
    ```bash
    curl -X DELETE "http://localhost:8000/api/v1/models/ollama/llama3.2:1b/unload"
    ```
    """
    try:
        success = await model_manager.unload_model(provider, model_name)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to unload model")
        
        return {"message": f"Model '{provider}/{model_name}' unloaded successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unload model: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to unload model")


@router.get("/providers")
async def list_providers(
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    List all available model providers
    
    Example usage:
    ```bash
    curl -X GET "http://localhost:8000/api/v1/models/providers"
    ```
    """
    try:
        providers = await model_manager.list_providers()
        return {
            "providers": providers,
            "total": len(providers)
        }
    except Exception as e:
        logger.error(f"Failed to list providers: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list providers")