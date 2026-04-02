#!/usr/bin/env bash
set -euo pipefail

# Format check 
black --check --target-version py310 src/

# Lint rapide et cohérent
ruff check --ignore=E402,F811,F401 src/
flake8 src/
pylint src/ --rcfile=.pylintrc --exit-zero

# Vérification de types
# Type checking with mypy (optional - remove if not needed)
# mypy src/ --ignore-missing-imports
