"""
Quick test script untuk OBS connection
"""
import json
from obs_controller import OBSController

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Create controller
controller = OBSController(config)

print("=" * 50)
print("Testing OBS Connection")
print("=" * 50)

# Test 1: Check if OBS running
print("\n1. Checking if OBS is running...")
if controller.is_obs_running():
    print("   ✓ OBS process detected")
else:
    print("   ✗ OBS not running!")
    exit(1)

# Test 2: Detect WebSocket
print("\n2. Detecting OBS WebSocket...")
detected = controller.detect_obs_websocket()
if detected:
    host, port = detected
    print(f"   ✓ Found WebSocket at {host}:{port}")
else:
    print("   ✗ WebSocket not detected")

# Test 3: Auto connect
print("\n3. Trying auto-connect...")
if controller.auto_connect():
    print("   ✓ Auto-connect SUCCESS!")
    
    # Test 4: Get scenes
    print("\n4. Getting scenes from OBS...")
    scenes = controller.get_scenes()
    if scenes:
        print(f"   ✓ Found {len(scenes)} scenes:")
        for scene in scenes:
            print(f"     - {scene}")
    else:
        print("   ! No scenes found (but connection OK)")
    
    # Disconnect
    controller.disconnect()
    print("\n✓ All tests passed!")
else:
    print("   ✗ Auto-connect FAILED!")
    exit(1)
