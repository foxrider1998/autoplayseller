"""
Build Script for AutoPlay Seller
Alternative Python script untuk build executable
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_step(step, message):
    """Print formatted step"""
    print(f"\n[{step}] {message}")
    print("-" * 60)

def check_dependencies():
    """Check and install required dependencies"""
    print_step("1/6", "Checking build dependencies")
    
    required = {
        'pyinstaller': 'PyInstaller',
        'pillow': 'Pillow',
        'obs-websocket-py': 'obs-websocket-py',
        'watchdog': 'watchdog',
        'psutil': 'psutil'
    }
    
    missing = []
    for package, name in required.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✓ {name} installed")
        except ImportError:
            print(f"  ✗ {name} not found")
            missing.append(package)
    
    if missing:
        print(f"\nInstalling missing packages: {', '.join(missing)}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
        print("  ✓ All dependencies installed")
    
    return True

def clean_build():
    """Clean previous build artifacts"""
    print_step("2/6", "Cleaning previous build")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  ✓ Removed {dir_name}/")
    
    print("  ✓ Clean complete")

def create_icon():
    """Create or check icon file"""
    print_step("3/6", "Checking icon file")
    
    icon_path = Path("icon.ico")
    if icon_path.exists():
        print(f"  ✓ Using existing icon.ico")
        return str(icon_path)
    else:
        print(f"  ⚠ No icon.ico found, will use default")
        return None

def build_executable():
    """Build executable using PyInstaller"""
    print_step("4/6", "Building executable")
    print("  This may take 2-5 minutes...\n")
    
    # Check if spec file exists
    spec_file = Path("AutoPlaySeller.spec")
    
    if spec_file.exists():
        # Use spec file
        cmd = [
            'pyinstaller',
            '--clean',
            'AutoPlaySeller.spec'
        ]
    else:
        # Build without spec file
        cmd = [
            'pyinstaller',
            '--name=AutoPlaySeller',
            '--windowed',  # No console
            '--onedir',  # One directory (easier to add files)
            '--clean',
            '--add-data=config.json:.',
            '--add-data=comments.txt:.',
            '--add-data=videos:videos',
            '--hidden-import=obswebsocket',
            '--hidden-import=watchdog.observers',
            '--hidden-import=watchdog.events',
            '--hidden-import=psutil',
            'main.py'
        ]
        
        # Add icon if exists
        if os.path.exists('icon.ico'):
            cmd.extend(['--icon=icon.ico'])
    
    try:
        subprocess.check_call(cmd)
        print("\n  ✓ Build successful!")
        return True
    except subprocess.CalledProcessError:
        print("\n  ✗ Build failed!")
        return False

def copy_additional_files():
    """Copy documentation and other files"""
    print_step("5/6", "Copying additional files")
    
    dist_dir = Path("dist/AutoPlaySeller")
    if not dist_dir.exists():
        print("  ✗ Distribution directory not found!")
        return False
    
    # Files to copy
    files_to_copy = [
        'README.md',
        'UPDATE_CONFIG_EDITOR.md',
        'AUTO_DETECT_OBS.md',
        'QUICKSTART_CONFIG_EDITOR.md',
        'config.json'
    ]
    
    for file_name in files_to_copy:
        src = Path(file_name)
        if src.exists():
            dst = dist_dir / file_name
            shutil.copy2(src, dst)
            print(f"  ✓ Copied {file_name}")
    
    # Ensure videos directory exists
    videos_dir = dist_dir / "videos"
    videos_dir.mkdir(exist_ok=True)
    
    # Copy README to videos folder
    videos_readme = Path("videos/README.md")
    if videos_readme.exists():
        shutil.copy2(videos_readme, videos_dir / "README.md")
        print(f"  ✓ Copied videos/README.md")
    
    print("  ✓ Additional files copied")
    return True

def create_distribution_package():
    """Create ZIP package for distribution"""
    print_step("6/6", "Creating distribution package")
    
    dist_dir = Path("dist/AutoPlaySeller")
    if not dist_dir.exists():
        print("  ✗ Distribution directory not found!")
        return False
    
    zip_name = "AutoPlaySeller-Portable"
    
    try:
        # Remove old zip if exists
        if os.path.exists(f"{zip_name}.zip"):
            os.remove(f"{zip_name}.zip")
        
        # Create ZIP
        shutil.make_archive(zip_name, 'zip', 'dist', 'AutoPlaySeller')
        
        zip_path = Path(f"{zip_name}.zip")
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        
        print(f"  ✓ Package created: {zip_name}.zip")
        print(f"  ✓ Size: {size_mb:.1f} MB")
        
        return True
    except Exception as e:
        print(f"  ✗ Failed to create package: {e}")
        return False

def main():
    """Main build process"""
    print("=" * 60)
    print("  AutoPlay Seller - Build Executable")
    print("=" * 60)
    
    try:
        # Run build steps
        if not check_dependencies():
            return 1
        
        clean_build()
        create_icon()
        
        if not build_executable():
            return 1
        
        copy_additional_files()
        create_distribution_package()
        
        # Success message
        print("\n" + "=" * 60)
        print("  Build Complete!")
        print("=" * 60)
        print(f"\n✓ Executable: dist/AutoPlaySeller/AutoPlaySeller.exe")
        print(f"✓ Package: AutoPlaySeller-Portable.zip")
        print(f"\nNext steps:")
        print(f"1. Test: dist/AutoPlaySeller/AutoPlaySeller.exe")
        print(f"2. Distribute: Share AutoPlaySeller-Portable.zip")
        print(f"3. Users just extract and run - No Python needed!")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n✗ Build cancelled by user")
        return 1
    except Exception as e:
        print(f"\n\n✗ Build failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
