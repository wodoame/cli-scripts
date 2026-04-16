#!/usr/bin/env bash

set -e

# Defaults
PROJECT_NAME=""
USE_REACT=false
USE_FULLSTACK=false
REACT_CREATED=false

# Help
show_help() {
  echo "Usage: $0 [project-name] [options]"
  echo ""
  echo "Creates a Django project with:"
  echo "  - uv (Python project + virtual environment)"
  echo "  - Django"
  echo "  - Django REST Framework (DRF)"
  echo "  - 'api' app with structured directories"
  echo ""
  echo "Options:"
  echo "  -h, --help       Show this help message"
  echo "  --react          Scaffold React frontend (requires setup-react in PATH)"
  echo "  --fullstack      Scaffold React + connect it with Django"
  echo ""
  echo "Examples:"
  echo "  $0 my-backend"
  echo "  $0 my-app --react"
  echo "  $0 my-app --fullstack"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
  -h | --help)
    show_help
    exit 0
    ;;
  --react)
    USE_REACT=true
    shift
    ;;
  --fullstack)
    USE_FULLSTACK=true
    USE_REACT=true
    shift
    ;;
  *)
    if [ -z "$PROJECT_NAME" ]; then
      PROJECT_NAME=$1
    else
      echo "Unknown argument: $1"
      exit 1
    fi
    shift
    ;;
  esac
done

check_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "❌ Error: Required command '$1' is not installed."
    echo "Please install $1 before running this script."
    exit 1
  fi
}

check_command uv

# Prompt if no project name
if [ -z "$PROJECT_NAME" ]; then
  read -p "Enter project name: " PROJECT_NAME
fi

echo "Creating Django project: $PROJECT_NAME"
echo ""

# Initialize project
uv init "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Install dependencies
echo "Installing Django and Django REST Framework..."
uv add django djangorestframework

# Create Django project
echo "Creating Django project (config module)..."
uv run django-admin startproject config .

# Create api app
echo "Creating api app..."
uv run python manage.py startapp api

# Create architecture folders
echo "Creating api structure..."

mkdir -p api/selectors
mkdir -p api/services
mkdir -p api/utils

touch api/selectors/__init__.py
touch api/services/__init__.py
touch api/utils/__init__.py

# Configure INSTALLED_APPS
echo "Configuring INSTALLED_APPS..."

sed -i "/INSTALLED_APPS = \[/a\    'rest_framework'," config/settings.py
sed -i "/INSTALLED_APPS = \[/a\    'api'," config/settings.py

# Wire API URLs
echo "Wiring API URLs..."

cat <<'EOF' >api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response


class HelloWorldView(APIView):
    def get(self, request):
        return Response({"message": "Hello, world!"})
EOF

cat <<'EOF' >api/urls.py
from django.urls import path
from .views import HelloWorldView

urlpatterns = [
    path("", HelloWorldView.as_view()),
]
EOF

sed -i "s/from django.urls import path/from django.urls import path, include/" config/urls.py
sed -i "/urlpatterns = \[/a\    path('api/', include('api.urls'))," config/urls.py

# React setup (optional)
if [ "$USE_REACT" = true ]; then
  echo ""
  echo "Setting up React frontend..."

  FRONTEND_NAME="frontend"

  if command -v setup-react >/dev/null 2>&1; then
    echo "Found setup-react"
    if setup-react "$FRONTEND_NAME"; then
      REACT_CREATED=true
    fi
  else
    echo "⚠️ setup-react not found in PATH. Skipping frontend setup."
  fi
fi

# Fullstack wiring
if [ "$USE_FULLSTACK" = true ] && [ "$REACT_CREATED" = true ]; then
  echo ""
  echo "Configuring fullstack integration..."

  FRONTEND_NAME="frontend"

  # Ensure os import exists
  if ! grep -q "^import os" config/settings.py; then
    sed -i "1i import os" config/settings.py
  fi

  # Fix TEMPLATES DIRS
  sed -i "s|'DIRS': \[\]|'DIRS': [os.path.join(BASE_DIR, '$FRONTEND_NAME', 'dist')]|" config/settings.py

  # Configure STATICFILES_DIRS
  if grep -q "^STATICFILES_DIRS" config/settings.py; then
    sed -i "s|^STATICFILES_DIRS = .*|STATICFILES_DIRS = [os.path.join(BASE_DIR, '$FRONTEND_NAME', 'dist', 'static')]|" config/settings.py
  else
    sed -i "/^STATIC_URL =/a\STATICFILES_DIRS = [os.path.join(BASE_DIR, '$FRONTEND_NAME', 'dist', 'static')]" config/settings.py
  fi

  # Create frontend view
  cat <<'EOF' >config/views.py
from django.views.generic import TemplateView

class FrontendView(TemplateView):
    template_name = "index.html"
EOF

  # Wire frontend route
  sed -i "1i from .views import FrontendView" config/urls.py
  sed -i "/urlpatterns = \[/a\    path('', FrontendView.as_view())," config/urls.py


  echo "✅ Fullstack integration complete."
fi

# Warning if fullstack failed
if [ "$USE_FULLSTACK" = true ] && [ "$REACT_CREATED" = false ]; then
  echo ""
  echo "⚠️ Fullstack setup requested, but React setup was not completed."
  echo "⚠️ Skipping frontend-backend integration."
fi

# Done
echo ""
echo "✅ Django project ready!"
echo "👉 Run: cd $PROJECT_NAME && uv run python manage.py runserver"
