# Always up-to-date list of internal cogs for main.py
import os

def _find_internal_cogs():
    cogs = []
    cogs_dir = os.path.dirname(__file__)
    # Scan cogs/ directory
    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py') and not filename.startswith('_') and filename != '__init__.py':
            cogs.append(f"cogs.{filename[:-3]}")
    # Scan extra_cogs/ directory (flat only, include all .py files)
    extra_cogs_dir = os.path.abspath(os.path.join(cogs_dir, '..', 'extra_cogs'))
    if os.path.isdir(extra_cogs_dir):
        for filename in os.listdir(extra_cogs_dir):
            full_path = os.path.join(extra_cogs_dir, filename)
            if os.path.isfile(full_path) and filename.endswith('.py'):
                cogs.append(f"extra_cogs.{filename[:-3]}")
    return cogs

INTERNAL_COGS = _find_internal_cogs()
