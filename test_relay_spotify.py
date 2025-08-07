#!/usr/bin/env python3
"""
Test script using actual RELAY functions to open Spotify
"""

import sys
import os
import logging
from pathlib import Path

# Add the relay package to the path
sys.path.insert(0, str(Path(__file__).parent))

from relay.config import Config
from relay.core.vision_engine import VisionEngine, VisionContext, ActionPlan
from relay.core.automation_engine import AutomationEngine, ExecutionResult
from relay.core.task_controller import TaskController
from PIL import Image
import time

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_spotify_open():
    """Test opening Spotify using RELAY functions"""
    print("🎵 Testing RELAY Spotify Opening")
    print("=" * 40)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config = Config()
        
        # Check API key
        api_key = config.get_openai_api_key()
        if not api_key:
            print("❌ No OpenAI API key found. Set OPENAI_API_KEY environment variable.")
            return False
        
        print("✅ Configuration loaded successfully")
        
        # Initialize components
        print("🔧 Initializing RELAY components...")
        
        # Vision engine
        vision_engine = VisionEngine(
            api_key=api_key,
            model=config.get("model", "gpt-4o-mini")
        )
        
        # Automation engine
        automation_engine = AutomationEngine(vision_engine)
        
        # Task controller
        task_controller = TaskController(vision_engine, automation_engine)
        
        print("✅ Components initialized successfully")
        
        # Test 1: Manual coordinate logging (no actual click)
        print("\n🧪 Test 1: Manual coordinates (dry-run, no actual click)")
        print("🎯 Manual Spotify coordinates: (756, 1006)")
        print("ℹ️  Skipping real click – using these coordinates only for comparison.")
        
        # ------------------------------------------------------------
        # Test 2: Full task execution with AI vision
        print("\n🧪 Test 2: Full task execution with AI vision")
        
        # Create a simple task context
        context = VisionContext(
            task_description="Open Spotify application",
            previous_actions=[],
            screenshots_history=[],
            current_screenshot=""
        )
        
        # Take a screenshot
        import pyautogui
        screenshot = pyautogui.screenshot()
        print(f"📸 Screenshot taken: {screenshot.size}")
        
        # Ask AI to analyze and plan action
        print("🤖 Asking AI to analyze screenshot and plan action...")
        ai_action_plan = vision_engine.analyze_screenshot(screenshot, context)
        
        print(f"🤖 AI suggested action: {ai_action_plan.action_type}")
        print(f"🤖 AI coordinates: {ai_action_plan.coordinates}")
        print(f"🤖 AI confidence: {ai_action_plan.confidence}/10")
        print(f"🤖 AI reasoning: {ai_action_plan.reasoning}")
        
        # Execute AI's suggested action
        if ai_action_plan.coordinates:
            print(f"🎯 Executing AI's suggested action at {ai_action_plan.coordinates}")
            ai_result = automation_engine.execute_action(ai_action_plan)
            
            if ai_result.success:
                if ai_result.action_verified:
                    print("✅ AI action completed and VERIFIED!")
                    print(f"   Verification: {ai_result.verification_message}")
                else:
                    print("⚠️ AI action completed but NOT VERIFIED")
                    print(f"   Verification: {ai_result.verification_message}")
            else:
                print(f"❌ AI action failed: {ai_result.error_message}")
        else:
            print("❌ AI didn't provide coordinates")
        
        # Test 3: Compare AI vs manual coordinates
        print("\n🧪 Test 3: Comparing AI vs manual coordinates")
        
        if ai_action_plan.coordinates:
            ai_x, ai_y = ai_action_plan.coordinates
            manual_x, manual_y = 756, 1006
            
            distance = ((ai_x - manual_x) ** 2 + (ai_y - manual_y) ** 2) ** 0.5
            print(f"📏 Distance between AI and manual coordinates: {distance:.1f} pixels")
            
            if distance < 50:
                print("✅ AI coordinates are close to manual coordinates")
            else:
                print("❌ AI coordinates are far from manual coordinates")
                print(f"   Manual: ({manual_x}, {manual_y})")
                print(f"   AI: ({ai_x}, {ai_y})")
        
        print("\n✅ Test complete!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.error(f"Test error: {e}")
        return False

def main():
    """Main test function"""
    success = test_spotify_open()
    
    if success:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 