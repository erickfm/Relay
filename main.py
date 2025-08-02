#!/usr/bin/env python3
"""
RELAY: Universal Desktop Assistant
Main entry point for the application
"""

import sys
import os
import logging
import traceback
from pathlib import Path

# Add the relay package to the path
sys.path.insert(0, str(Path(__file__).parent))

from relay.config import Config
from relay.core.vision_engine import VisionEngine
from relay.core.automation_engine import AutomationEngine
from relay.core.task_controller import TaskController
from relay.ui.main_window import MainWindow

def setup_logging(config: Config):
    """Setup logging configuration"""
    log_config = config.get_logging_settings()
    log_level = getattr(logging, log_config.get("level", "INFO").upper())
    
    # Create logs directory
    log_dir = Path.home() / ".relay" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / log_config.get("file", "relay.log")),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_dependencies():
    """Check if all required dependencies are available"""
    missing_deps = []
    
    try:
        import openai
    except ImportError:
        missing_deps.append("openai")
    
    try:
        import pyautogui
    except ImportError:
        missing_deps.append("pyautogui")
    
    try:
        import customtkinter
    except ImportError:
        missing_deps.append("customtkinter")
    
    try:
        from PIL import Image
    except ImportError:
        missing_deps.append("pillow")
    
    if missing_deps:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\nInstall them with uv:")
        print("   uv sync")
        print("\nOr run the installation script:")
        print("   ./install.sh")
        return False
    
    return True

def check_permissions():
    """Check if RELAY has necessary permissions"""
    try:
        import pyautogui
        # Test screenshot capability
        screenshot = pyautogui.screenshot()
        if screenshot is None:
            print("❌ Cannot take screenshots. Check screen recording permissions.")
            return False
    except Exception as e:
        print(f"❌ Permission check failed: {e}")
        print("Make sure RELAY has screen recording and accessibility permissions.")
        return False
    
    return True

def setup_api_key(config: Config):
    """Setup OpenAI API key"""
    api_key = config.get_openai_api_key()
    
    if not api_key:
        print("🔑 OpenAI API Key Required")
        print("RELAY needs an OpenAI API key to function.")
        print("\nYou can set it in several ways:")
        print("1. Environment variable: export OPENAI_API_KEY='your-key-here'")
        print("2. Configuration file: ~/.relay/config.json")
        print("3. Enter it now (will be saved to config file)")
        
        choice = input("\nEnter your OpenAI API key now? (y/n): ").lower().strip()
        
        if choice == 'y':
            api_key = input("OpenAI API Key: ").strip()
            if api_key:
                config.set_openai_api_key(api_key)
                print("✅ API key saved!")
            else:
                print("❌ No API key provided. Exiting.")
                return False
        else:
            print("❌ API key required. Exiting.")
            return False
    
    return True

def main():
    """Main application entry point"""
    print("🚀 Starting RELAY: Universal Desktop Assistant")
    print("=" * 50)
    
    try:
        # Check dependencies
        if not check_dependencies():
            sys.exit(1)
        
        # Load configuration
        config = Config()
        setup_logging(config)
        logger = logging.getLogger(__name__)
        
        logger.info("RELAY starting up...")
        
        # Check permissions
        if not check_permissions():
            logger.error("Permission check failed")
            sys.exit(1)
        
        # Setup API key
        if not setup_api_key(config):
            logger.error("API key setup failed")
            sys.exit(1)
        
        # Validate configuration
        if not config.validate_config():
            logger.error("Configuration validation failed")
            sys.exit(1)
        
        logger.info("Configuration validated successfully")
        
        # Initialize components
        logger.info("Initializing RELAY components...")
        
        # Vision engine
        vision_engine = VisionEngine(
            api_key=config.get_openai_api_key(),
            model=config.get("model", "gpt-4-vision-preview")
        )
        
        # Automation engine
        automation_engine = AutomationEngine()
        
        # Task controller
        task_controller = TaskController(vision_engine, automation_engine)
        
        # Apply configuration to components
        task_controller.max_iterations = config.get("max_iterations", 50)
        task_controller.max_failures = config.get("max_failures", 10)
        
        logger.info("Components initialized successfully")
        
        # Create and run UI
        logger.info("Starting user interface...")
        app = MainWindow(task_controller)
        
        print("✅ RELAY is ready!")
        print("💡 Try asking it to: 'Make a dad rock playlist on Spotify'")
        print("🛑 Move mouse to screen corner for emergency stop")
        print("=" * 50)
        
        app.run()
        
    except KeyboardInterrupt:
        print("\n👋 RELAY stopped by user")
        logger.info("Application stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 