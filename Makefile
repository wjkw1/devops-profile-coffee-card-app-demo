.PHONY: dev down seed

dev:
	docker compose up -d db api
	pnpm --prefix frontend dev

down:
	docker compose down

seed:
	docker compose --profile seed run --rm seed

logs:
	docker compose logs -f api
