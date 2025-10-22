"""
LangChain Prompt Template Management System

This module provides a comprehensive prompt template management system that
integrates with LangChain's prompt templates while adding additional features
like template versioning, validation, and dynamic loading.

Key Features:
- Template registry and management
- Variable validation and type checking  
- Template versioning and rollback
- Dynamic template loading from files
- Template composition and inheritance
- Multi-language support
- Template performance tracking

Example Usage:
    ```python
    from src.prompts.manager import PromptManager
    from src.prompts.templates import create_agent_prompt
    
    # Create prompt manager
    manager = PromptManager()
    
    # Register a template
    template = create_agent_prompt(
        system_message="You are a helpful assistant",
        task_description="Answer questions accurately"
    )
    manager.register_template("assistant_v1", template)
    
    # Use template
    prompt = await manager.get_prompt("assistant_v1", {
        "user_input": "What is Python?",
        "context": "Programming languages"
    })
    ```
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from abc import ABC, abstractmethod

from langchain_core.prompts import (
    PromptTemplate, 
    ChatPromptTemplate, 
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,
    MessagesPlaceholder
)
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field, validator


class PromptVariable(BaseModel):
    """Definition of a prompt variable"""
    name: str
    type: str = "string"  # string, integer, float, boolean, list, dict
    required: bool = True
    default_value: Optional[Any] = None
    description: Optional[str] = None
    validation_pattern: Optional[str] = None  # regex pattern for validation
    min_length: Optional[int] = None
    max_length: Optional[int] = None


class PromptMetadata(BaseModel):
    """Metadata for prompt templates"""
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    category: str = "general"
    language: str = "en"
    variables: List[PromptVariable] = Field(default_factory=list)
    usage_count: int = 0
    success_rate: float = 1.0


class TemplateConfig(BaseModel):
    """Configuration for template management"""
    templates_dir: str = "./src/prompts/templates"
    auto_save: bool = True
    version_control: bool = True
    validation_enabled: bool = True
    cache_templates: bool = True
    max_cache_size: int = 100


class BasePromptTemplate(ABC):
    """Base class for all prompt templates"""
    
    def __init__(self, metadata: PromptMetadata):
        self.metadata = metadata
        self._template = None
        self._compiled = False
    
    @abstractmethod
    def compile(self) -> Union[PromptTemplate, ChatPromptTemplate]:
        """Compile the template into a LangChain template"""
        pass
    
    def validate_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and process variables"""
        validated = {}
        
        for var_def in self.metadata.variables:
            var_name = var_def.name
            
            if var_def.required and var_name not in variables:
                if var_def.default_value is not None:
                    validated[var_name] = var_def.default_value
                else:
                    raise ValueError(f"Required variable '{var_name}' is missing")
            
            if var_name in variables:
                value = variables[var_name]
                
                # Type validation
                if var_def.type == "string" and not isinstance(value, str):
                    value = str(value)
                elif var_def.type == "integer":
                    value = int(value)
                elif var_def.type == "float":
                    value = float(value)
                elif var_def.type == "boolean":
                    value = bool(value)
                
                # Length validation for strings
                if var_def.type == "string":
                    if var_def.min_length and len(value) < var_def.min_length:
                        raise ValueError(f"Variable '{var_name}' is too short (min: {var_def.min_length})")
                    if var_def.max_length and len(value) > var_def.max_length:
                        raise ValueError(f"Variable '{var_name}' is too long (max: {var_def.max_length})")
                
                # Pattern validation
                if var_def.validation_pattern:
                    import re
                    if not re.match(var_def.validation_pattern, str(value)):
                        raise ValueError(f"Variable '{var_name}' does not match required pattern")
                
                validated[var_name] = value
        
        return validated


