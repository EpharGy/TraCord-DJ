# Always up-to-date list of internal cogs for main.py
import os

def _find_internal_cogs():
    cogs = []
    cogs_dir = os.path.dirname(__file__)
    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py') and not filename.startswith('_') and filename != '__init__.py':
            cogs.append(f"cogs.{filename[:-3]}")
    return cogs

INTERNAL_COGS = _find_internal_cogs()
