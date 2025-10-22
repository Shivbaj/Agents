"""
LangGraph-based workflow orchestration for multi-agent systems

This module provides a framework for creating complex workflows that coordinate
multiple agents to solve sophisticated tasks. It uses LangGraph for state management
and execution flow control.

Key Features:
- Multi-agent coordination
- State management across workflow steps
- Conditional routing and decision making
- Error handling and recovery
- Parallel execution capabilities
- Dynamic agent selection

Example Usage:
    ```python
    from src.orchestrator.workflow import WorkflowBuilder, WorkflowState
    from src.agents.implementations.general_assistant import GeneralAssistant
    
    # Create a workflow
    builder = WorkflowBuilder()
    workflow = builder.create_research_workflow()
    
    # Execute workflow
    result = await workflow.execute({
        "query": "Research the latest developments in AI",
        "max_depth": 3
    })
    ```
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, TypedDict, Annotated
from enum import Enum
import json

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool
from loguru import logger

from src.agents.base.agent import BaseAgent
from src.agents.registry.manager import AgentManager


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowState(TypedDict):
    """
    Base state structure for workflows
    
    This can be extended by specific workflows to include additional state fields
    """
    # Core workflow state
    workflow_id: str
    status: WorkflowStatus
    current_step: str
    steps_completed: List[str]
    
    # Input/Output
    initial_input: Dict[str, Any]
    current_input: Dict[str, Any]
    final_output: Optional[Dict[str, Any]]
    
    # Agent coordination
    active_agents: List[str]
    agent_outputs: Dict[str, Any]
    
    # Messages and communication
    messages: List[BaseMessage]
    
    # Metadata and tracking
    created_at: datetime
    updated_at: datetime
    execution_time: float
    error_message: Optional[str]


class WorkflowNode:
    """
    Represents a single node/step in a workflow
    """
    
    def __init__(
        self,
        name: str,
        agent_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        function: Optional[Callable] = None,
        tools: Optional[List[BaseTool]] = None,
        condition: Optional[Callable] = None,
        timeout: int = 300
    ):
        self.name = name
        self.agent_type = agent_type
        self.agent_id = agent_id
        self.function = function
        self.tools = tools or []
        self.condition = condition
        self.timeout = timeout


class MultiAgentWorkflow:
    """
    A workflow that coordinates multiple agents using LangGraph
    """
    
    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: str = "",
        agent_manager: Optional[AgentManager] = None
    ):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.agent_manager = agent_manager or AgentManager()
        
        # Graph components
        self.graph: Optional[StateGraph] = None
        self.nodes: Dict[str, WorkflowNode] = {}
        self.compiled_graph = None
        
        # Execution tracking
        self.execution_history: List[Dict[str, Any]] = []
        
        logger.info(f"Created workflow: {self.workflow_id} ({self.name})")
    
    def add_node(self, node: WorkflowNode) -> 'MultiAgentWorkflow':
        """Add a node to the workflow"""
        self.nodes[node.name] = node
        logger.info(f"Added node '{node.name}' to workflow {self.workflow_id}")
        return self
    
    async def _execute_agent_node(
        self, 
        state: WorkflowState, 
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Execute a node that uses an agent"""
        try:
            # Get or create agent
            if node.agent_id:
                agent = await self.agent_manager.get_agent(node.agent_id)
            elif node.agent_type:
                agents = await self.agent_manager.discover_agents(node.agent_type)
                if not agents:
                    raise ValueError(f"No agents found for type: {node.agent_type}")
                agent = agents[0]  # Use first available agent
            else:
                raise ValueError(f"Node {node.name} requires either agent_id or agent_type")
            
            if not agent:
                raise ValueError(f"Agent not found for node {node.name}")
            
            # Prepare input for agent
            agent_input = state.get("current_input", {})
            session_id = f"{state['workflow_id']}_{node.name}"
            
            # Add tools to agent if specified
            if node.tools:
                for tool in node.tools:
                    agent.add_tool(tool)
            
            # Execute agent
            logger.info(f"Executing agent {agent.id} for node {node.name}")
            
            if isinstance(agent_input, dict) and "message" in agent_input:
                message = agent_input["message"]
            else:
                message = str(agent_input)
            
            response = await agent.process_message(
                message=message,
                session_id=session_id,
                context=agent_input
            )
            
            # Update state
            state["agent_outputs"][node.name] = {
                "agent_id": agent.id,
                "response": response.content,
                "metadata": response.metadata
            }
            
            state["current_input"] = {
                "message": response.content,
                **response.metadata
            }
            
            return state
            
        except Exception as e:
            logger.error(f"Error executing agent node {node.name}: {str(e)}")
            state["error_message"] = str(e)
            state["status"] = WorkflowStatus.FAILED
            return state
    
    async def _execute_function_node(
        self, 
        state: WorkflowState, 
        node: WorkflowNode
    ) -> Dict[str, Any]:
        """Execute a node that uses a custom function"""
        try:
            if not node.function:
                raise ValueError(f"Node {node.name} requires a function")
            
            logger.info(f"Executing function for node {node.name}")
            
            # Execute function (handle both sync and async)
            if asyncio.iscoroutinefunction(node.function):
                result = await node.function(state)
            else:
                result = node.function(state)
            
            # Update state based on result
            if isinstance(result, dict):
                state.update(result)
            else:
                state["current_input"] = {"result": result}
            
            return state
            
        except Exception as e:
            logger.error(f"Error executing function node {node.name}: {str(e)}")
            state["error_message"] = str(e)
            state["status"] = WorkflowStatus.FAILED
            return state
    
    def _create_node_executor(self, node_name: str):
        """Create an executor function for a specific node"""
        
        async def execute_node(state: WorkflowState) -> WorkflowState:
            node = self.nodes[node_name]
            
            # Check condition if specified
            if node.condition and not node.condition(state):
                logger.info(f"Skipping node {node_name} - condition not met")
                return state
            
            # Update tracking
            state["current_step"] = node_name
            state["updated_at"] = datetime.now()
            
            # Execute based on node type
            if node.agent_type or node.agent_id:
                result_state = await self._execute_agent_node(state, node)
            elif node.function:
                result_state = await self._execute_function_node(state, node)
            else:
                raise ValueError(f"Node {node_name} has no execution method defined")
            
            # Update completion tracking
            if result_state.get("status") != WorkflowStatus.FAILED:
                result_state["steps_completed"].append(node_name)
            
            return result_state
        
        return execute_node
    
    def compile(self) -> 'MultiAgentWorkflow':
        """Compile the workflow into an executable graph"""
        if not self.nodes:
            raise ValueError("Cannot compile workflow with no nodes")
        
        # Create state graph
        self.graph = StateGraph(WorkflowState)
        
        # Add nodes
        for node_name in self.nodes:
            executor = self._create_node_executor(node_name)
            self.graph.add_node(node_name, executor)
        
        # Set entry point (first node added)
        first_node = next(iter(self.nodes.keys()))
        self.graph.set_entry_point(first_node)
        
        # Compile graph
        self.compiled_graph = self.graph.compile()
        
        logger.info(f"Compiled workflow {self.workflow_id} with {len(self.nodes)} nodes")
        return self
    
    def add_edge(self, from_node: str, to_node: str) -> 'MultiAgentWorkflow':
        """Add an edge between two nodes"""
        if not self.graph:
            raise ValueError("Must create graph before adding edges")
        
        self.graph.add_edge(from_node, to_node)
        logger.info(f"Added edge: {from_node} -> {to_node}")
        return self
    
    def add_conditional_edge(
        self, 
        from_node: str, 
        condition_func: Callable,
        condition_map: Dict[str, str]
    ) -> 'MultiAgentWorkflow':
        """Add a conditional edge that routes based on state"""
        if not self.graph:
            raise ValueError("Must create graph before adding edges")
        
        self.graph.add_conditional_edges(from_node, condition_func, condition_map)
        logger.info(f"Added conditional edge from {from_node}")
        return self
    
    def finish_at(self, node_name: str) -> 'MultiAgentWorkflow':
        """Mark a node as a terminal node"""
        if not self.graph:
            raise ValueError("Must create graph before setting terminal nodes")
        
        self.graph.add_edge(node_name, END)
        logger.info(f"Set {node_name} as terminal node")
        return self
    
    async def execute(
        self, 
        initial_input: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """Execute the workflow with given input"""
        if not self.compiled_graph:
            raise ValueError("Workflow must be compiled before execution")
        
        # Create initial state
        initial_state: WorkflowState = {
            "workflow_id": self.workflow_id,
            "status": WorkflowStatus.RUNNING,
            "current_step": "",
            "steps_completed": [],
            "initial_input": initial_input,
            "current_input": initial_input,
            "final_output": None,
            "active_agents": [],
            "agent_outputs": {},
            "messages": [HumanMessage(content=str(initial_input))],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "execution_time": 0.0,
            "error_message": None
        }
        
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting workflow execution: {self.workflow_id}")
            
            # Execute workflow
            final_state = await self.compiled_graph.ainvoke(
                initial_state, 
                config=config or {}
            )
            
            # Update final state
            execution_time = (datetime.now() - start_time).total_seconds()
            final_state["execution_time"] = execution_time
            final_state["updated_at"] = datetime.now()
            
            if final_state.get("status") != WorkflowStatus.FAILED:
                final_state["status"] = WorkflowStatus.COMPLETED
                final_state["final_output"] = final_state.get("current_input")
            
            # Add to execution history
            self.execution_history.append({
                "execution_id": f"{self.workflow_id}_{start_time.timestamp()}",
                "start_time": start_time,
                "end_time": datetime.now(),
                "execution_time": execution_time,
                "status": final_state["status"],
                "steps_completed": final_state["steps_completed"],
                "final_output": final_state.get("final_output")
            })
            
            logger.info(f"Workflow execution completed: {self.workflow_id}")
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {self.workflow_id} - {str(e)}")
            
            # Create error state
            error_state = initial_state.copy()
            error_state.update({
                "status": WorkflowStatus.FAILED,
                "error_message": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "updated_at": datetime.now()
            })
            
            return error_state


class WorkflowBuilder:
    """
    Builder class for creating common workflow patterns
    """
    
    def __init__(self, agent_manager: Optional[AgentManager] = None):
        self.agent_manager = agent_manager or AgentManager()
    
    def create_research_workflow(self, workflow_id: str = None) -> MultiAgentWorkflow:
        """
        Create a research workflow that:
        1. Takes a query
        2. Plans research approach
        3. Gathers information
        4. Synthesizes findings
        5. Creates final report
        """
        workflow_id = workflow_id or f"research_workflow_{datetime.now().timestamp()}"
        
        workflow = MultiAgentWorkflow(
            workflow_id=workflow_id,
            name="Research Workflow",
            description="Multi-step research workflow with planning, gathering, and synthesis",
            agent_manager=self.agent_manager
        )
        
        # Add nodes
        workflow.add_node(WorkflowNode(
            name="planner",
            agent_type="general_assistant",
            function=None
        ))
        
        workflow.add_node(WorkflowNode(
            name="researcher",
            agent_type="general_assistant",
            function=None
        ))
        
        workflow.add_node(WorkflowNode(
            name="synthesizer",
            agent_type="summarizer_agent",
            function=None
        ))
        
        # Build graph structure
        workflow.compile()
        workflow.add_edge("planner", "researcher")
        workflow.add_edge("researcher", "synthesizer")
        workflow.finish_at("synthesizer")
        
        return workflow.compile()
    
    def create_document_processing_workflow(
        self, 
        workflow_id: str = None
    ) -> MultiAgentWorkflow:
        """
        Create a document processing workflow that:
        1. Receives document
        2. Extracts text/content
        3. Analyzes content
        4. Generates summary
        5. Creates insights
        """
        workflow_id = workflow_id or f"doc_processing_{datetime.now().timestamp()}"
        
        workflow = MultiAgentWorkflow(
            workflow_id=workflow_id,
            name="Document Processing Workflow",
            description="Multi-step document analysis and processing",
            agent_manager=self.agent_manager
        )
        
        # Custom extraction function
        async def extract_content(state: WorkflowState) -> Dict[str, Any]:
            """Extract content from document"""
            # This would integrate with actual document processing tools
            doc_input = state.get("current_input", {})
            extracted_content = f"Extracted content from: {doc_input}"
            
            return {
                "current_input": {
                    "message": f"Please analyze this content: {extracted_content}",
                    "content": extracted_content
                }
            }
        
        # Add nodes
        workflow.add_node(WorkflowNode(
            name="extractor",
            function=extract_content
        ))
        
        workflow.add_node(WorkflowNode(
            name="analyzer",
            agent_type="general_assistant"
        ))
        
        workflow.add_node(WorkflowNode(
            name="summarizer",
            agent_type="summarizer_agent"
        ))
        
        # Build graph structure
        workflow.compile()
        workflow.add_edge("extractor", "analyzer")
        workflow.add_edge("analyzer", "summarizer")
        workflow.finish_at("summarizer")
        
        return workflow.compile()
    
    def create_multimodal_analysis_workflow(
        self, 
        workflow_id: str = None
    ) -> MultiAgentWorkflow:
        """
        Create a multimodal analysis workflow for processing images and text
        """
        workflow_id = workflow_id or f"multimodal_{datetime.now().timestamp()}"
        
        workflow = MultiAgentWorkflow(
            workflow_id=workflow_id,
            name="Multimodal Analysis Workflow",
            description="Process images and text together for comprehensive analysis",
            agent_manager=self.agent_manager
        )
        
        # Route based on input type
        def route_input(state: WorkflowState) -> str:
            """Route to different processors based on input type"""
            current_input = state.get("current_input", {})
            
            if "image" in current_input or "file_path" in current_input:
                return "vision_processor"
            else:
                return "text_processor"
        
        # Add nodes
        workflow.add_node(WorkflowNode(
            name="vision_processor",
            agent_type="vision_agent"
        ))
        
        workflow.add_node(WorkflowNode(
            name="text_processor",
            agent_type="general_assistant"
        ))
        
        workflow.add_node(WorkflowNode(
            name="integrator",
            agent_type="general_assistant"
        ))
        
        # Build graph structure with conditional routing
        workflow.compile()
        workflow.add_conditional_edge(
            "START", 
            route_input, 
            {
                "vision_processor": "vision_processor",
                "text_processor": "text_processor"
            }
        )
        workflow.add_edge("vision_processor", "integrator")
        workflow.add_edge("text_processor", "integrator")
        workflow.finish_at("integrator")
        
        return workflow.compile()