"""
Test Script - AutoPlay Seller
Script untuk test semua komponen sebelum production
"""
import sys
import json
from pathlib import Path

def check_dependencies():
    """Check apakah semua dependencies terinstall"""
    print("Checking dependencies...")
    
    dependencies = [
        'tkinter',
        'watchdog',
        'obswebsocket'
    ]
    
    missing = []
    for dep in dependencies:
        try:
            if dep == 'tkinter':
                import tkinter
            elif dep == 'watchdog':
                import watchdog
            elif dep == 'obswebsocket':
                import obswebsocket
            print(f"  ✓ {dep}")
        except ImportError:
            print(f"  ✗ {dep} - NOT FOUND")
            missing.append(dep)
    
    if missing:
        print(f"\n⚠ Missing dependencies: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✓ All dependencies OK!")
    return True


def check_config():
    """Check config.json"""
    print("\nChecking configuration...")
    
    config_path = Path("config.json")
    if not config_path.exists():
        print("  ✗ config.json not found!")
        print("  Run: python generate_config.py")
        return False
    
    print("  ✓ config.json exists")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Check required keys
        required = ['obs_settings', 'comment_keywords', 'comment_source']
        for key in required:
            if key in config:
                print(f"  ✓ {key}")
            else:
                print(f"  ✗ {key} - MISSING")
                return False
        
        # Check keywords count
        num_keywords = len(config['comment_keywords'])
        print(f"  ✓ {num_keywords} keywords configured")
        
        return True
    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON: {e}")
        return False


def check_videos():
    """Check video files"""
    print("\nChecking video files...")
    
    videos_dir = Path("videos")
    if not videos_dir.exists():
        print("  ✗ videos/ folder not found!")
        return False
    
    print("  ✓ videos/ folder exists")
    
    # Check for video files
    video_files = list(videos_dir.glob("*.mp4"))
    print(f"  Found {len(video_files)} MP4 files")
    
    if len(video_files) == 0:
        print("  ⚠ No video files found!")
        print("  Please add video files to videos/ folder")
        return False
    
    # List first 5
    print("\n  Video files:")
    for vf in video_files[:5]:
        size_mb = vf.stat().st_size / (1024 * 1024)
        print(f"    - {vf.name} ({size_mb:.1f} MB)")
    
    if len(video_files) > 5:
        print(f"    ... and {len(video_files) - 5} more")
    
    return True


def test_comment_detector():
    """Test comment detector module"""
    print("\nTesting comment detector...")
    
    try:
        from comment_detector import Comment, CommentMatcher
        
        # Load config
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        matcher = CommentMatcher(config['comment_keywords'])
        
        # Test comments
        test_cases = [
            Comment("user1", "keranjang 1"),
            Comment("user2", "keranjang 5"),
            Comment("user3", "mau beli dong"),
            Comment("user4", "keranjang1"),  # tanpa spasi
        ]
        
        for comment in test_cases:
            match = matcher.match(comment)
            if match:
                print(f"  ✓ '{comment.text}' → {match['matched_keyword']}")
            else:
                print(f"  - '{comment.text}' → no match")
        
        print("  ✓ Comment detector OK!")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_obs_controller():
    """Test OBS controller (without connecting)"""
    print("\nTesting OBS controller...")
    
    try:
        from obs_controller import OBSController
        
        # Load config
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        controller = OBSController(config)
        
        print(f"  ✓ Controller initialized")
        print(f"    Host: {controller.host}")
        print(f"    Port: {controller.port}")
        print(f"    Video Source: {controller.video_source_name}")
        
        print("  ⚠ Not connecting to OBS in test mode")
        print("  ℹ Start OBS manually and test connection in app")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_gui():
    """Test GUI import"""
    print("\nTesting GUI...")
    
    try:
        import tkinter as tk
        
        # Test basic window
        root = tk.Tk()
        root.withdraw()  # Hide window
        
        print("  ✓ Tkinter OK")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    print("=" * 50)
    print("  AutoPlay Seller - Test Suite")
    print("=" * 50)
    print()
    
    tests = [
        ("Dependencies", check_dependencies),
        ("Configuration", check_config),
        ("Video Files", check_videos),
        ("Comment Detector", test_comment_detector),
        ("OBS Controller", test_obs_controller),
        ("GUI", test_gui),
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n✗ {name} test failed: {e}")
            results[name] = False
        print()
    
    # Summary
    print("=" * 50)
    print("  Test Summary")
    print("=" * 50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {name}")
    
    print()
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Ready to use.")
        print("\nNext steps:")
        print("1. Start OBS Studio")
        print("2. Enable WebSocket server in OBS")
        print("3. Run: python main.py")
        print("4. Click 'Connect to OBS'")
        print("5. Click 'Start Monitoring'")
        print("6. Add comments to comments.txt to test")
        return 0
    else:
        print("\n⚠ Some tests failed. Please fix issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