class SimplePromptTemplate(BasePromptTemplate):
    """Simple text-based prompt template"""
    
    def __init__(self, metadata: PromptMetadata, template_text: str):
        super().__init__(metadata)
        self.template_text = template_text
    
    def compile(self) -> PromptTemplate:
        """Compile to LangChain PromptTemplate"""
        if not self._compiled:
            input_variables = [var.name for var in self.metadata.variables]
            self._template = PromptTemplate(
                template=self.template_text,
                input_variables=input_variables
            )
            self._compiled = True
        
        return self._template


class ChatPromptTemplateWrapper(BasePromptTemplate):
    """Chat-based prompt template with multiple messages"""
    
    def __init__(
        self,
        metadata: PromptMetadata,
        system_message: Optional[str] = None,
        messages: List[Dict[str, str]] = None
    ):
        super().__init__(metadata)
        self.system_message = system_message
        self.messages = messages or []
    
    def compile(self) -> ChatPromptTemplate:
        """Compile to LangChain ChatPromptTemplate"""
        if not self._compiled:
            template_messages = []
            
            # Add system message if provided
            if self.system_message:
                template_messages.append(
                    SystemMessagePromptTemplate.from_template(self.system_message)
                )
            
            # Add other messages
            for msg in self.messages:
                role = msg.get("role", "human")
                content = msg.get("content", "")
                
                if role == "system":
                    template_messages.append(
                        SystemMessagePromptTemplate.from_template(content)
                    )
                elif role == "human":
                    template_messages.append(
                        HumanMessagePromptTemplate.from_template(content)
                    )
                elif role == "assistant":
                    template_messages.append(
                        AIMessagePromptTemplate.from_template(content)
                    )
                elif role == "placeholder":
                    template_messages.append(
                        MessagesPlaceholder(variable_name=content)
                    )
            
            self._template = ChatPromptTemplate.from_messages(template_messages)
            self._compiled = True
        
        return self._template


