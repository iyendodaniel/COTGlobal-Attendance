.PHONY: build run stop logs shell migrate createsuperuser clean help

# Docker commands
build:
	docker compose build

runbuild:
	docker compose up -d --build

run:
	docker compose up -d

stop:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec web python manage.py shell

# Django management commands (run inside container)
migrate:
	docker compose exec web python manage.py migrate

createsuperuser:
	docker compose exec web python manage.py createsuperuser

collectstatic:
	docker compose exec web python manage.py collectstatic --noinput

# Development
dev:
	python manage.py runserver

dev-migrate:
	python manage.py migrate

# Cleanup
clean:
	docker compose down -v --rmi local
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Help
help:
	@echo "Available commands:"
	@echo "  make build          - Build Docker image"
	@echo "  make run            - Start containers in background"
	@echo "  make stop           - Stop containers"
	@echo "  make logs           - View container logs"
	@echo "  make shell          - Open Django shell in container"
	@echo "  make migrate        - Run migrations in container"
	@echo "  make createsuperuser - Create Django superuser"
	@echo "  make collectstatic  - Collect static files"
	@echo "  make dev            - Run local development server"
	@echo "  make dev-migrate    - Run migrations locally"
	@echo "  make clean          - Remove containers, volumes, and cache"

