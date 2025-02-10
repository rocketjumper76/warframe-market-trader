import PyInstaller.__main__
import os

def build_exe():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define paths
    icon_path = os.path.join(current_dir, 'assets', 'icon.ico')
    
    # Ensure the icon exists
    if not os.path.exists(icon_path):
        print(f"Warning: Icon file not found at {icon_path}")
        icon_path = None
    
    # Build command
    command = [
        'main.py',                # Your main script
        '--name=WarframeTrader',  # Name of the executable
        '--windowed',             # Don't show console window
        '--clean',                # Clean cache before building
        '--noconfirm',           # Replace existing build without asking
        '--add-data=src;src',    # Include your source files
        '--add-data=assets;assets',  # Include assets
        f'--workpath={os.path.join(current_dir, "build")}',  # Build files location
        f'--distpath={os.path.join(current_dir, "dist")}',   # Output location
    ]
    
    # Add icon if it exists
    if icon_path:
        command.append(f'--icon={icon_path}')
    
    # Run PyInstaller
    print("Starting build process...")
    PyInstaller.__main__.run(command)
    print("Build complete! Check the 'dist/WarframeTrader' folder for your application.")

if __name__ == "__main__":
    build_exe() 