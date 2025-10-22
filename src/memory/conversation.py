"""
Conversation Memory Management for Multi-Agent System

This module provides various memory implementations for agents to maintain
context across conversations, store long-term knowledge, and retrieve
relevant information efficiently.

Key Features:
- Conversation buffer management
- Vector-based semantic search
- Persistent storage options
- Memory summarization
- Context-aware retrieval

Example Usage:
    ```python
    from src.memory.conversation import ConversationMemory
    from src.memory.vector_store import VectorMemory
    
    # Create conversation memory
    conv_memory = ConversationMemory(
        session_id="user_123",
        max_tokens=4000
    )
    
    # Add messages
    await conv_memory.add_message("user", "Hello, how are you?")
    await conv_memory.add_message("assistant", "I'm doing well, thank you!")
    
    # Get conversation history
    history = await conv_memory.get_conversation_history()
    
    # Create vector memory for semantic search
    vector_memory = VectorMemory()
    await vector_memory.add_documents([
        {"content": "Python is a programming language", "metadata": {"topic": "programming"}},
        {"content": "FastAPI is a web framework", "metadata": {"topic": "web"}}
    ])
    
    # Search for relevant information
    results = await vector_memory.search("web development", k=2)
    ```
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
from abc import ABC, abstractmethod

try:
    from langchain_community.memory import ConversationBufferWindowMemory, ConversationSummaryBufferMemory
except ImportError:
    try:
        from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryBufferMemory
    except ImportError:
        # Fallback: create dummy classes
        ConversationBufferWindowMemory = None
        ConversationSummaryBufferMemory = None
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma, FAISS
from langchain_core.documents import Document
from pydantic import BaseModel, Field

from src.config.settings import get_settings


class MemoryConfig(BaseModel):
    """Configuration for memory systems"""
    memory_type: str
    max_tokens: int = Field(default=4000, ge=100, le=100000)
    max_messages: int = Field(default=100, ge=1, le=10000)
    summarize_threshold: int = Field(default=2000, ge=100, le=50000)
    persistence_path: Optional[str] = None
    embedding_model: str = "text-embedding-ada-002"
    vector_store_type: str = "chroma"  # chroma, faiss, or none


class BaseMemory(ABC):
    """Base class for all memory implementations"""
    
    def __init__(self, session_id: str, config: MemoryConfig):
        self.session_id = session_id
        self.config = config
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
    
    @abstractmethod
    async def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to memory"""
        pass
    
    @abstractmethod
    async def get_conversation_history(self, limit: Optional[int] = None) -> List[BaseMessage]:
        """Get conversation history"""
        pass
    
    @abstractmethod
    async def clear_memory(self):
        """Clear all memory"""
        pass
    
    @abstractmethod
    async def save_to_storage(self):
        """Save memory to persistent storage"""
        pass
    
    @abstractmethod
    async def load_from_storage(self):
        """Load memory from persistent storage"""
        pass


