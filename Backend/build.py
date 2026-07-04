"""Vercel build step (see pyproject.toml): apply database migrations before the new code goes live.

Production builds migrate the production database. Preview builds migrate only when they have their own Neon branch
(PREVIEW_DATABASE_URL); otherwise they would share production's DATABASE_URL, and an unmerged branch must never
change the production schema. Vercel runs collectstatic itself.
"""
import os
import subprocess
import sys

env = os.environ.get('VERCEL_ENV', 'local')
if env == 'production' or (env == 'preview' and os.environ.get('PREVIEW_DATABASE_URL')):
    print(f'Applying migrations to the {env} database...', flush=True)
    sys.exit(subprocess.call([sys.executable, 'manage.py', 'migrate', '--noinput']))
print(f'Skipping migrations for a {env} build.')
