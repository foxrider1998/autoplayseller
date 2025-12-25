"""
Test video playback di OBS
"""
import json
import time
from obs_controller import OBSController
from pathlib import Path

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

controller = OBSController(config)

print("=" * 60)
print("Testing Video Playback in OBS")
print("=" * 60)

# Connect
print("\n1. Connecting to OBS...")
if not controller.connect():
    print("✗ Failed to connect!")
    exit(1)

print("✓ Connected!")

# Get scenes
print("\n2. Available scenes:")
scenes = controller.get_scenes()
for scene in scenes:
    print(f"   - {scene}")
    sources = controller.get_sources(scene)
    if sources:
        print(f"     Sources: {', '.join(sources)}")
    else:
        print(f"     (no sources)")

# Create test video file if not exists
test_video = Path("videos/test.mp4")
if not test_video.exists():
    print(f"\n⚠ Test video not found: {test_video}")
    print("  Please create 'videos' folder and add a test.mp4 file")
    print("  Or use any existing video file")
    
    # Try to find any video file
    videos_dir = Path("videos")
    if videos_dir.exists():
        video_files = list(videos_dir.glob("*.mp4")) + list(videos_dir.glob("*.mov"))
        if video_files:
            test_video = video_files[0]
            print(f"\n  Using: {test_video}")
        else:
            controller.disconnect()
            exit(1)
    else:
        controller.disconnect()
        exit(1)

# Play video
print(f"\n3. Testing video playback...")
print(f"   Video: {test_video}")

if controller.play_video(str(test_video)):
    print("\n✓ Video should be playing in OBS now!")
    print("  Check your OBS window - you should see the video")
    
    # Wait a bit
    print("\n  Waiting 5 seconds...")
    time.sleep(5)
    
    # Stop video
    print("\n4. Stopping video...")
    controller.stop_video()
    print("✓ Video stopped!")
else:
    print("\n✗ Failed to play video!")

# Disconnect
controller.disconnect()
print("\n" + "=" * 60)
print("Test completed!")