class ConversationMemory(BaseMemory):
    """
    Conversation memory with buffering and summarization capabilities
    """
    
    def __init__(
        self,
        session_id: str,
        config: Optional[MemoryConfig] = None,
        llm = None
    ):
        config = config or MemoryConfig(memory_type="conversation")
        super().__init__(session_id, config)
        
        self.messages: List[Dict[str, Any]] = []
        self.summary: Optional[str] = None
        
        # Initialize LangChain memory
        if llm and config.summarize_threshold > 0:
            self.langchain_memory = ConversationSummaryBufferMemory(
                llm=llm,
                max_token_limit=config.summarize_threshold,
                return_messages=True
            )
        else:
            self.langchain_memory = ConversationBufferWindowMemory(
                k=config.max_messages,
                return_messages=True
            )
    
    async def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to conversation memory"""
        message_data = {
            "id": str(uuid4()),
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.messages.append(message_data)
        self.last_accessed = datetime.now()
        
        # Add to LangChain memory
        if role == "user":
            self.langchain_memory.chat_memory.add_user_message(content)
        elif role == "assistant":
            self.langchain_memory.chat_memory.add_ai_message(content)
        
        # Auto-save if configured
        if self.config.persistence_path:
            await self.save_to_storage()
    
    async def get_conversation_history(self, limit: Optional[int] = None) -> List[BaseMessage]:
        """Get conversation history as LangChain messages"""
        # Use LangChain memory for summarized/windowed history
        memory_vars = self.langchain_memory.load_memory_variables({})
        history = memory_vars.get("history", [])
        
        if limit:
            history = history[-limit:]
        
        return history
    
    async def get_raw_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get raw message data"""
        messages = self.messages
        if limit:
            messages = messages[-limit:]
        return messages
    
    async def get_summary(self) -> Optional[str]:
        """Get conversation summary if available"""
        if hasattr(self.langchain_memory, 'moving_summary_buffer'):
            return self.langchain_memory.moving_summary_buffer
        return self.summary
    
    async def clear_memory(self):
        """Clear conversation memory"""
        self.messages.clear()
        self.langchain_memory.clear()
        self.summary = None
        
        # Clear persistent storage if configured
        if self.config.persistence_path:
            await self.save_to_storage()
    
    async def save_to_storage(self):
        """Save memory to persistent storage"""
        if not self.config.persistence_path:
            return
        
        storage_data = {
            "session_id": self.session_id,
            "config": self.config.dict(),
            "messages": self.messages,
            "summary": await self.get_summary(),
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat()
        }
        
        # Save to SQLite
        conn = sqlite3.connect(self.config.persistence_path)
        try:
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_memory (
                    session_id TEXT PRIMARY KEY,
                    data TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert or update
            cursor.execute(
                "INSERT OR REPLACE INTO conversation_memory (session_id, data) VALUES (?, ?)",
                (self.session_id, json.dumps(storage_data))
            )
            
            conn.commit()
        finally:
            conn.close()
    
    async def load_from_storage(self):
        """Load memory from persistent storage"""
        if not self.config.persistence_path:
            return
        
        conn = sqlite3.connect(self.config.persistence_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data FROM conversation_memory WHERE session_id = ?",
                (self.session_id,)
            )
            
            row = cursor.fetchone()
            if row:
                storage_data = json.loads(row[0])
                
                self.messages = storage_data.get("messages", [])
                self.summary = storage_data.get("summary")
                self.created_at = datetime.fromisoformat(storage_data.get("created_at", datetime.now().isoformat()))
                
                # Rebuild LangChain memory
                for msg in self.messages:
                    role = msg["role"]
                    content = msg["content"]
                    
                    if role == "user":
                        self.langchain_memory.chat_memory.add_user_message(content)
                    elif role == "assistant":
                        self.langchain_memory.chat_memory.add_ai_message(content)
                
        finally:
            conn.close()


class VectorMemory:
    """
    Vector-based memory for semantic search and retrieval
    """
    
    def __init__(
        self,
        collection_name: str = "agent_memory",
        config: Optional[MemoryConfig] = None,
        embeddings: Optional[Embeddings] = None
    ):
        self.collection_name = collection_name
        self.config = config or MemoryConfig(memory_type="vector")
        
        # Initialize embeddings
        if embeddings:
            self.embeddings = embeddings
        else:
            settings = get_settings()
            if settings.openai_api_key:
                self.embeddings = OpenAIEmbeddings(
                    model=self.config.embedding_model,
                    openai_api_key=settings.openai_api_key
                )
            else:
                raise ValueError("No embeddings model available. Set OpenAI API key or provide embeddings.")
        
        # Initialize vector store
        self.vector_store = None
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Initialize the vector store"""
        if self.config.vector_store_type == "chroma":
            if self.config.persistence_path:
                self.vector_store = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings,
                    persist_directory=self.config.persistence_path
                )
            else:
                self.vector_store = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings
                )
        elif self.config.vector_store_type == "faiss":
            # FAISS will be created when first document is added
            self.vector_store = None
        else:
            raise ValueError(f"Unsupported vector store type: {self.config.vector_store_type}")
    
    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to vector memory"""
        if not documents:
            return
        
        # Convert to LangChain documents
        docs = []
        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            metadata["timestamp"] = datetime.now().isoformat()
            metadata["id"] = doc.get("id", str(uuid4()))
            
            docs.append(Document(page_content=content, metadata=metadata))
        
        if self.config.vector_store_type == "faiss" and self.vector_store is None:
            # Create FAISS index
            self.vector_store = FAISS.from_documents(docs, self.embeddings)
        else:
            # Add to existing store
            await self.vector_store.aadd_documents(docs)
    
    async def search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        if not self.vector_store:
            return []
        
        try:
            # Perform similarity search
            if filter_metadata:
                results = await self.vector_store.asimilarity_search(
                    query, k=k, filter=filter_metadata
                )
            else:
                results = await self.vector_store.asimilarity_search(query, k=k)
            
            # Convert to dict format
            search_results = []
            for doc in results:
                search_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "relevance_score": getattr(doc, "relevance_score", None)
                })
            
            return search_results
            
        except Exception as e:
            print(f"Vector search failed: {e}")
            return []
    
    async def search_with_scores(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search for relevant documents with similarity scores"""
        if not self.vector_store:
            return []
        
        try:
            # Perform similarity search with scores
            if filter_metadata:
                results = await self.vector_store.asimilarity_search_with_score(
                    query, k=k, filter=filter_metadata
                )
            else:
                results = await self.vector_store.asimilarity_search_with_score(query, k=k)
            
            # Convert to dict format
            search_results = []
            for doc, score in results:
                doc_dict = {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                search_results.append((doc_dict, score))
            
            return search_results
            
        except Exception as e:
            print(f"Vector search with scores failed: {e}")
            return []
    
    async def delete_documents(self, document_ids: List[str]):
        """Delete documents by ID"""
        if not self.vector_store or not hasattr(self.vector_store, "delete"):
            return
        
        try:
            self.vector_store.delete(document_ids)
        except Exception as e:
            print(f"Failed to delete documents: {e}")
    
    async def get_document_count(self) -> int:
        """Get total number of documents in vector store"""
        if not self.vector_store:
            return 0
        
        try:
            # This method varies by vector store implementation
            if hasattr(self.vector_store, "_collection"):
                return self.vector_store._collection.count()
            else:
                return 0
        except Exception:
            return 0


class HybridMemory:
    """
    Hybrid memory combining conversation and vector memory
    """
    
    def __init__(
        self,
        session_id: str,
        conversation_config: Optional[MemoryConfig] = None,
        vector_config: Optional[MemoryConfig] = None,
        llm = None,
        embeddings: Optional[Embeddings] = None
    ):
        self.session_id = session_id
        
        # Initialize conversation memory
        self.conversation_memory = ConversationMemory(
            session_id=session_id,
            config=conversation_config,
            llm=llm
        )
        
        # Initialize vector memory
        self.vector_memory = VectorMemory(
            collection_name=f"session_{session_id}",
            config=vector_config,
            embeddings=embeddings
        )
    
    async def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add message to both conversation and vector memory"""
        # Add to conversation memory
        await self.conversation_memory.add_message(role, content, metadata)
        
        # Add to vector memory (for semantic search)
        if content.strip():  # Only add non-empty content
            doc_metadata = {
                "role": role,
                "session_id": self.session_id,
                **(metadata or {})
            }
            
            await self.vector_memory.add_documents([{
                "content": content,
                "metadata": doc_metadata
            }])
    
    async def get_conversation_history(self, limit: Optional[int] = None) -> List[BaseMessage]:
        """Get conversation history"""
        return await self.conversation_memory.get_conversation_history(limit)
    
    async def search_relevant_context(
        self,
        query: str,
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """Search for relevant context from vector memory"""
        return await self.vector_memory.search(query, k=k)
    
    async def get_enhanced_context(
        self,
        current_query: str,
        conversation_limit: int = 10,
        context_limit: int = 3
    ) -> Dict[str, Any]:
        """Get enhanced context combining conversation and relevant information"""
        # Get recent conversation
        conversation = await self.get_conversation_history(limit=conversation_limit)
        
        # Get relevant context
        relevant_context = await self.search_relevant_context(current_query, k=context_limit)
        
        return {
            "conversation_history": conversation,
            "relevant_context": relevant_context,
            "session_id": self.session_id
        }
    
    async def clear_memory(self):
        """Clear both conversation and vector memory"""
        await self.conversation_memory.clear_memory()
        # Note: Vector memory clearing would need to be implemented
        # based on the specific vector store's capabilities


class MemoryManager:
    """
    Manager for different types of memory across multiple sessions
    """
    
    def __init__(self):
        self.memories: Dict[str, BaseMemory] = {}
        self.settings = get_settings()
    
    def create_conversation_memory(
        self,
        session_id: str,
        config: Optional[MemoryConfig] = None,
        llm = None
    ) -> ConversationMemory:
        """Create or get conversation memory for a session"""
        if session_id in self.memories:
            return self.memories[session_id]
        
        config = config or MemoryConfig(
            memory_type="conversation",
            persistence_path=f"{self.settings.upload_dir}/memory.db"
        )
        
        memory = ConversationMemory(session_id, config, llm)
        self.memories[session_id] = memory
        return memory
    
    def create_hybrid_memory(
        self,
        session_id: str,
        conversation_config: Optional[MemoryConfig] = None,
        vector_config: Optional[MemoryConfig] = None,
        llm = None,
        embeddings = None
    ) -> HybridMemory:
        """Create hybrid memory for a session"""
        conversation_config = conversation_config or MemoryConfig(
            memory_type="conversation",
            persistence_path=f"{self.settings.upload_dir}/memory.db"
        )
        
        vector_config = vector_config or MemoryConfig(
            memory_type="vector",
            persistence_path=f"{self.settings.upload_dir}/vector_db"
        )
        
        return HybridMemory(
            session_id=session_id,
            conversation_config=conversation_config,
            vector_config=vector_config,
            llm=llm,
            embeddings=embeddings
        )
    
    async def cleanup_old_sessions(self, days_old: int = 30):
        """Clean up memory for sessions older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        sessions_to_remove = []
        for session_id, memory in self.memories.items():
            if memory.last_accessed < cutoff_date:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            await self.memories[session_id].clear_memory()
            del self.memories[session_id]
        
        return len(sessions_to_remove)