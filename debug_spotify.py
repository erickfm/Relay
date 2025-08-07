#!/usr/bin/env python3
"""
Debug script to find and test clicking on the Spotify icon
"""

import pyautogui
import time
from PIL import Image

def main():
    print("🎵 Spotify Icon Debug")
    print("=" * 30)
    
    # Get screen information
    screen_width, screen_height = pyautogui.size()
    print(f"📺 Screen size: {screen_width}x{screen_height}")
    
    # Common dock positions (bottom of screen)
    print("\n🔍 Testing common dock positions...")
    
    # Test different Y positions near the bottom
    y_positions = [screen_height - 50, screen_height - 100, screen_height - 150]
    
    for y in y_positions:
        print(f"\n🎯 Testing Y position: {y}")
        
        # Test different X positions across the bottom
        x_positions = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500]
        
        for x in x_positions:
            if x > screen_width:
                continue
                
            print(f"   Testing ({x}, {y})...")
            
            # Move to position
            pyautogui.moveTo(x, y, duration=0.1)
            time.sleep(0.1)
            
            # Get current position to verify
            actual_x, actual_y = pyautogui.position()
            print(f"   Actual position: ({actual_x}, {actual_y})")
            
            # Optional: take a screenshot to see what's there
            # screenshot = pyautogui.screenshot(region=(x-50, y-50, 100, 100))
            # screenshot.save(f"debug_{x}_{y}.png")
    
    print("\n🎯 Manual testing - move your mouse to the Spotify icon and press Enter...")
    input("Press Enter when your mouse is over the Spotify icon...")
    
    # Get the position where user placed the mouse
    spotify_x, spotify_y = pyautogui.position()
    print(f"🎵 Spotify icon position: ({spotify_x}, {spotify_y})")
    
    # Test clicking on that position
    print(f"\n🖱️ Testing click on Spotify icon at ({spotify_x}, {spotify_y})...")
    
    # Take before screenshot
    before_screenshot = pyautogui.screenshot()
    print("📸 Before screenshot taken")
    
    # Click
    pyautogui.click(spotify_x, spotify_y)
    print("🖱️ Click executed")
    
    # Wait a moment
    time.sleep(2)
    
    # Take after screenshot
    after_screenshot = pyautogui.screenshot()
    print("📸 After screenshot taken")
    
    # Save screenshots for comparison
    before_screenshot.save("before_spotify_click.png")
    after_screenshot.save("after_spotify_click.png")
    print("💾 Screenshots saved as 'before_spotify_click.png' and 'after_spotify_click.png'")
    
    print("\n✅ Debug complete! Check the screenshots to see if Spotify opened.")

if __name__ == "__main__":
    main() 