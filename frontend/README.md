# Coffee Card Frontend

React dashboard for the Coffee Card concession kiosk.

## Components

The dashboard has four main components:

1. Sidebar — logo/branding, live search input, "Register customer" button, scrollable customer list, and an API health indicator at the bottom.
2. Customer panel (main area) — renders when a customer is selected. Contains a header with name/avatar/edit/archive actions, a 3-stat summary row (credits remaining, active cards, total cards), and the card grid below.
3. Card tiles — each loyalty card shown as a punch-card with filled/empty dots, a credit counter, and Redeem/Refund buttons. An "Add card" tile sits at the end of the grid.
4. Modals — two modals: 1. Register customer (name, email, phone) and the second to confirm a delete.

## Stack

| Component       | Choice            | Notes                                                    |
| --------------- | ----------------- | -------------------------------------------------------- |
| Language        | TypeScript        |                                                          |
| Framework       | React 19          | Hooks-based, no SSR requirement                          |
| Build Tool      | Vite              | Fast HMR in dev, optimised production builds             |
| Styling         | Tailwind CSS v3   | Utility-first, purged in production                      |
| Linting         | ESLint + Prettier | ESLint for rules, Prettier for formatting (no conflicts) |
| Package Manager | pnpm              |                                                          |

## Project Layout

```text
frontend/
├── public/
├── src/
│   ├── App.tsx         # Root component
│   ├── main.tsx        # Entry point — mounts App to #root
│   └── index.css       # Tailwind directives (@base, @components, @utilities)
├── eslint.config.js    # ESLint flat config with Prettier integration
├── tailwind.config.js  # Content paths for purging
├── postcss.config.js   # Required by Tailwind
├── .prettierrc         # Prettier rules
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
└── index.html
```

## Local Development

**Prerequisites:** Node 20+ and pnpm.

Install pnpm if not already available:

```bash
npm install -g pnpm
```

Install dependencies from the `frontend/` directory:

```bash
cd frontend
pnpm install
```

Start the dev server:

```bash
pnpm dev
```

The app will be available at `http://localhost:5173` with hot module replacement enabled.

## Building for Production

```bash
pnpm build
```

Output is written to `dist/`. Preview the production build locally:

```bash
pnpm preview
```

## Linting and Formatting

ESLint handles lint rules. Prettier handles formatting. `eslint-config-prettier` disables any ESLint rules that would conflict with Prettier.

```bash
# Lint
pnpm eslint src

# Format check
pnpm prettier --check src

# Format write
pnpm prettier --write src
```

Pre-commit hooks (configured at the repo root) run ruff over the `api/` directory. Frontend linting is enforced in CI via the PR workflow.
