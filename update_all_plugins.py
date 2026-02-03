#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAIN SCRIPT - Processes ALL Enigma2 plugins in the repository.
Finds all locale directories and updates translations automatically.
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict


def find_all_plugins(root_dir: str = ".") -> List[Dict]:
    """
    Find ALL plugins in the repository by searching for locale directories.
    Returns list of plugins with their info.
    """
    plugins = []
    root_path = Path(root_dir)

    print("🔍 Scanning repository for plugins...")

    # Search for all locale directories
    for locale_dir in root_path.rglob("*"):
        if not locale_dir.is_dir():
            continue

        dir_name = locale_dir.name.lower()

        # Check if this is a locale directory
        is_locale = any(pattern in dir_name for pattern in [
            'locale', 'locales', 'po', 'translations', 'i18n'
        ])

        if is_locale:
            # Determine plugin directory (2-3 levels up from locale)
            plugin_dir = locale_dir
            for _ in range(3):  # Try going up 3 levels
                plugin_dir = plugin_dir.parent

            # Verify it's a plugin (has Python files or setup.xml)
            has_py = any(plugin_dir.rglob("*.py"))
            has_xml = any(plugin_dir.rglob("setup*.xml"))

            if has_py or has_xml:
                plugin_info = {
                    'plugin_dir': str(plugin_dir),
                    'plugin_name': plugin_dir.name,
                    'locale_dir': str(locale_dir),
                    'has_py': has_py,
                    'has_xml': has_xml,
                    'py_files': len(list(plugin_dir.rglob("*.py"))),
                    'xml_files': len(list(plugin_dir.rglob("setup*.xml")))
                }

                # Avoid duplicates
                if not any(p['plugin_dir'] == plugin_info['plugin_dir']
                           for p in plugins):
                    plugins.append(plugin_info)

    # Also find plugins without locale directories (create them)
    for potential_plugin in root_path.rglob("plugin.py"):
        plugin_dir = potential_plugin.parent
        plugin_name = plugin_dir.name

        # Check if already in list
        if not any(p['plugin_dir'] == str(plugin_dir) for p in plugins):
            plugins.append({
                'plugin_dir': str(plugin_dir),
                'plugin_name': plugin_name,
                'locale_dir': str(plugin_dir / "locale"),  # Will create
                'has_py': True,
                'has_xml': any(plugin_dir.rglob("setup*.xml")),
                'py_files': len(list(plugin_dir.rglob("*.py"))),
                'xml_files': len(list(plugin_dir.rglob("setup*.xml")))
            })

    return plugins


def process_single_plugin(plugin_info: Dict) -> Dict:
    """
    Process translations for a single plugin.
    This function contains the logic from your universal script.
    """
    results = {
        'plugin_name': plugin_info['plugin_name'],
        'success': False,
        'new_strings': 0,
        'updated_po': 0,
        'compiled_mo': 0,
        'errors': []
    }

    plugin_dir = Path(plugin_info['plugin_dir'])
    locale_dir = Path(plugin_info['locale_dir'])

    print(f"\n{'=' * 60}")
    print(f"📦 Processing: {plugin_info['plugin_name']}")
    print(f"📁 Directory: {plugin_dir}")
    print(f"{'=' * 60}")

    # Ensure locale directory exists
    if not locale_dir.exists():
        print(f"⚠️  Creating locale directory: {locale_dir}")
        locale_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Change to plugin directory
        original_cwd = os.getcwd()
        os.chdir(plugin_dir)

        # 2. Extract strings from XML
        xml_strings = extract_from_xml(plugin_dir)

        # 3. Extract strings from Python
        py_strings = extract_from_python(plugin_dir)

        # 4. Update POT file
        pot_file = locale_dir / f"{plugin_info['plugin_name']}.pot"
        results['new_strings'] = update_pot_file(
            xml_strings,
            py_strings,
            pot_file,
            locale_dir,
            plugin_info['plugin_name'])

        # 5. Update PO files
        results['updated_po'] = update_po_files(pot_file, locale_dir)

        # 6. Compile MO files
        results['compiled_mo'] = compile_mo_files(locale_dir)

        # 7. Return to original directory
        os.chdir(original_cwd)

        results['success'] = True

    except Exception as e:
        results['errors'].append(str(e))
        print(f"❌ Error processing {plugin_info['plugin_name']}: {e}")

    return results


def extract_from_xml(plugin_dir: Path) -> List[str]:
    """Extract strings from setup XML files"""
    strings = set()
    xml_files = list(plugin_dir.glob("setup*.xml"))

    if not xml_files:
        return []

    try:
        import xml.etree.ElementTree as ET

        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                for elem in root.iter():
                    for attr in [
                        'text',
                        'description',
                        'title',
                        'caption',
                        'value',
                            'summary']:
                        if attr in elem.attrib:
                            text = elem.attrib[attr].strip()
                            if text and not re.match(
                                    r'^#[0-9a-fA-F]{6,8}$', text):
                                strings.add(text)
            except Exception as e:
                print(f"⚠️  Could not parse {xml_file.name}: {e}")

    except ImportError:
        print("⚠️  xml.etree.ElementTree not available")

    return sorted(strings)


