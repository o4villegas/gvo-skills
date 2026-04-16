---
name: cloudflare-deploy
description: "Scaffold and develop Cloudflare Workers projects from official templates. Use this skill whenever the user wants to create a new Cloudflare Workers project, deploy something to Cloudflare, start a new web app on Cloudflare, build an API on Workers, or mentions wanting to use Cloudflare services like D1, KV, R2, Durable Objects, or Workers AI. Also trigger when the user says things like 'deploy to the edge', 'serverless project', 'new worker', or asks about Cloudflare templates."
---

# Cloudflare Deploy

Scaffold new Cloudflare Workers projects from the official template catalog, then continue into development.

## How it works

When the user wants a new Cloudflare project, guide them through template selection, scaffold it, and keep building.

## Step 1: Understand what they want to build

Ask the user to describe what they're building. Listen for cues about:
- **Frontend framework preference** (React, Astro, Next.js, Remix, React Router)
- **Backend needs** (API, database, auth, real-time)
- **Storage requirements** (SQL database, key-value, object/file storage)
- **Special features** (AI, chat, containers, workflows, payments)

If the description is vague (e.g. "I want to build a web app"), ask one focused follow-up question to narrow it down. Don't interrogate — one question is enough to pick the right template.

## Step 2: Fetch the latest templates

Before recommending anything, fetch the current template list from the official Cloudflare docs to make sure you're working with up-to-date information:

```
WebFetch: https://developers.cloudflare.com/workers/get-started/quickstarts/
```

Parse the page to extract the template names, descriptions, and `npm create cloudflare@latest` commands. Cross-reference with the catalog in `references/templates.md` — the fetched page is the source of truth, but the reference file has cost and architecture notes that the docs page doesn't include.

If the fetch fails, fall back to `references/templates.md` — it's a solid snapshot, just might not have the very latest additions.

## Step 3: Recommend templates (cost-aware)

Narrow down to **2-3 best-fit templates** and present them as a short comparison. For each option, explain:
- What it gives you out of the box
- Which Cloudflare services it uses
- **Cost implications** — this matters

### Cost hierarchy (cheapest to most expensive)

When two templates could both work, prefer the cheaper one unless the user's requirements clearly need the more expensive option.

1. **Static/Assets only** — practically free (Workers free tier: 100k requests/day)
2. **KV** — very cheap reads, good for config/session data (free tier: 100k reads/day)
3. **D1** — cheap serverless SQL, great default for most database needs (free tier: 5M rows read/day, 100k writes/day)
4. **R2** — object storage, no egress fees (free tier: 10GB storage, 1M reads/month)
5. **Durable Objects** — powerful but costs add up with scale (per-request + wall-clock duration billing). Only recommend when the user genuinely needs coordination, state, or real-time features
6. **Hyperdrive + external DB** — adds external database costs on top of Workers costs. Only recommend when the user already has a Postgres/MySQL database they need to connect to
7. **Workers AI** — usage-based model inference pricing. Recommend only when the user explicitly wants AI features

### Example recommendation format

> Based on what you described, here are the best fits:
>
> 1. **d1-template** — Lightweight API with D1 (serverless SQLite). Cheapest database option, generous free tier. Good if you're starting fresh with no existing database.
>
> 2. **react-router-hono-fullstack-template** — Full-stack with React Router + Hono + shadcn/ui. More setup but you get a complete app with a nice UI layer. You'd add D1 yourself for storage.
>
> 3. **chanfana-openapi-template** — API-first with auto-generated OpenAPI docs, D1, and Vitest testing. Great if you want a well-structured backend with built-in documentation.
>
> I'd suggest **#1** if you want to start simple, or **#2** if you need a frontend too. Which one speaks to you?

Always end the recommendation with a clear question asking the user to pick.

## Step 4: Ask about project location

Once the user picks a template, ask:

> Where should I create the project? I can set it up in the current directory, or in a specific folder — just give me a name or path.

## Step 5: Scaffold the project

Run the template command:

```bash
npm create cloudflare@latest -- --template=cloudflare/templates/<template-name> <project-path>
```

If the command prompts for interactive input (project name, git init, etc.), handle it. After scaffolding completes, read through the generated project structure so you understand what was created.

## Step 6: Continue development

After scaffolding, you're now in development mode. The project is set up — start building what the user described. This means:

- Read the generated `wrangler.toml` / `wrangler.jsonc` to understand the configuration
- Look at the entry point and understand the template's patterns
- Start implementing the user's actual features

Don't just scaffold and stop. The user came to build something — keep going.

## Step 7: Deploy check

At a natural stopping point (a feature works, the app is in a usable state), ask the user:

> Want me to deploy this to Cloudflare now, or keep developing locally first?

If they want to deploy:
1. Make sure `wrangler` is available (`npx wrangler --version`)
2. Check if they're logged in (`npx wrangler whoami`)
3. If not logged in, tell them to run `npx wrangler login` and wait
4. Deploy with `npx wrangler deploy`
5. Share the deployed URL

If they want to keep developing, just keep building. Ask again later when appropriate.
