#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNIVERSAL translation update script for ANY Enigma2 plugin.
Automatically finds locale directories in plugin folder or subfolders.
"""

import os
import re
import sys
import subprocess
from pathlib import Path

# ===== CONFIGURATION - CHANGE ONLY THESE 2 VALUES =====
PLUGIN_NAME = os.environ.get('PLUGIN_NAME', 'RaiPlay')
PLUGIN_ROOT = Path("usr/lib/enigma2/python/Plugins/Extensions")
# CHANGE THIS: Path to your plugin directory (without plugin name)
# ===== END CONFIGURATION =====
if '/' in PLUGIN_NAME:
    PLUGIN_NAME = Path(PLUGIN_NAME).name

# Full path to the specific plugin
PLUGIN_DIR = PLUGIN_ROOT / PLUGIN_NAME

print("=" * 70)
print(f"PLUGIN NAME FROM ENV: {os.environ.get('PLUGIN_NAME', 'NOT SET')}")
print(f"USING PLUGIN NAME: {PLUGIN_NAME}")
print("=" * 70)

# ===== 1. FIND LOCALE DIRECTORY =====
def find_locale_directory():
    """Find locale directory in plugin folder or subfolders"""
    
    print("\n1. Searching for locale directory...")
    
    # Try these possible locations in order
    possible_locations = [
        PLUGIN_DIR / "locale",                     # plugin/locale
        PLUGIN_DIR / "po",                         # plugin/po
        PLUGIN_DIR / "locales",                    # plugin/locales
        PLUGIN_DIR / "translations",               # plugin/translations
    ]
    
    # Also search in all subdirectories
    for loc in possible_locations:
        if loc.exists():
            print(f"✓ Found locale at: {loc}")
            return loc
    
    # Search recursively for any locale-like directory
    print("Searching recursively for locale directories...")
    for root, dirs, _ in os.walk(PLUGIN_DIR):
        for dir_name in dirs:
            if dir_name.lower() in ['locale', 'locales', 'po', 'translations', 'i18n']:
                locale_path = Path(root) / dir_name
                print(f"✓ Found locale at: {locale_path}")
                return locale_path
    
    print("⚠️  No locale directory found, will create: plugin/locale")
    locale_dir = PLUGIN_DIR / "locale"
    locale_dir.mkdir(parents=True, exist_ok=True)
    return locale_dir

# Initialize paths
LOCALE_DIR = find_locale_directory()
POT_FILE = LOCALE_DIR / f"{PLUGIN_NAME}.pot"

print(f"Locale directory: {LOCALE_DIR}")
print(f"POT file: {POT_FILE}")

# ===== 2. VERIFY STRUCTURE =====
def check_structure():
    """Verify that the plugin structure exists"""
    
    if not PLUGIN_DIR.exists():
        print(f"❌ ERROR: Plugin directory not found: {PLUGIN_DIR}")
        print("\nAvailable plugins in directory:")
        if PLUGIN_ROOT.exists():
            for item in PLUGIN_ROOT.iterdir():
                if item.is_dir():
                    print(f"  • {item.name}")
        sys.exit(1)
    
    print(f"✓ Plugin directory exists")
    
    # Check for setup.xml
    setup_xml = PLUGIN_DIR / "setup.xml"
    if not setup_xml.exists():
        # Try to find any setup*.xml file
        xml_files = list(PLUGIN_DIR.glob("setup*.xml"))
        if xml_files:
            print(f"✓ Found {len(xml_files)} setup XML file(s)")
        else:
            print("⚠️  No setup.xml file found")
    else:
        print(f"✓ setup.xml found")
    
    # Check Python files
    py_files = list(PLUGIN_DIR.rglob("*.py"))
    print(f"✓ {len(py_files)} Python files found")
    
    return True

# ===== 3. EXTRACT FROM SETUP.XML =====
def extract_from_xml():
    """Extract strings from setup.xml and setup.*.xml files"""
    
    strings = set()
    
    # Look for all XML setup files
    xml_files = list(PLUGIN_DIR.glob("setup*.xml"))
    
    if not xml_files:
        print("No setup XML files found")
        return []
    
    print(f"\n2. Extracting from {len(xml_files)} XML file(s)...")
    
    for xml_file in xml_files:
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            extracted = 0
            for elem in root.iter():
                for attr in ['text', 'description', 'title', 'caption', 'value']:
                    if attr in elem.attrib:
                        text = elem.attrib[attr].strip()
                        if text and text not in ["None", ""]:
                            # Exclude color codes and empty strings
                            if not re.match(r'^#[0-9a-fA-F]{6,8}$', text):
                                strings.add(text)
                                extracted += 1
            
            print(f"  {xml_file.name}: {extracted} strings")
            
        except Exception as e:
            print(f"  ERROR parsing {xml_file}: {e}")
    
    print(f"✓ Total XML strings: {len(strings)}")
    return sorted(strings)

# ===== 4. EXTRACT FROM PYTHON FILES =====
def extract_from_python():
    """Extract strings from all .py files"""
    
    py_files = list(PLUGIN_DIR.rglob("*.py"))
    
    if not py_files:
        print("No Python files found")
        return []
    
    print(f"\n3. Extracting from {len(py_files)} Python file(s)...")
    
    original_cwd = os.getcwd()
    os.chdir(PLUGIN_DIR)
    
    try:
        temp_pot = Path("temp_py.pot")
        cmd = [
            'xgettext',
            '--no-wrap',
            '-L', 'Python',
            '--from-code=UTF-8',
            '-kpgettext:1c,2',
            '-k_:1,2',
            '-k_:1',
            '--add-comments=TRANSLATORS:',
            '-d', PLUGIN_NAME,
            '-o', str(temp_pot),
        ] + [str(f.relative_to(PLUGIN_DIR)) for f in py_files]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0 and "warning" not in result.stderr.lower():
            print(f"⚠️  xgettext warning: {result.stderr[:200]}")
        
        strings = set()
        if temp_pot.exists():
            with open(temp_pot, 'r', encoding='utf-8') as f:
                content = f.read()
                for match in re.finditer(r'msgid "([^"]+)"', content):
                    text = match.group(1)
                    if text and text.strip() and text not in ['""', '']:
                        strings.add(text.strip())
            
            temp_pot.unlink()
        
        print(f"✓ Python strings: {len(strings)}")
        return sorted(strings)
        
    except Exception as e:
        print(f"ERROR with xgettext: {e}")
        return []
    finally:
        os.chdir(original_cwd)

# ===== 5. UPDATE .POT FILE =====
def update_pot_file(xml_strings, py_strings):
    """Add new strings to .pot file"""
    
    all_strings = sorted(set(xml_strings + py_strings))
    
    if not all_strings:
        print("No strings to process")
        return 0
    
    # Ensure locale directory exists
    LOCALE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Read existing strings from POT file
    existing_strings = set()
    if POT_FILE.exists():
        with open(POT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            for match in re.finditer(r'msgid "([^"]+)"', content):
                existing_strings.add(match.group(1))
    
    # Find new strings
    new_strings = [s for s in all_strings if s not in existing_strings]
    
    if not new_strings:
        print("No new strings for .pot file")
        return 0
    
    print(f"\n4. Adding {len(new_strings)} new strings to {POT_FILE.name}...")
    
    # Append to .pot file
    with open(POT_FILE, 'a', encoding='utf-8') as f:
        f.write('\n# New strings - GitHub Action\n')
        for text in new_strings:
            escaped = text.replace('"', '\\"')
            f.write(f'\nmsgid "{escaped}"\n')
            f.write('msgstr ""\n')
    
    return len(new_strings)

# ===== 6. FIND ALL .PO FILES =====
def find_all_po_files():
    """Find all .po files in locale directory and subdirectories"""
    
    po_files = []
    
    if not LOCALE_DIR.exists():
        return po_files
    
    # Search for .po files recursively
    for po_file in LOCALE_DIR.rglob("*.po"):
        # Accept either exact name or name containing plugin name
        if po_file.name == f"{PLUGIN_NAME}.po" or PLUGIN_NAME.lower() in po_file.name.lower():
            po_files.append(po_file)
    
    return po_files

# ===== 7. UPDATE ALL .PO FILES =====
def update_po_files():
    """Update all .po files with msgmerge"""
    
    if not POT_FILE.exists():
        print("ERROR: .pot file not found")
        return 0
    
    po_files = find_all_po_files()
    
    if not po_files:
        print("No .po files found")
        return 0
    
    print(f"\n5. Updating {len(po_files)} .po file(s)...")
    
    updated = 0
    for po_file in po_files:
        try:
            # Get language from directory structure
            rel_path = po_file.relative_to(LOCALE_DIR)
            lang = rel_path.parts[0] if len(rel_path.parts) > 1 else "root"
            
            print(f"  Updating {lang}...", end=" ")
            
            cmd = [
                'msgmerge',
                '--update',
                '--backup=none',
                '--no-wrap',
                '--sort-output',
                '--previous',
                str(po_file),
                str(POT_FILE)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓")
                updated += 1
            else:
                print(f"✗ {result.stderr[:100]}")
                
        except Exception as e:
            print(f"✗ {e}")
    
    return updated

# ===== 8. COMPILE .MO FILES =====
def compile_mo_files():
    """Compile all .po files to .mo files"""
    
    po_files = find_all_po_files()
    
    if not po_files:
        print("No .po files to compile")
        return 0
    
    print(f"\n6. Compiling {len(po_files)} .po file(s) to .mo...")
    
    compiled = 0
    for po_file in po_files:
        try:
            mo_file = po_file.with_suffix('.mo')
            
            # Get language for display
            rel_path = po_file.relative_to(LOCALE_DIR)
            lang = rel_path.parts[0] if len(rel_path.parts) > 1 else "root"
            
            print(f"  Compiling {lang}...", end=" ")
            
            cmd = ['msgfmt', '-o', str(mo_file), str(po_file)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                file_size = mo_file.stat().st_size
                print(f"✓ ({file_size} bytes)")
                compiled += 1
            else:
                print(f"✗")
                
        except Exception as e:
            print(f"✗ {e}")
    
    return compiled

# ===== 9. MAIN FUNCTION =====
def main():
    """Main execution function"""
    
    print("\n" + "=" * 70)
    print(f"GITHUB ACTION - TRANSLATION UPDATE FOR: {PLUGIN_NAME}")
    print("=" * 70)
    
    # 1. Check plugin structure
    if not check_structure():
        return
    
    # 2. Extract strings
    xml_strings = extract_from_xml()
    py_strings = extract_from_python()
    
    if not xml_strings and not py_strings:
        print("\nNo strings found to update")
        # Still compile existing .mo files
        compiled = compile_mo_files()
        print(f"\nCompiled {compiled} .mo files (no string updates)")
        return
    
    # 3. Update .pot file
    new_strings = update_pot_file(xml_strings, py_strings)
    
    # 4. Update .po files (even if no new strings, to ensure consistency)
    updated_po = update_po_files()
    
    # 5. Always compile .mo files
    compiled_mo = compile_mo_files()
    
    print("\n" + "=" * 70)
    print("✅ TRANSLATION UPDATE COMPLETED")
    print("-" * 70)
    print(f"Plugin:          {PLUGIN_NAME}")
    print(f"New strings:     {new_strings}")
    print(f"Updated .po:     {updated_po}")
    print(f"Compiled .mo:    {compiled_mo}")
    print(f"Locale path:     {LOCALE_DIR}")
    print("=" * 70)

if __name__ == "__main__":
    main()
