#!/usr/bin/env python3
"""
Debug script to show current PyAutoGUI mouse position and screen information
"""

import pyautogui
import time
from PIL import Image

def main():
    print("🐭 PyAutoGUI Mouse Position Debug")
    print("=" * 40)
    
    # Get screen information
    screen_width, screen_height = pyautogui.size()
    print(f"📺 Screen size: {screen_width}x{screen_height}")
    
    # Get current mouse position
    mouse_x, mouse_y = pyautogui.position()
    print(f"🖱️ Current mouse position: ({mouse_x}, {mouse_y})")
    
    # Take a screenshot and show its size
    try:
        screenshot = pyautogui.screenshot()
        screenshot_width, screenshot_height = screenshot.size
        print(f"📸 Screenshot size: {screenshot_width}x{screenshot_height}")
        
        # Calculate scaling factors
        scale_x = screen_width / screenshot_width
        scale_y = screen_height / screenshot_height
        print(f"📏 Scaling factors: x={scale_x:.2f}, y={scale_y:.2f}")
        
    except Exception as e:
        print(f"❌ Failed to take screenshot: {e}")
    
    print("\n🎯 Moving mouse to test positions...")
    
    # Test some positions
    test_positions = [
        (100, 100),
        (screen_width // 2, screen_height // 2),
        (screen_width - 100, screen_height - 100)
    ]
    
    for i, (x, y) in enumerate(test_positions, 1):
        print(f"\n{i}. Moving to ({x}, {y})...")
        pyautogui.moveTo(x, y, duration=1)
        time.sleep(0.5)
        
        # Get position after move
        actual_x, actual_y = pyautogui.position()
        print(f"   Actual position: ({actual_x}, {actual_y})")
        
        if (x, y) == (actual_x, actual_y):
            print("   ✅ Position matches!")
        else:
            print("   ❌ Position mismatch!")
    
    # Move back to original position
    print(f"\n🔄 Moving back to original position ({mouse_x}, {mouse_y})...")
    pyautogui.moveTo(mouse_x, mouse_y, duration=1)
    
    print("\n✅ Debug complete!")

if __name__ == "__main__":
    main() 