class PromptManager:
    """
    Centralized manager for prompt templates
    """
    
    def __init__(self, config: Optional[TemplateConfig] = None):
        self.config = config or TemplateConfig()
        self.templates: Dict[str, BasePromptTemplate] = {}
        self.template_cache: Dict[str, Union[PromptTemplate, ChatPromptTemplate]] = {}
        self.template_files: Dict[str, Path] = {}
        
        # Ensure templates directory exists
        os.makedirs(self.config.templates_dir, exist_ok=True)
        
        # Load existing templates
        self._load_templates_from_files()
    
    def register_template(
        self,
        template_id: str,
        template: BasePromptTemplate,
        save_to_file: bool = None
    ):
        """Register a new template"""
        if save_to_file is None:
            save_to_file = self.config.auto_save
        
        # Update metadata
        template.metadata.id = template_id
        template.metadata.updated_at = datetime.now()
        
        # Store template
        self.templates[template_id] = template
        
        # Clear cache
        if template_id in self.template_cache:
            del self.template_cache[template_id]
        
        # Save to file if requested
        if save_to_file:
            self._save_template_to_file(template_id, template)
    
    async def get_prompt(
        self,
        template_id: str,
        variables: Dict[str, Any] = None,
        validate: bool = None
    ) -> Union[str, List[BaseMessage]]:
        """Get a formatted prompt"""
        if validate is None:
            validate = self.config.validation_enabled
        
        variables = variables or {}
        
        # Get template
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template '{template_id}' not found")
        
        # Validate variables
        if validate:
            variables = template.validate_variables(variables)
        
        # Get compiled template from cache or compile
        if self.config.cache_templates and template_id in self.template_cache:
            compiled_template = self.template_cache[template_id]
        else:
            compiled_template = template.compile()
            
            if self.config.cache_templates:
                self.template_cache[template_id] = compiled_template
                
                # Manage cache size
                if len(self.template_cache) > self.config.max_cache_size:
                    # Remove oldest entry (simple FIFO)
                    oldest_key = next(iter(self.template_cache))
                    del self.template_cache[oldest_key]
        
        # Format prompt
        if isinstance(compiled_template, PromptTemplate):
            result = compiled_template.format(**variables)
        else:  # ChatPromptTemplate
            result = compiled_template.format_messages(**variables)
        
        # Update usage statistics
        template.metadata.usage_count += 1
        
        return result
    
    def get_template(self, template_id: str) -> Optional[BasePromptTemplate]:
        """Get a template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[PromptMetadata]:
        """List available templates with optional filtering"""
        templates = []
        
        for template in self.templates.values():
            # Filter by category
            if category and template.metadata.category != category:
                continue
            
            # Filter by tags
            if tags and not any(tag in template.metadata.tags for tag in tags):
                continue
            
            templates.append(template.metadata)
        
        return templates
    
    def delete_template(self, template_id: str, delete_file: bool = True):
        """Delete a template"""
        if template_id not in self.templates:
            raise ValueError(f"Template '{template_id}' not found")
        
        # Remove from memory
        del self.templates[template_id]
        
        # Remove from cache
        if template_id in self.template_cache:
            del self.template_cache[template_id]
        
        # Delete file
        if delete_file and template_id in self.template_files:
            file_path = self.template_files[template_id]
            if file_path.exists():
                file_path.unlink()
            del self.template_files[template_id]
    
    def create_version(self, template_id: str, new_version: str) -> str:
        """Create a new version of an existing template"""
        if not self.config.version_control:
            raise ValueError("Version control is disabled")
        
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template '{template_id}' not found")
        
        # Create new versioned ID
        new_id = f"{template_id}_v{new_version}"
        
        # Create copy with new metadata
        new_metadata = template.metadata.copy()
        new_metadata.id = new_id
        new_metadata.version = new_version
        new_metadata.created_at = datetime.now()
        new_metadata.updated_at = datetime.now()
        
        # Create new template instance (this is a simplified approach)
        if isinstance(template, SimplePromptTemplate):
            new_template = SimplePromptTemplate(new_metadata, template.template_text)
        elif isinstance(template, ChatPromptTemplateWrapper):
            new_template = ChatPromptTemplateWrapper(
                new_metadata,
                template.system_message,
                template.messages.copy()
            )
        else:
            raise ValueError(f"Cannot version template of type {type(template)}")
        
        # Register new version
        self.register_template(new_id, new_template)
        
        return new_id
    
    def _load_templates_from_files(self):
        """Load templates from JSON files"""
        templates_dir = Path(self.config.templates_dir)
        if not templates_dir.exists():
            return
        
        for file_path in templates_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                template = self._create_template_from_data(data)
                if template:
                    self.templates[template.metadata.id] = template
                    self.template_files[template.metadata.id] = file_path
                    
            except Exception as e:
                print(f"Error loading template from {file_path}: {e}")
    
    def _create_template_from_data(self, data: Dict[str, Any]) -> Optional[BasePromptTemplate]:
        """Create template instance from JSON data"""
        try:
            # Create metadata
            metadata_data = data["metadata"]
            metadata_data["variables"] = [
                PromptVariable(**var) for var in metadata_data.get("variables", [])
            ]
            metadata = PromptMetadata(**metadata_data)
            
            # Create appropriate template type
            template_type = data.get("type", "simple")
            
            if template_type == "simple":
                return SimplePromptTemplate(
                    metadata=metadata,
                    template_text=data["template_text"]
                )
            elif template_type == "chat":
                return ChatPromptTemplateWrapper(
                    metadata=metadata,
                    system_message=data.get("system_message"),
                    messages=data.get("messages", [])
                )
            
        except Exception as e:
            print(f"Error creating template from data: {e}")
            return None
    
    def _save_template_to_file(self, template_id: str, template: BasePromptTemplate):
        """Save template to JSON file"""
        file_path = Path(self.config.templates_dir) / f"{template_id}.json"
        
        # Prepare data for saving
        data = {
            "type": "simple" if isinstance(template, SimplePromptTemplate) else "chat",
            "metadata": {
                "id": template.metadata.id,
                "name": template.metadata.name,
                "description": template.metadata.description,
                "version": template.metadata.version,
                "author": template.metadata.author,
                "created_at": template.metadata.created_at.isoformat(),
                "updated_at": template.metadata.updated_at.isoformat(),
                "tags": template.metadata.tags,
                "category": template.metadata.category,
                "language": template.metadata.language,
                "variables": [var.dict() for var in template.metadata.variables],
                "usage_count": template.metadata.usage_count,
                "success_rate": template.metadata.success_rate
            }
        }
        
        if isinstance(template, SimplePromptTemplate):
            data["template_text"] = template.template_text
        elif isinstance(template, ChatPromptTemplateWrapper):
            data["system_message"] = template.system_message
            data["messages"] = template.messages
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.template_files[template_id] = file_path


# Factory functions for creating common prompt templates
def create_agent_prompt(
    agent_name: str = "Assistant",
    system_message: str = None,
    task_description: str = None,
    personality_traits: List[str] = None,
    constraints: List[str] = None
) -> ChatPromptTemplateWrapper:
    """Create a standard agent prompt template"""
    
    system_parts = []
    
    if system_message:
        system_parts.append(system_message)
    else:
        system_parts.append(f"You are {agent_name}, a helpful AI assistant.")
    
    if task_description:
        system_parts.append(f"Your primary task is: {task_description}")
    
    if personality_traits:
        traits_text = ", ".join(personality_traits)
        system_parts.append(f"Your personality traits: {traits_text}")
    
    if constraints:
        constraints_text = "\n".join(f"- {constraint}" for constraint in constraints)
        system_parts.append(f"Important constraints:\n{constraints_text}")
    
    full_system_message = "\n\n".join(system_parts)
    
    messages = [
        {"role": "human", "content": "{user_input}"}
    ]
    
    # Add context placeholder if needed
    if "{context}" in full_system_message:
        messages.insert(0, {"role": "placeholder", "content": "context_messages"})
    
    metadata = PromptMetadata(
        id=f"{agent_name.lower()}_prompt",
        name=f"{agent_name} Prompt",
        description=f"Standard prompt for {agent_name} agent",
        category="agent",
        variables=[
            PromptVariable(name="user_input", description="User's input message"),
        ]
    )
    
    if "{context}" in full_system_message:
        metadata.variables.append(
            PromptVariable(name="context_messages", description="Context messages", required=False)
        )
    
    return ChatPromptTemplateWrapper(
        metadata=metadata,
        system_message=full_system_message,
        messages=messages
    )


def create_task_prompt(
    task_type: str,
    instructions: str,
    input_format: str = None,
    output_format: str = None,
    examples: List[Dict[str, str]] = None
) -> SimplePromptTemplate:
    """Create a task-specific prompt template"""
    
    template_parts = []
    
    template_parts.append(f"Task: {task_type}")
    template_parts.append(f"Instructions: {instructions}")
    
    if input_format:
        template_parts.append(f"Input format: {input_format}")
    
    if output_format:
        template_parts.append(f"Output format: {output_format}")
    
    if examples:
        template_parts.append("Examples:")
        for i, example in enumerate(examples, 1):
            template_parts.append(f"Example {i}:")
            template_parts.append(f"Input: {example.get('input', '')}")
            template_parts.append(f"Output: {example.get('output', '')}")
    
    template_parts.append("Now, please complete the following:")
    template_parts.append("Input: {input}")
    template_parts.append("Output:")
    
    template_text = "\n\n".join(template_parts)
    
    metadata = PromptMetadata(
        id=f"{task_type.lower()}_task",
        name=f"{task_type} Task Prompt",
        description=f"Prompt for {task_type} tasks",
        category="task",
        variables=[
            PromptVariable(name="input", description="Task input")
        ]
    )
    
    return SimplePromptTemplate(metadata, template_text)