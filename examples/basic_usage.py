#!/usr/bin/env python3
"""
Basic Usage Example for RELAY
Demonstrates how to use RELAY programmatically
"""

import sys
import time
from pathlib import Path

# Add the relay package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from relay.config import Config
from relay.core.vision_engine import VisionEngine
from relay.core.automation_engine import AutomationEngine
from relay.core.task_controller import TaskController

def example_basic_task():
    """Example of running a basic task programmatically"""
    
    print("🚀 RELAY Basic Usage Example")
    print("=" * 40)
    
    # Initialize configuration
    config = Config()
    
    # Check for API key
    api_key = config.get_openai_api_key()
    if not api_key:
        print("❌ OpenAI API key not found!")
        print("Set it with: export OPENAI_API_KEY='your-key'")
        print("Or run: uv run python main.py to set it up interactively")
        return
    
    # Initialize components
    print("📡 Initializing RELAY components...")
    
    vision_engine = VisionEngine(
        api_key=api_key,
        model=config.get("model", "gpt-4-vision-preview")
    )
    
    automation_engine = AutomationEngine()
    task_controller = TaskController(vision_engine, automation_engine)
    
    # Setup callbacks for monitoring
    def on_status_update(status):
        print(f"📊 Status: {status.current_iteration} iterations, "
              f"{status.successful_actions}/{status.total_actions} actions")
    
    def on_narration(message):
        print(f"💭 {message}")
    
    def on_completion(success, message):
        if success:
            print(f"✅ Task completed: {message}")
        else:
            print(f"❌ Task failed: {message}")
    
    # Example task
    task_description = "Open a web browser and navigate to google.com"
    
    print(f"🎯 Starting task: {task_description}")
    print("=" * 40)
    
    # Execute task
    success = task_controller.execute_task(
        task_description,
        on_status_update=on_status_update,
        on_narration=on_narration,
        on_completion=on_completion
    )
    
    if not success:
        print("❌ Failed to start task")
        return
    
    # Wait for completion
    while task_controller.task_status.is_running:
        time.sleep(1)
    
    print("=" * 40)
    print("🏁 Example completed!")

def example_with_custom_settings():
    """Example with custom configuration settings"""
    
    print("\n🔧 RELAY with Custom Settings Example")
    print("=" * 40)
    
    # Create custom config
    config = Config()
    
    # Customize settings
    config.set("max_iterations", 20)  # Limit iterations
    config.set("max_failures", 5)     # Limit failures
    config.set("confidence_threshold", 5)  # Higher confidence requirement
    
    # Initialize with custom settings
    vision_engine = VisionEngine(
        api_key=config.get_openai_api_key(),
        model=config.get("model", "gpt-4-vision-preview")
    )
    
    automation_engine = AutomationEngine()
    task_controller = TaskController(vision_engine, automation_engine)
    
    # Apply custom settings
    task_controller.max_iterations = config.get("max_iterations", 20)
    task_controller.max_failures = config.get("max_failures", 5)
    
    # Simple task
    task_description = "Take a screenshot and wait 2 seconds"
    
    print(f"🎯 Custom task: {task_description}")
    
    def on_narration(message):
        print(f"💭 {message}")
    
    def on_completion(success, message):
        print(f"{'✅' if success else '❌'} {message}")
    
    # Execute
    task_controller.execute_task(
        task_description,
        on_narration=on_narration,
        on_completion=on_completion
    )
    
    # Wait for completion
    while task_controller.task_status.is_running:
        time.sleep(0.5)

def example_error_handling():
    """Example showing error handling and recovery"""
    
    print("\n🛡️ RELAY Error Handling Example")
    print("=" * 40)
    
    config = Config()
    
    vision_engine = VisionEngine(
        api_key=config.get_openai_api_key(),
        model=config.get("model", "gpt-4-vision-preview")
    )
    
    automation_engine = AutomationEngine()
    task_controller = TaskController(vision_engine, automation_engine)
    
    # Task that might fail
    task_description = "Click on a non-existent button that doesn't exist"
    
    print(f"🎯 Testing error handling: {task_description}")
    
    def on_narration(message):
        print(f"💭 {message}")
    
    def on_completion(success, message):
        if not success:
            print(f"❌ Expected failure: {message}")
            print("This demonstrates RELAY's error handling capabilities")
        else:
            print("✅ Unexpected success!")
    
    # Execute
    task_controller.execute_task(
        task_description,
        on_narration=on_narration,
        on_completion=on_completion
    )
    
    # Wait for completion
    while task_controller.task_status.is_running:
        time.sleep(0.5)

if __name__ == "__main__":
    try:
        # Run examples
        example_basic_task()
        example_with_custom_settings()
        example_error_handling()
        
        print("\n🎉 All examples completed!")
        print("Try running the main application with: uv run python main.py")
        
    except KeyboardInterrupt:
        print("\n👋 Examples stopped by user")
    except Exception as e:
        print(f"\n❌ Error in examples: {e}")
        import traceback
        traceback.print_exc() 