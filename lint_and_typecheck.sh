# Script de linting et vérification de types pour CI/CD

# Linting avec pylint
pylint src/ --rcfile=.pylintrc

# Vérification de types avec ty (typer-check)
ty src/
