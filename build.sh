#!/usr/bin/env bash
# Build script for Render (and any similar host).
# Exit immediately if any command fails.
set -o errexit

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Compile SCSS sources to CSS
python manage.py compile_scss

# 3. Gather static files for WhiteNoise to serve
python manage.py collectstatic --no-input

# 4. Apply database migrations
python manage.py migrate
