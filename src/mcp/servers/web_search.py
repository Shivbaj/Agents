"""
Sample MCP Server for Web Search

This is an example implementation of an MCP server that provides web search capabilities.
It demonstrates how to create custom MCP servers and tools that can be used by agents.

This server provides:
- Web search functionality
- URL content extraction
- Search result summarization

Usage:
    ```python
    from src.mcp.servers.web_search import WebSearchServer
    
    # Create and register server
    server = WebSearchServer()
    await manager.register_server(server)
    
    # Use tools
    response = await manager.execute_tool("web_search", {
        "query": "Python async programming",
        "max_results": 5
    })
    ```
"""

from typing import Dict, Any, List
import json
import asyncio
from datetime import datetime

# Temporarily use print instead of loguru for base implementation
# from loguru import logger

from ..base.tool import BaseMCPServer, BaseMCPTool, MCPToolRequest, MCPToolResponse


class WebSearchTool(BaseMCPTool):
    """Tool for searching the web"""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for information on any topic",
            parameters_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    },
                    "safe_search": {
                        "type": "boolean",
                        "description": "Enable safe search filtering",
                        "default": True
                    }
                },
                "required": ["query"]
            },
            capabilities=["search", "web_access"]
        )
    
    async def execute(self, request: MCPToolRequest) -> MCPToolResponse:
        """Execute web search"""
        try:
            query = request.parameters.get("query")
            max_results = request.parameters.get("max_results", 5)
            safe_search = request.parameters.get("safe_search", True)
            
            print(f"Executing web search: {query} (max_results: {max_results})")
            
            # Simulate web search - in a real implementation, you would integrate with
            # a search API like Google Custom Search, Bing Search, or DuckDuckGo
            await asyncio.sleep(0.5)  # Simulate API call delay
            
            # Mock search results
            mock_results = [
                {
                    "title": f"Result {i+1} for '{query}'",
                    "url": f"https://example{i+1}.com/search-result",
                    "snippet": f"This is a sample search result snippet for query '{query}'. "
                              f"It contains relevant information about the topic.",
                    "domain": f"example{i+1}.com",
                    "timestamp": datetime.now().isoformat()
                }
                for i in range(min(max_results, 5))
            ]
            
            result = {
                "query": query,
                "results": mock_results,
                "total_results": len(mock_results),
                "search_time": 0.5,
                "safe_search_enabled": safe_search
            }
            
            return MCPToolResponse(
                success=True,
                result=result,
                metadata={
                    "tool_name": self.name,
                    "execution_time": 0.5,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            print(f"Web search failed: {str(e)}")
            return MCPToolResponse(
                success=False,
                error=f"Web search failed: {str(e)}"
            )


class URLExtractTool(BaseMCPTool):
    """Tool for extracting content from URLs"""
    
    def __init__(self):
        super().__init__(
            name="url_extract",
            description="Extract text content from a web page URL",
            parameters_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to extract content from"
                    },
                    "extract_links": {
                        "type": "boolean",
                        "description": "Whether to extract links from the page",
                        "default": False
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum length of extracted text",
                        "default": 5000,
                        "minimum": 100,
                        "maximum": 50000
                    }
                },
                "required": ["url"]
            },
            capabilities=["web_access", "content_extraction"]
        )
    
    async def execute(self, request: MCPToolRequest) -> MCPToolResponse:
        """Extract content from URL"""
        try:
            url = request.parameters.get("url")
            extract_links = request.parameters.get("extract_links", False)
            max_length = request.parameters.get("max_length", 5000)
            
            print(f"Extracting content from URL: {url}")
            
            # Simulate URL content extraction - in a real implementation, you would
            # use libraries like requests + BeautifulSoup, scrapy, or playwright
            await asyncio.sleep(1.0)  # Simulate fetch delay
            
            # Mock extracted content
            mock_content = {
                "url": url,
                "title": "Sample Web Page Title",
                "content": f"This is mock extracted content from {url}. " * 20,
                "word_count": 200,
                "language": "en",
                "extraction_time": 1.0
            }
            
            if extract_links:
                mock_content["links"] = [
                    {"text": "Link 1", "url": "https://example.com/link1"},
                    {"text": "Link 2", "url": "https://example.com/link2"}
                ]
            
            # Truncate content if needed
            if len(mock_content["content"]) > max_length:
                mock_content["content"] = mock_content["content"][:max_length] + "..."
                mock_content["truncated"] = True
            
            return MCPToolResponse(
                success=True,
                result=mock_content,
                metadata={
                    "tool_name": self.name,
                    "execution_time": 1.0,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            print(f"URL extraction failed: {str(e)}")
            return MCPToolResponse(
                success=False,
                error=f"URL extraction failed: {str(e)}"
            )


class WebSearchServer(BaseMCPServer):
    """
    MCP Server providing web search and content extraction capabilities
    
    This server demonstrates how to create a collection of related tools
    that work together to provide comprehensive web access functionality.
    """
    
    def __init__(self):
        super().__init__(
            name="web_search_server",
            version="1.0.0",
            description="Provides web search and content extraction tools for agents",
            capabilities=["search", "web_access", "content_extraction"]
        )
    
    async def initialize(self):
        """Initialize the web search server"""
        if self.is_initialized:
            return
        
        print(f"Initializing {self.name}...")
        
        # Perform any initialization tasks here
        # e.g., API key validation, rate limit setup, etc.
        
        self.is_initialized = True
        print(f"{self.name} initialized successfully")
    
    async def register_tools(self) -> List[BaseMCPTool]:
        """Register tools provided by this server"""
        tools = [
            WebSearchTool(),
            URLExtractTool()
        ]
        
        print(f"Registered {len(tools)} tools for {self.name}")
        return tools


# Example of how to create a more specialized server
class ResearchServer(BaseMCPServer):
    """
    Specialized MCP Server for research tasks
    
    This server provides higher-level research capabilities by combining
    multiple web search and analysis tools.
    """
    
    def __init__(self):
        super().__init__(
            name="research_server",
            version="1.0.0", 
            description="Provides advanced research and analysis tools",
            capabilities=["research", "analysis", "synthesis"]
        )
    
    async def initialize(self):
        """Initialize the research server"""
        if self.is_initialized:
            return
        
        print(f"Initializing {self.name}...")
        self.is_initialized = True
        print(f"{self.name} initialized successfully")
    
    async def register_tools(self) -> List[BaseMCPTool]:
        """Register research tools"""
        
        class ResearchTool(BaseMCPTool):
            """Advanced research tool that combines search and analysis"""
            
            def __init__(self):
                super().__init__(
                    name="research_topic",
                    description="Conduct comprehensive research on a topic",
                    parameters_schema={
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "The research topic"
                            },
                            "depth": {
                                "type": "string",
                                "enum": ["shallow", "medium", "deep"],
                                "description": "Research depth level",
                                "default": "medium"
                            },
                            "sources": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Preferred source types",
                                "default": ["academic", "news", "web"]
                            }
                        },
                        "required": ["topic"]
                    },
                    capabilities=["research", "synthesis", "analysis"]
                )
            
            async def execute(self, request: MCPToolRequest) -> MCPToolResponse:
                """Execute research task"""
                try:
                    topic = request.parameters.get("topic")
                    depth = request.parameters.get("depth", "medium")
                    sources = request.parameters.get("sources", ["academic", "news", "web"])
                    
                    print(f"Researching topic: {topic} (depth: {depth})")
                    
                    # Simulate research process
                    await asyncio.sleep(2.0)
                    
                    # Mock research results
                    result = {
                        "topic": topic,
                        "research_depth": depth,
                        "sources_searched": sources,
                        "findings": [
                            {
                                "source": "Academic Paper",
                                "title": f"Research on {topic}",
                                "summary": f"Key findings about {topic} from academic research...",
                                "relevance_score": 0.95
                            },
                            {
                                "source": "News Article", 
                                "title": f"Latest developments in {topic}",
                                "summary": f"Recent news and updates about {topic}...",
                                "relevance_score": 0.87
                            }
                        ],
                        "synthesis": f"Based on research, {topic} appears to be a significant area with multiple perspectives...",
                        "research_time": 2.0
                    }
                    
                    return MCPToolResponse(
                        success=True,
                        result=result,
                        metadata={
                            "tool_name": self.name,
                            "execution_time": 2.0,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    
                except Exception as e:
                    return MCPToolResponse(
                        success=False,
                        error=f"Research failed: {str(e)}"
                    )
        
        tools = [ResearchTool()]
        print(f"Registered {len(tools)} tools for {self.name}")
        return tools