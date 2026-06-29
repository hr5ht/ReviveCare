"""Vercel build step (see pyproject.toml): apply database migrations before the new code goes live.

Only production builds migrate. Preview builds share the production DATABASE_URL unless they are given their own,
and an unmerged branch must never change the production schema. Vercel runs collectstatic itself.
"""
import os
import subprocess
import sys

if os.environ.get('VERCEL_ENV') == 'production':
    print('Applying migrations...', flush=True)
    sys.exit(subprocess.call([sys.executable, 'manage.py', 'migrate', '--noinput']))
print(f"Skipping migrations for a {os.environ.get('VERCEL_ENV', 'local')} build.")
