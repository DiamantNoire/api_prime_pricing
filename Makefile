# Makefile pour gestion Docker

build:
	docker build -t api_prime_pricing .

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec api /bin/bash

prune:
	docker system prune -f
