# cloudflare-deploy

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that helps you scaffold and develop Cloudflare Workers projects from official templates — with cost-aware recommendations.

Instead of scrolling through 30+ templates trying to figure out which one fits your project, just describe what you want to build. The skill narrows it down to 2-3 best options, explains the trade-offs (especially cost), and scaffolds the project for you.

## What it does

### 1. Smart template selection

You say something like:

> "init a cloudflare project, i need a saas app with a dashboard"

The skill:
- Fetches the **latest templates** from [Cloudflare's official docs](https://developers.cloudflare.com/workers/get-started/quickstarts/) so recommendations are always up to date
- Narrows down to **2-3 best-fit templates** based on what you described
- Presents a **cost comparison** so you don't accidentally pick an expensive option when a cheaper one would work

### 2. Cost-aware recommendations

The skill always prefers the cheapest option that meets your needs. It follows this cost hierarchy:

| Tier | Service | Free Tier |
|------|---------|-----------|
| Cheapest | Static/Workers Assets | 100k requests/day |
| Very cheap | KV (key-value) | 100k reads/day |
| Cheap | D1 (serverless SQLite) | 5M rows read/day, 100k writes/day |
| Low-medium | R2 (object storage) | 10GB storage, 1M reads/month, zero egress |
| Medium-high | Durable Objects | Per-request + wall-clock billing |
| Expensive | Hyperdrive + external DB | External database costs on top |
| Usage-based | Workers AI | Per-token/inference pricing |

For example, if you need a database, the skill recommends **D1** (free, serverless SQLite) instead of Postgres via Hyperdrive — unless you explicitly have an existing Postgres database you need to connect to.

### 3. Project scaffolding

Once you pick a template, the skill:
- Asks where to create the project (current directory or a specific folder)
- Runs `npm create cloudflare@latest -- --template=cloudflare/templates/<template-name>`
- Reads through the generated project to understand the structure

### 4. Continues into development

The skill doesn't stop at scaffolding. After the project is created, it:
- Reads `wrangler.toml` / `wrangler.jsonc` to understand the configuration
- Starts implementing the features you described
- Keeps building until you have something working

### 5. Deployment

At a natural stopping point, the skill asks if you want to deploy:
- Checks if `wrangler` is available and you're logged in
- Deploys with `npx wrangler deploy`
- Shares the live URL

## Supported templates

The skill covers **30+ official Cloudflare templates** across these categories:

| Category | Templates | Example |
|----------|-----------|---------|
| **Frontend / Full-Stack** | Astro, Next.js, React Router, Remix, Vite+React, SaaS Admin | `astro-blog-starter-template` |
| **API / Backend** | Chanfana OpenAPI, Node.js HTTP | `chanfana-openapi-template` |
| **Database** | D1, D1 Sessions, Postgres Hyperdrive, MySQL Hyperdrive | `d1-template` |
| **Real-Time** | Durable Chat, Multiplayer Globe, Durable Objects | `durable-chat-template` |
| **AI** | LLM Chat, Text-to-Image, NL Web | `llm-chat-app-template` |
| **Storage** | R2 Explorer, KV To-Do List | `r2-explorer-template` |
| **Infrastructure** | Containers, Workers for Platforms, Workflows | `workflows-starter-template` |
| **Auth** | OpenAuth | `openauth-template` |

## Installation

### Option 1: Clone to your skills directory

```bash
git clone https://github.com/kemalabuteliyte/cloudflare-deploy.git ~/.claude/skills/cloudflare-deploy
```

### Option 2: Manual copy

1. Download or clone this repo
2. Copy the `cloudflare-deploy` folder into `~/.claude/skills/`:

```bash
cp -r cloudflare-deploy ~/.claude/skills/cloudflare-deploy
```

### Verify installation

After installing, start a new Claude Code session. The skill should appear in your available skills list. You can verify by asking Claude something like:

> "init a new cloudflare project"

If the skill is loaded, Claude will ask what you want to build and present template recommendations with cost info — instead of just listing generic options.

## Usage examples

Here are some prompts that trigger the skill:

```
"init a web project for cloudflare, i will build a company webpage"
```
→ Recommends Astro (cheapest, static), asks if you need a blog or dynamic features

```
"i want to deploy a project to cloudflare, its gonna be a saas app with user accounts"
```
→ Recommends saas-admin-template or react-router-hono-fullstack-template with D1

```
"set up a cloudflare worker project, i need an api that stores data"
```
→ Recommends d1-template or chanfana-openapi-template, highlights D1 free tier

```
"build me a real-time chat app on cloudflare"
```
→ Recommends durable-chat-template, warns about Durable Objects cost scaling

```
"deploy a next.js app to cloudflare"
```
→ Goes straight to next-starter-template, explains OpenNext adapter

## Project structure

```
cloudflare-deploy/
├── SKILL.md                    # Skill definition (triggers + instructions)
├── references/
│   └── templates.md            # Template catalog with cost/architecture notes
└── evals/
    └── evals.json              # Test cases for skill validation
```

- **SKILL.md** — The main skill file. Contains the 7-step workflow (understand → fetch → recommend → locate → scaffold → develop → deploy) and the cost hierarchy.
- **references/templates.md** — A categorized catalog of all 30+ templates with cost tiers, "best for" notes, and warnings. The skill cross-references this with live data from Cloudflare's docs page.
- **evals/evals.json** — Test prompts used to validate the skill works correctly.

## How it triggers

The skill activates when you mention anything related to:
- Creating a new Cloudflare Workers project
- Deploying to Cloudflare
- Starting a new web app on Cloudflare
- Building an API on Workers
- Using Cloudflare services (D1, KV, R2, Durable Objects, Workers AI)
- Phrases like "deploy to the edge", "serverless project", "new worker"
- Asking about Cloudflare templates

## License

MIT
