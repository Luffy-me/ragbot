# Convenience commands

.PHONY: up down logs backend-dev frontend-dev sample-pdf

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

sample-pdf:
	cd backend && python scripts/generate_sample_pdf.py

backend-dev:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend-dev:
	cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
