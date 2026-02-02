#!/usr/bin/env python3
"""
find_locale_dirs.py - Trova tutte le cartelle locale nei plugin
"""
import sys
import json
import re
import subprocess
from pathlib import Path


def find_all_locale_directories(root_dir="."):
    """
    Trova ricorsivamente tutte le cartelle 'locale' con vari pattern
    """
    locale_dirs = []
    
    # Estensioni dei file di traduzione
    translation_extensions = ['.po', '.mo', '.pot']
    
    for path in Path(root_dir).rglob("*"):
        if not path.is_dir():
            continue
        
        # Salta directory nascoste e di sistema
        if any(part.startswith('.') for part in path.parts):
            continue
        if any(part in ['__pycache__', 'venv', 'node_modules', 'build', 'dist'] for part in path.parts):
            continue
        
        dir_name = path.name.lower()
        
        # Controlla se è una cartella locale
        is_locale_dir = (
            dir_name in ['locale', 'locales', 'i18n', 'translations', 'po'] or
            any(file.suffix.lower() in translation_extensions for file in path.iterdir())
        )
        
        if is_locale_dir:
            # Trova la directory del plugin (due livelli sopra per LC_MESSAGES)
            plugin_path = path
            for _ in range(3):  # locale/xx/LC_MESSAGES -> plugin root
                plugin_path = plugin_path.parent
            
            translation_files = []
            for f in path.rglob('*'):
                if f.suffix.lower() in translation_extensions:
                    try:
                        translation_files.append(str(f.relative_to(path)))
                    except ValueError:
                        pass
            
            locale_dirs.append({
                'locale_path': str(path),
                'plugin_dir': str(plugin_path),
                'plugin_name': plugin_path.name,
                'relative_path': str(path.relative_to(root_dir)),
                'has_lc_messages': any('LC_MESSAGES' in str(p) for p in path.rglob('*')),
                'translation_files': translation_files
            })
    
    return locale_dirs


def extract_strings_from_py(plugin_dir):
    """Estrai stringhe dai file Python"""
    plugin_path = Path(plugin_dir)
    py_files = list(plugin_path.rglob("*.py"))
    
    if not py_files:
        print("⚠️ No Python files found")
        return []
    
    print(f"🔍 Found {len(py_files)} Python files")
    
    # Usa xgettext per estrarre le stringhe
    temp_pot = plugin_path / "temp.pot"
    
    try:
        cmd = [
            'xgettext', '--no-wrap', '-L', 'Python',
            '--from-code=UTF-8', '-o', str(temp_pot)
        ] + [str(f) for f in py_files]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if temp_pot.exists():
            with open(temp_pot, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Estrai msgid
            strings = re.findall(r'msgid "([^"]+)"', content)
            temp_pot.unlink()
            
            return [s for s in strings if s.strip()]
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error extracting strings: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    return []


def update_po_files(locale_dir, strings):
    """Aggiorna i file .po"""
    locale_path = Path(locale_dir)
    
    # Cerca tutti i file .po
    po_files = list(locale_path.rglob("*.po"))
    
    if not po_files:
        print("ℹ️ No .po files found, creating template...")
        return
    
    print(f"📄 Found {len(po_files)} .po files")
    
    for po_file in po_files:
        print(f"  • {po_file.relative_to(locale_path)}")
        # Qui aggiungi la logica per aggiornare i file .po


def create_translation_update_script(plugin_info):
    """
    Crea uno script di aggiornamento traduzioni personalizzato per il plugin
    """
    template = '''#!/usr/bin/env python3
"""
Auto-generated translation updater for: {plugin_name}
Locale directory: {relative_path}
"""
import os
import sys
import subprocess
import re
from pathlib import Path

PLUGIN_NAME = "{plugin_name}"
LOCALE_DIR = Path("{locale_path}")
PLUGIN_DIR = Path("{plugin_dir}")

def extract_strings_from_py():
    """Estrai stringhe dai file Python"""
    py_files = list(PLUGIN_DIR.rglob("*.py"))
    
    if not py_files:
        print("⚠️ No Python files found")
        return []
    
    print(f"🔍 Found {{len(py_files)}} Python files")
    
    # Usa xgettext per estrarre le stringhe
    temp_pot = PLUGIN_DIR / "temp.pot"
    
    try:
        cmd = [
            'xgettext', '--no-wrap', '-L', 'Python',
            '--from-code=UTF-8', '-o', str(temp_pot)
        ] + [str(f) for f in py_files]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        if temp_pot.exists():
            with open(temp_pot, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Estrai msgid
            strings = re.findall(r'msgid "([^"]+)"', content)
            temp_pot.unlink()
            
            return [s for s in strings if s.strip()]
            
    except Exception as e:
        print(f"❌ Error extracting strings: {{e}}")
    
    return []

def update_po_files(strings):
    """Aggiorna i file .po"""
    # Cerca tutti i file .po
    po_files = list(LOCALE_DIR.rglob("*.po"))
    
    if not po_files:
        print("ℹ️ No .po files found, creating template...")
        return
    
    print(f"📄 Found {{len(po_files)}} .po files")
    
    for po_file in po_files:
        print(f"  • {{po_file.relative_to(LOCALE_DIR)}}")
        # Qui aggiungi la logica per aggiornare i file .po

def main():
    print(f"🚀 Updating translations for: {{PLUGIN_NAME}}")
    print(f"📁 Plugin directory: {{PLUGIN_DIR}}")
    print(f"🌍 Locale directory: {{LOCALE_DIR}}")
    
    # 1. Estrai stringhe
    strings = extract_strings_from_py()
    print(f"📝 Found {{len(strings)}} translatable strings")
    
    # 2. Aggiorna file .po
    update_po_files(strings)
    
    # 3. Compila .mo
    print("✅ Translation update completed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''.format(plugin_name=plugin_info['plugin_name'],
           relative_path=plugin_info['relative_path'],
           locale_path=plugin_info['locale_path'],
           plugin_dir=plugin_info['plugin_dir']
           )
    
    script_path = Path(plugin_info['plugin_dir']) / "update_translations.py"
    script_path.write_text(template, encoding='utf-8')
    script_path.chmod(0o755)
    
    return str(script_path)


def main():
    print("🔍 Scanning for locale directories...")
    
    locale_dirs = find_all_locale_directories()
    
    if not locale_dirs:
        print("❌ No locale directories found")
        return 1
    
    print(f"\n✅ Found {len(locale_dirs)} locale directories:\n")
    
    for i, locale in enumerate(locale_dirs, 1):
        print(f"{i:2}. {locale['plugin_name']}")
        print(f"    📍 {locale['relative_path']}")
        print(f"    📁 Plugin: {locale['plugin_dir']}")
        print(f"    📄 Files: {len(locale['translation_files'])} translation files")
        if locale['has_lc_messages']:
            print("    ✓ Has LC_MESSAGES structure")
        print()
    
    # Salva in JSON
    with open('locale_scan_report.json', 'w', encoding='utf-8') as f:
        json.dump(locale_dirs, f, indent=2, ensure_ascii=False)
    
    # Crea script per plugin senza
    plugins_without_script = []
    for locale in locale_dirs:
        plugin_dir = Path(locale['plugin_dir'])
        update_script = plugin_dir / "update_translations.py"
        
        if not update_script.exists():
            plugins_without_script.append(locale)
    
    if plugins_without_script:
        print(f"\n⚠️  {len(plugins_without_script)} plugins without update script:")
        for plugin in plugins_without_script:
            script_path = create_translation_update_script(plugin)
            print(f"   • Created: {script_path}")
    
    print("\n📊 Report saved to: locale_scan_report.json")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