def extract_from_python(plugin_dir: Path) -> List[str]:
    """Extract strings from Python files using xgettext"""
    py_files = list(plugin_dir.rglob("*.py"))

    if not py_files:
        return []

    strings = set()
    temp_pot = plugin_dir / "temp.pot"

    try:
        rel_paths = [str(f.relative_to(plugin_dir)) for f in py_files]

        cmd = [
            'xgettext',
            '--no-wrap',
            '-L', 'Python',
            '--from-code=UTF-8',
            '-o', str(temp_pot),
        ] + rel_paths[:20]  # Limit to 20 files to avoid command line limits

        subprocess.run(cmd, capture_output=True, text=True)

        if temp_pot.exists():
            with open(temp_pot, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for match in re.finditer(r'msgid "([^"]+)"', content):
                    text = match.group(1)
                    if text and text.strip():
                        strings.add(text.strip())

            temp_pot.unlink()

    except Exception as e:
        print(f"⚠️  Error extracting Python strings: {e}")

    return sorted(strings)


def update_pot_file(xml_strings: List[str], py_strings: List[str],
                    pot_file: Path, locale_dir: Path, plugin_name: str) -> int:
    """Update or create POT file"""
    all_strings = sorted(set(xml_strings + py_strings))

    if not all_strings:
        return 0

    locale_dir.mkdir(parents=True, exist_ok=True)

    # Read existing strings
    existing_strings = set()
    if pot_file.exists():
        try:
            with open(pot_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for match in re.finditer(r'msgid "([^"]+)"', content):
                    existing_strings.add(match.group(1))
        except Exception:
            pass

    # Find new strings
    new_strings = [s for s in all_strings if s not in existing_strings]

    if not new_strings:
        return 0

    # Write to POT file
    mode = 'a' if pot_file.exists() else 'w'
    with open(pot_file, mode, encoding='utf-8') as f:
        if mode == 'w':
            f.write(f'''# {plugin_name} translations
# Copyright (C) {plugin_name} Team
#
msgid ""
msgstr ""
"Project-Id-Version: {plugin_name}\\n"
"POT-Creation-Date: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"

''')

        for text in new_strings:
            escaped = text.replace('"', '\\"')
            f.write(f'msgid "{escaped}"\n')
            f.write('msgstr ""\n\n')

    return len(new_strings)


def update_po_files(pot_file: Path, locale_dir: Path) -> int:
    """Update all PO files with msgmerge"""
    if not pot_file.exists():
        return 0

    po_files = list(locale_dir.rglob("*.po"))

    if not po_files:
        return 0

    updated = 0
    for po_file in po_files:
        try:
            cmd = [
                'msgmerge',
                '--update',
                '--backup=none',
                '--no-wrap',
                str(po_file),
                str(pot_file)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                updated += 1

        except Exception:
            pass

    return updated


def compile_mo_files(locale_dir: Path) -> int:
    """Compile PO files to MO files"""
    po_files = list(locale_dir.rglob("*.po"))

    if not po_files:
        return 0

    compiled = 0
    for po_file in po_files:
        try:
            mo_file = po_file.with_suffix('.mo')
            cmd = ['msgfmt', '-o', str(mo_file), str(po_file)]
            subprocess.run(cmd, capture_output=True, text=True)

            if mo_file.exists():
                compiled += 1

        except Exception:
            pass

    return compiled


def main():
    """Main function - Process ALL plugins"""
    print("UNIVERSAL PLUGIN TRANSLATION UPDATER")
    print("=" * 60)

    # Find all plugins
    plugins = find_all_plugins()

    if not plugins:
        print("No plugins found in repository")
        return 1

    print("Found {} plugin(s):".format(len(plugins)))
    for i, plugin in enumerate(plugins, 1):
        print("  {:2}. {}".format(i, plugin['plugin_name']))
        print("      Directory: {}".format(plugin['plugin_dir']))
        print("      {} Python files, {} XML files".format(
            plugin['py_files'], plugin['xml_files']))

    # Process each plugin
    print("\nProcessing {} plugin(s)...".format(len(plugins)))

    all_results = []
    successful = 0

    for plugin in plugins:
        result = process_single_plugin(plugin)
        all_results.append(result)

        if result['success']:
            successful += 1
            status = "SUCCESS"
        else:
            status = "FAILED"

        print("{} {}: {} new strings, {} PO updated, {} MO compiled".format(
            status, result['plugin_name'],
            result['new_strings'], result['updated_po'], result['compiled_mo']
        ))

    # Generate report
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print("Total plugins: {}".format(len(plugins)))
    print("Successful: {}".format(successful))
    print("Failed: {}".format(len(plugins) - successful))

    # Save detailed report
    report = {
        'timestamp': subprocess.check_output(['date', '+%Y-%m-%d %H:%M:%S'], text=True).strip(),
        'total_plugins': len(plugins),
        'successful': successful,
        'failed': len(plugins) - successful,
        'details': all_results
    }

    with open('translation_update_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\nDetailed report saved to: translation_update_report.json")

    return 0 if successful > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
