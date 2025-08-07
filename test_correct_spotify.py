#!/usr/bin/env python3
"""
Test script to click at the correct Spotify coordinates
"""

import pyautogui
import time
from PIL import Image

def main():
    print("🎵 Testing Correct Spotify Coordinates")
    print("=" * 40)
    
    # The correct coordinates we found
    spotify_x, spotify_y = 587, 1001
    print(f"🎯 Correct Spotify position: ({spotify_x}, {spotify_y})")
    
    # Get current mouse position
    current_x, current_y = pyautogui.position()
    print(f"🖱️ Current mouse position: ({current_x}, {current_y})")
    
    # Take before screenshot
    print("📸 Taking before screenshot...")
    before_screenshot = pyautogui.screenshot()
    before_screenshot.save("test_before_spotify.png")
    
    # Move to Spotify icon
    print(f"🖱️ Moving to Spotify icon at ({spotify_x}, {spotify_y})...")
    pyautogui.moveTo(spotify_x, spotify_y, duration=1)
    time.sleep(0.5)
    
    # Verify we're at the right position
    actual_x, actual_y = pyautogui.position()
    print(f"✅ Mouse position after move: ({actual_x}, {actual_y})")
    
    # Click
    print("🖱️ Clicking on Spotify icon...")
    pyautogui.click(spotify_x, spotify_y)
    
    # Wait for Spotify to open
    print("⏳ Waiting 3 seconds for Spotify to open...")
    time.sleep(3)
    
    # Take after screenshot
    print("📸 Taking after screenshot...")
    after_screenshot = pyautogui.screenshot()
    after_screenshot.save("test_after_spotify.png")
    
    print("💾 Screenshots saved as 'test_before_spotify.png' and 'test_after_spotify.png'")
    print("\n✅ Test complete! Check the screenshots to see if Spotify opened.")
    
    # Move mouse back to original position
    print(f"🔄 Moving back to original position ({current_x}, {current_y})...")
    pyautogui.moveTo(current_x, current_y, duration=1)

if __name__ == "__main__":
    main() 