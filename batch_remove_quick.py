#!/usr/bin/env python3
"""
Quick Batch Background Removal
Uses Quick Export to avoid dialogs
"""

import subprocess
import time
from pathlib import Path
import shutil

def posix_to_hfs(posix_path):
    """Convert POSIX path to HFS path for AppleScript"""
    script = f'''
    set posixPath to "{posix_path}"
    set hfsPath to POSIX file posixPath as string
    return hfsPath
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip()

def setup_quick_export(output_folder):
    """Set up Quick Export preferences to use PNG and specific folder"""
    script = f'''
    tell application "System Events"
        tell process "Adobe Photoshop 2025"
            -- Open Preferences
            keystroke "," using command down
            delay 1
            
            -- Navigate to Export preferences (might need adjustment)
            -- Click on Export in the sidebar
            click row 8 of outline 1 of scroll area 1 of window 1
            delay 0.5
            
            -- Set Quick Export Format to PNG
            click pop up button 1 of window 1
            delay 0.5
            keystroke "PNG"
            keystroke return
            delay 0.5
            
            -- Set location to "Ask Where to Export"
            click pop up button 2 of window 1
            delay 0.5
            keystroke "Ask"
            keystroke return
            delay 0.5
            
            -- Click OK
            click button "OK" of window 1
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", script], capture_output=True)

def process_image_quick(input_path, output_path):
    """Process image with Quick Export method"""
    
    input_hfs = posix_to_hfs(str(input_path))
    
    # Open file
    open_script = f'''
    tell application "Adobe Photoshop 2025"
        activate
        open file "{input_hfs}"
    end tell
    '''
    
    result = subprocess.run(["osascript", "-e", open_script], capture_output=True, text=True)
    if result.returncode != 0:
        return False
    
    time.sleep(2)
    
    # Convert background layer
    convert_script = '''
    tell application "Adobe Photoshop 2025"
        tell current document
            if exists background layer then
                set background layer's name to "Layer 0"
            end if
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", convert_script], capture_output=True)
    time.sleep(0.5)
    
    # Select Subject
    select_script = '''
    tell application "System Events"
        tell process "Adobe Photoshop 2025"
            click menu item "Subject" of menu "Select" of menu bar item "Select" of menu bar 1
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", select_script], capture_output=True)
    time.sleep(2)  # Wait for AI selection
    
    # Invert selection
    invert_script = '''
    tell application "System Events"
        tell process "Adobe Photoshop 2025"
            click menu item "Inverse" of menu "Select" of menu bar item "Select" of menu bar 1
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", invert_script], capture_output=True)
    time.sleep(0.5)
    
    # Delete background
    delete_script = '''
    tell application "System Events"
        tell process "Adobe Photoshop 2025"
            key code 51  -- Delete key
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", delete_script], capture_output=True)
    time.sleep(0.5)
    
    # Deselect
    deselect_script = '''
    tell application "System Events"
        tell process "Adobe Photoshop 2025"
            keystroke "d" using command down
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", deselect_script], capture_output=True)
    time.sleep(0.5)
    
    # Trim
    trim_script = '''
    tell application "System Events"
        tell process "Adobe Photoshop 2025"
            click menu item "Trim..." of menu "Image" of menu bar item "Image" of menu bar 1
            delay 0.5
            keystroke return  -- OK with default settings
        end tell
    end tell
    '''
    subprocess.run(["osascript", "-e", trim_script], capture_output=True)
    time.sleep(1)
    
    # Use Save a Copy instead of Export
    save_script = f'''
    tell application "Adobe Photoshop 2025"
        tell current document
            -- Create PNG save options
            set pngOptions to {{class:PNG save options, compression:6}}
            
            -- Save a copy as PNG
            save in file "{posix_to_hfs(str(output_path))}" as PNG with options pngOptions with copying
        end tell
    end tell
    '''
    
    result = subprocess.run(["osascript", "-e", save_script], capture_output=True, text=True)
    time.sleep(1)
    
    # Close without saving
    close_script = '''
    tell application "Adobe Photoshop 2025"
        close current document saving no
    end tell
    '''
    subprocess.run(["osascript", "-e", close_script], capture_output=True)
    
    return output_path.exists()

def main():
    print("=== Quick Batch Background Removal ===")
    print("Saves directly without dialogs")
    print()
    
    # Get folders
    input_folder = input("Enter input folder path: ").strip().strip('"')
    output_folder = input("Enter output folder path: ").strip().strip('"')
    
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    
    if not input_path.exists():
        print("❌ Input folder does not exist!")
        return
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp'}
    image_files = [f for f in input_path.iterdir() 
                   if f.is_file() and f.suffix.lower() in image_extensions]
    
    print(f"\n📁 Found {len(image_files)} image files")
    
    if not image_files:
        print("❌ No image files found!")
        return
    
    # Show files
    print("\n📋 Files to process:")
    for i, f in enumerate(image_files[:5]):
        print(f"  • {f.name}")
    if len(image_files) > 5:
        print(f"  ... and {len(image_files) - 5} more")
    
    # Confirm
    confirm = input("\nProceed? (y/N): ").strip().lower()
    if confirm != 'y':
        return
    
    print("\n⚠️  Make sure Terminal has accessibility permissions:")
    print("   System Preferences > Security & Privacy > Privacy > Accessibility")
    input("   Press Enter when ready...")
    
    # Open Photoshop
    print("\n🎨 Opening Photoshop...")
    subprocess.run(["osascript", "-e", 'tell application "Adobe Photoshop 2025" to activate'])
    time.sleep(3)
    
    # Process files
    processed = 0
    failed = 0
    skipped = 0
    
    print("\n🚀 Processing images...")
    print("-" * 50)
    
    for i, input_file in enumerate(image_files, 1):
        output_file = output_path / f"{input_file.stem}.png"
        
        if output_file.exists():
            print(f"[{i}/{len(image_files)}] ⏭️  Skipping {input_file.name} (exists)")
            skipped += 1
            continue
        
        print(f"[{i}/{len(image_files)}] 🔄 Processing {input_file.name}...", end='', flush=True)
        
        try:
            success = process_image_quick(input_file, output_file)
            
            if success:
                print(" ✅")
                processed += 1
            else:
                print(" ❌")
                failed += 1
        except Exception as e:
            print(f" ❌ ({str(e)[:30]}...)")
            failed += 1
        
        time.sleep(0.5)
    
    print("-" * 50)
    print(f"\n📊 Results:")
    print(f"  ✅ Processed: {processed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  📁 Total: {len(image_files)}")
    
    if processed > 0:
        print(f"\n🎉 Output saved to: {output_path}")

if __name__ == "__main__":
    main()