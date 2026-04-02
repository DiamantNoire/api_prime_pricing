#!/usr/bin/env bash
set -euo pipefail

# Format check (ne modifie pas le code en CI)
black --check src tests

# Lint rapide et cohérent
ruff check src tests
flake8 src tests
pylint src/ --rcfile=.pylintrc

# Vérification de types
ty src/
