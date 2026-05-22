.PHONY: dev down seed

dev:
	docker compose up -d --build
	pnpm --prefix frontend dev

down:
	docker compose down

seed:
	docker exec api python seed.py

logs:
	docker compose logs -f api
