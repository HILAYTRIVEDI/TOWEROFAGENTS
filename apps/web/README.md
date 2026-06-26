# Tower of Agents — Web Dashboard

The Next.js frontend for Tower of Agents. It serves the enterprise governance landing page and the operational dashboard where operators create workflows, upload artifacts, monitor live agent runs, and review auditable decision packets.

## Quick Start

### Via Docker (recommended)

From the repository root:

```bash
docker compose up --build
```

The dashboard will be available at `http://localhost:3000`.

### Standalone (local development)

```bash
cd apps/web
npm install
npm run dev
```

> **Note:** The dashboard expects the API at `http://localhost:8000` by default. Set `NEXT_PUBLIC_API_BASE_URL` to override.

## Technology Stack

| Layer       | Technology                |
| ----------- | ------------------------- |
| Framework   | Next.js 15 (App Router)   |
| Language    | TypeScript 5              |
| Styling     | Vanilla CSS (globals.css) |
| Runtime     | Node.js 22 Alpine         |
| Package Mgr | npm (standalone) / pnpm (monorepo) |

## Architecture

```
apps/web/
├── app/
│   ├── layout.tsx              # Root HTML layout + global CSS import
│   ├── page.tsx                # Landing page (enterprise governance marketing)
│   ├── globals.css             # Complete design system (~2000 lines)
│   ├── not-found.tsx           # 404 page
│   │
│   └── (app)/                  # Authenticated app shell (sidebar layout)
│       ├── layout.tsx          # AppShell wrapper with sidebar navigation
│       ├── dashboard/          # Workflow overview + run history
│       ├── workflows/          # Workflow CRUD, document upload, execution
│       ├── agents/             # Agent registry browser
│       ├── knowledge-base/     # Organization-shared knowledge uploads
│       ├── reports/            # Decision packet viewer
│       └── docs/               # Inline documentation
│
├── components/                 # Shared React components
│   ├── app-shell.tsx           # Sidebar + main content layout
│   ├── dashboard-tabs.tsx      # Tabbed dashboard with workflow/run lists
│   ├── document-upload.tsx     # File upload + ingestion status tracking
│   ├── workflow-create-form.tsx# New workflow creation form
│   ├── run-workflow.tsx        # Workflow execution trigger
│   ├── band-session-form.tsx   # Band room assignment
│   ├── workflow-remove-button.tsx # Workflow deletion with confirmation
│   ├── page-header.tsx         # Reusable page header with eyebrow
│   └── empty-state.tsx         # Empty state placeholder
│
├── lib/                        # Shared utilities and API client functions
│
├── public/                     # Static assets (favicon, etc.)
│
├── Dockerfile                  # Multi-stage Node 22 Alpine production build
├── package.json                # Dependencies and scripts
├── tsconfig.json               # TypeScript configuration
└── tailwind.config.ts          # Tailwind config (minimal, CSS-first approach)
```

## Pages

### Landing Page (`/`)

The public-facing enterprise marketing page with five sections:

1. **Hero** — Split-pane product interface mock with animated LangGraph node graph
2. **Contrast Matrix** — Chaos vs. TOA Standard comparison table
3. **Architecture** — Interactive system architecture diagram with hover effects
4. **Workflows** — Three-card grid with expandable API contract preview
5. **Technical Footer** — Animated terminal showing Docker setup commands

Dark mode design with `#0a0c10` background, `#00ffc8` (teal) accent, glassmorphism, micro-animations, and responsive breakpoints.

### Dashboard (`/dashboard`)

Tabbed workflow overview showing:
- Active workflow runs with status badges
- Run history with decision packet links
- Quick-action buttons for workflow creation

### Workflows (`/workflows`)

Full workflow lifecycle:
- **Create** — Name, description, and template selection
- **Detail** — Document upload, Band room assignment, execution trigger
- **Run** — Execute the specialist agent pipeline against uploaded artifacts
- **Report** — View the generated decision packet

### Agents (`/agents`)

Registry browser listing all specialist agent roles grouped by domain (HR, Sales, Engineering, Platform).

### Knowledge Base (`/knowledge-base`)

Organization-wide shared knowledge management:
- Upload documents that persist across all workflows
- Shared chunks are retrieved alongside workflow-specific evidence

### Reports (`/reports/{id}`)

Decision packet viewer showing:
- Recommendation, confidence score, and rationale
- Strengths, gaps, and interview questions
- Policy compliance notes
- Band audit message summary
- Human-review required banner

## Design System

The CSS is organized with two prefix systems in `globals.css`:

| Prefix    | Scope                                      |
| --------- | ------------------------------------------ |
| (none)    | Global tokens, typography, buttons, cards  |
| `toa-`    | Landing page dark-mode components           |

### Global Tokens

```css
--ink:        #17211b    /* Primary text */
--muted:      #667168    /* Secondary text */
--paper:      #f3f1e9    /* Page background */
--panel:      #fffdf7    /* Card backgrounds */
--line:       #d8d8cd    /* Borders */
--green:      #176b4d    /* Accent */
--green-dark: #0f4935    /* Primary actions */
--lime:       #d6f06c    /* Highlight */
--red:        #a3362b    /* Destructive */
```

### Landing Page Palette

```css
Background:    #0a0c10 (near-black)
Accent:        #00ffc8 (teal/cyan)
Surface:       rgba(255, 255, 255, 0.03-0.08)
Text:          rgba(255, 255, 255, 0.45-0.85)
Danger:        #ff4d4d / #ff6b6b (contrast matrix)
```

## Scripts

```bash
npm run dev        # Start Next.js dev server with hot reload
npm run build      # Production build
npm start          # Start production server
npm run lint       # ESLint
npm run typecheck  # TypeScript type checking (tsc --noEmit)
```

## Environment Variables

| Variable                    | Description                      | Default                   |
| --------------------------- | -------------------------------- | ------------------------- |
| `NEXT_PUBLIC_API_BASE_URL`  | Backend API URL (build-time)     | `http://localhost:8000`   |
| `NEXT_PUBLIC_DEFAULT_ORG_ID`| Temporary org scope (pre-auth)   | —                         |
| `API_BASE_URL`              | Server-side API URL (runtime)    | `http://api:8000`         |
| `HOSTNAME`                  | Bind address                     | `0.0.0.0`                 |
| `PORT`                      | Listen port                      | `3000`                    |

## Docker

Multi-stage build on `node:22-alpine`:

1. **dependencies** — `npm ci` for lockfile-exact installs
2. **builder** — `npm run build` with build-time env vars baked in
3. **runner** — Production image with `.next` output only

The `docker-compose.override.yml` replaces the production build with `npm run dev` and bind-mounts the source directory for hot reload during local development.

## Responsive Breakpoints

| Breakpoint    | Behavior                                           |
| ------------- | -------------------------------------------------- |
| `> 1024px`    | Full two-column hero, 3-col grids                  |
| `880px–1024px` | Single-column hero, stacked architecture diagram  |
| `560px–880px`  | Hidden nav links, stacked contrast table          |
| `< 560px`     | Full-width buttons, single-column everything      |
