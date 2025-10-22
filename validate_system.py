#!/usr/bin/env python3
"""
Comprehensive validation script for Multi-Agent System
Tests all components, dependencies, and Docker setup
"""
import asyncio
import os
import sys
import subprocess
from pathlib import Path
import json
from typing import List, Dict, Any

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


class ValidationResult:
    def __init__(self, name: str, success: bool, message: str, details: Dict[str, Any] = None):
        self.name = name
        self.success = success
        self.message = message
        self.details = details or {}


class SystemValidator:
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, result: ValidationResult):
        self.results.append(result)
        if result.success:
            self.passed += 1
            print(f"✅ {result.name}: {result.message}")
        else:
            self.failed += 1
            print(f"❌ {result.name}: {result.message}")
            if result.details:
                for key, value in result.details.items():
                    print(f"   {key}: {value}")
    
    def test_python_version(self):
        """Test Python version compatibility"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 9:
            self.add_result(ValidationResult(
                "Python Version",
                True,
                f"Python {version.major}.{version.minor}.{version.micro} (compatible)"
            ))
        else:
            self.add_result(ValidationResult(
                "Python Version", 
                False,
                f"Python {version.major}.{version.minor}.{version.micro} (requires Python 3.9+)"
            ))
    
    def test_uv_installation(self):
        """Test UV package manager"""
        try:
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.add_result(ValidationResult(
                    "UV Package Manager",
                    True,
                    f"UV installed: {result.stdout.strip()}"
                ))
            else:
                self.add_result(ValidationResult(
                    "UV Package Manager",
                    False,
                    "UV not working properly"
                ))
        except FileNotFoundError:
            self.add_result(ValidationResult(
                "UV Package Manager",
                False,
                "UV not installed"
            ))
    
    def test_core_dependencies(self):
        """Test core Python dependencies"""
        dependencies = {
            "fastapi": "FastAPI web framework",
            "uvicorn": "ASGI server",
            "pydantic": "Data validation",
            "redis": "Redis client",
            "httpx": "HTTP client",
            "loguru": "Logging library",
            "langsmith": "Observability (optional)"
        }
        
        for package, description in dependencies.items():
            try:
                __import__(package)
                self.add_result(ValidationResult(
                    f"Package: {package}",
                    True,
                    f"{description} - Available"
                ))
            except ImportError:
                optional = "(optional)" in description
                self.add_result(ValidationResult(
                    f"Package: {package}",
                    optional,  # Optional packages don't fail validation
                    f"{description} - {'Missing (optional)' if optional else 'Missing (required)'}"
                ))
    
    def test_project_structure(self):
        """Test project directory structure"""
        required_dirs = [
            "src",
            "src/agents",
            "src/api", 
            "src/config",
            "src/mcp",
            "src/observability",
            "tests"
        ]
        
        required_files = [
            "pyproject.toml",
            "uv.lock",
            "requirements.txt",
            "src/main.py",
            "src/config/settings.py",
            ".env.example",
            "docker-compose.yml",
            "Dockerfile"
        ]
        
        for directory in required_dirs:
            path = Path(directory)
            if path.exists() and path.is_dir():
                self.add_result(ValidationResult(
                    f"Directory: {directory}",
                    True,
                    "Present"
                ))
            else:
                self.add_result(ValidationResult(
                    f"Directory: {directory}",
                    False,
                    "Missing"
                ))
        
        for file in required_files:
            path = Path(file)
            if path.exists() and path.is_file():
                self.add_result(ValidationResult(
                    f"File: {file}",
                    True,
                    "Present"
                ))
            else:
                self.add_result(ValidationResult(
                    f"File: {file}",
                    False,
                    "Missing"
                ))
    
    def test_docker_setup(self):
        """Test Docker configuration"""
        try:
            # Test Docker
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.add_result(ValidationResult(
                    "Docker",
                    True,
                    f"Docker installed: {result.stdout.strip()}"
                ))
            else:
                self.add_result(ValidationResult(
                    "Docker",
                    False,
                    "Docker not working"
                ))
            
            # Test Docker Compose
            compose_cmd = None
            for cmd in ["docker-compose", "docker compose"]:
                try:
                    result = subprocess.run([*cmd.split(), "--version"], capture_output=True, text=True)
                    if result.returncode == 0:
                        compose_cmd = cmd
                        self.add_result(ValidationResult(
                            "Docker Compose",
                            True,
                            f"Docker Compose available: {result.stdout.strip()}"
                        ))
                        break
                except FileNotFoundError:
                    continue
            
            if not compose_cmd:
                self.add_result(ValidationResult(
                    "Docker Compose",
                    False,
                    "Docker Compose not available"
                ))
        
        except FileNotFoundError:
            self.add_result(ValidationResult(
                "Docker",
                False,
                "Docker not installed"
            ))
    
    async def test_application_startup(self):
        """Test that the application can start up"""
        try:
            from src.config.settings import get_settings
            settings = get_settings()
            
            self.add_result(ValidationResult(
                "Settings Loading",
                True,
                f"Configuration loaded (environment: {settings.environment})"
            ))
            
            # Test MCP system
            from src.mcp.manager import get_mcp_manager
            mcp_manager = get_mcp_manager()
            await mcp_manager.initialize()
            
            self.add_result(ValidationResult(
                "MCP System",
                True,
                "MCP manager initialization successful"
            ))
            
            # Test observability system
            try:
                from src.observability import initialize_observability
                await initialize_observability()
                
                self.add_result(ValidationResult(
                    "Observability System",
                    True,
                    "Observability initialization successful"
                ))
            except Exception as e:
                self.add_result(ValidationResult(
                    "Observability System",
                    True,  # Non-critical
                    f"Observability initialization failed (non-critical): {str(e)}"
                ))
            
            # Test agent system
            from src.agents.registry.manager import AgentManager
            agent_manager = AgentManager()
            await agent_manager.initialize()
            
            self.add_result(ValidationResult(
                "Agent System",
                True,
                "Agent manager initialization successful"
            ))
            
            # Cleanup
            await mcp_manager.cleanup()
            await agent_manager.cleanup()
            
        except Exception as e:
            self.add_result(ValidationResult(
                "Application Startup",
                False,
                f"Failed to initialize application: {str(e)}"
            ))
    
    def test_environment_variables(self):
        """Test environment configuration"""
        # Check for .env file
        env_file = Path(".env")
        example_file = Path(".env.example")
        
        if env_file.exists():
            self.add_result(ValidationResult(
                "Environment File",
                True,
                ".env file present"
            ))
        elif example_file.exists():
            self.add_result(ValidationResult(
                "Environment File",
                True,
                ".env.example present (copy to .env and configure)"
            ))
        else:
            self.add_result(ValidationResult(
                "Environment File",
                False,
                "No environment configuration found"
            ))
        
        # Check critical environment variables
        env_vars = [
            ("OPENAI_API_KEY", "OpenAI API access", True),
            ("ANTHROPIC_API_KEY", "Anthropic API access", True),
            ("LANGSMITH_API_KEY", "LangSmith observability", True),
            ("REDIS_URL", "Redis connection", False),
            ("OLLAMA_BASE_URL", "Ollama connection", False)
        ]
        
        for var_name, description, optional in env_vars:
            value = os.getenv(var_name)
            if value:
                # Mask sensitive values
                display_value = value[:8] + "..." if len(value) > 8 else "set"
                self.add_result(ValidationResult(
                    f"Env Var: {var_name}",
                    True,
                    f"{description} - {display_value}"
                ))
            else:
                self.add_result(ValidationResult(
                    f"Env Var: {var_name}",
                    optional,  # Optional vars don't fail validation
                    f"{description} - {'Not set (optional)' if optional else 'Not set (required for functionality)'}"
                ))
    
    def generate_report(self):
        """Generate validation report"""
        print("\n" + "="*60)
        print("🔍 MULTI-AGENT SYSTEM VALIDATION REPORT")
        print("="*60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📊 Total: {len(self.results)}")
        
        if self.failed == 0:
            print("\n🎉 All validations passed! System is ready to run.")
            print("\n🚀 Quick start commands:")
            print("   Development: ./start.sh")
            print("   Docker Dev:  docker-compose -f docker-compose.dev.yml up")
            print("   Docker Prod: docker-compose -f docker-compose.prod.yml up")
        else:
            print(f"\n⚠️  {self.failed} validation(s) failed. Please review and fix:")
            for result in self.results:
                if not result.success:
                    print(f"   - {result.name}: {result.message}")
        
        print("\n📚 Documentation:")
        print("   - API Docs: http://localhost:8000/docs")
        print("   - Architecture: ARCHITECTURE.md")
        print("   - Development: DEVELOPMENT.md")
        print("   - API Examples: API_EXAMPLES.md")


async def main():
    """Run comprehensive validation"""
    print("🔍 Starting Multi-Agent System Validation...")
    print("=" * 60)
    
    validator = SystemValidator()
    
    # Run all validations
    print("\n📋 Testing system requirements...")
    validator.test_python_version()
    validator.test_uv_installation()
    
    print("\n📦 Testing dependencies...")
    validator.test_core_dependencies()
    
    print("\n📁 Testing project structure...")
    validator.test_project_structure()
    
    print("\n🐳 Testing Docker setup...")
    validator.test_docker_setup()
    
    print("\n🔧 Testing environment configuration...")
    validator.test_environment_variables()
    
    print("\n🚀 Testing application components...")
    await validator.test_application_startup()
    
    # Generate final report
    validator.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if validator.failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())