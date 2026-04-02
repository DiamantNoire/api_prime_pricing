#!/usr/bin/env bash
set -euo pipefail

# Format check 
black --check --target-version py310 src/

# Lint rapide et cohérent
ruff check --ignore=E402,F811,F401 src/
flake8 src/ --max-line-length=120 --ignore=E402,E501,F401,F811
pylint src/ --rcfile=.pylintrc --exit-zero

# Vérification de types
# Type checking with mypy (optional - remove if not needed)
# mypy src/ --ignore-missing-imports
