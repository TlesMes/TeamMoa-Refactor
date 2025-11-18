#!/bin/bash
set -e

echo "========================================"
echo "TeamMoa Deployment Entrypoint Script"
echo "========================================"

# Wait for database to be ready
echo "Waiting for database connection..."
until python << END
import sys
import os
import django
import environ

# Load environment variables
env = environ.Env()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TeamMoa.settings.${DJANGO_SETTINGS_MODULE:-prod}')
django.setup()

# Try database connection
from django.db import connections
from django.db.utils import OperationalError
try:
    db_conn = connections['default']
    db_conn.cursor()
    print("Database is ready!")
    sys.exit(0)
except OperationalError:
    print("Database not ready, retrying...")
    sys.exit(1)
END
do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "✅ Database connection established"

# Create logs directory if it doesn't exist
mkdir -p /app/logs
chmod 755 /app/logs
echo "✅ Logs directory created at /app/logs"

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput
echo "✅ Migrations completed"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear
echo "✅ Static files collected"

# Create superuser if it doesn't exist (optional, for first deployment)
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py shell << END
from accounts.models import User
import os

username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"✅ Superuser '{username}' created successfully")
else:
    print(f"ℹ️  Superuser '{username}' already exists")
END
fi

echo "========================================"
echo "🚀 Starting TeamMoa Application..."
echo "========================================"

# Execute the main command (Daphne or Gunicorn)
exec "$@"
