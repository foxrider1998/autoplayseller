"""
Test Main Video + Promo Video System
"""
import json
import time
from obs_controller import OBSController
from pathlib import Path

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

controller = OBSController(config)

print("=" * 70)
print("Testing Main Video + Promo Video Autoplay System")
print("=" * 70)

# Connect
print("\n1. Connecting to OBS...")
if not controller.connect():
    print("✗ Failed to connect!")
    exit(1)
print("✓ Connected!")

# Setup main video
print("\n2. Setting up main background video...")
print(f"   Configured path: {controller.main_video_path}")

if controller.main_video_path and Path(controller.main_video_path).exists():
    if controller.setup_main_video():
        print("✓ Main video is now playing (looping in background)")
    else:
        print("✗ Failed to setup main video")
else:
    print("⚠ Main video not configured or file not found")
    print("  Set 'main_video_path' in config.json to a valid video file")
    print("  For now, skipping main video setup...")

# Test promo video
print("\n3. Testing promo video playback...")

# Find a promo video from config
promo_video = None
for keyword, data in config['comment_keywords'].items():
    video_path = data.get('video_path', '')
    if video_path and Path(video_path).exists():
        promo_video = video_path
        promo_keyword = keyword
        break

if not promo_video:
    print("⚠ No valid promo video found in config!")
    print("  Please add a video file and update config.json")
    controller.disconnect()
    exit(1)

print(f"   Using promo: {Path(promo_video).name}")
print(f"   Keyword: '{promo_keyword}'")

# Play promo video
print("\n4. Playing promo video...")
if controller.play_video(promo_video, is_promo=True):
    print("✓ Promo video playing!")
    
    # Get duration
    duration = controller.get_media_duration()
    if duration > 0:
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Will return to main video in {duration + controller.main_video_delay:.1f} seconds...")
        
        # Wait for video to finish
        print(f"\n   Waiting for promo to finish...")
        for i in range(int(duration) + 2):
            time.sleep(1)
            print(f"   {i+1}s...", end='\r')
        
        print("\n\n✓ Promo finished! Should have returned to main video")
    else:
        print("   (Could not get video duration)")
        print("   Waiting 5 seconds...")
        time.sleep(5)
else:
    print("✗ Failed to play promo video!")

# Manual return test
if controller.main_video_path:
    print("\n5. Testing manual return to main video...")
    time.sleep(2)
    controller.play_main_video()
    print("✓ Manually returned to main video")

# Disconnect
print("\n6. Disconnecting...")
controller.disconnect()

print("\n" + "=" * 70)
print("Test completed!")
print("\n📝 Summary:")
print("   1. Main video plays in loop as background")
print("   2. When comment detected → Promo video plays")
print("   3. After promo ends → Auto return to main video")
print("   4. Main video continues looping")
print("=" * 70)
