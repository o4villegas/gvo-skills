# Cloudflare Workers Template Catalog

This is a snapshot of the official templates. The skill fetches the live list from the docs, but this file provides cost/architecture context the docs page doesn't include.

**Source of truth**: https://developers.cloudflare.com/workers/get-started/quickstarts/

**Scaffold command**: `npm create cloudflare@latest -- --template=cloudflare/templates/<name>`

---

## Table of Contents

- [Frontend / Full-Stack](#frontend--full-stack)
- [API / Backend](#api--backend)
- [Database](#database)
- [Real-Time / Stateful](#real-time--stateful)
- [AI](#ai)
- [Storage](#storage)
- [Infrastructure / Platform](#infrastructure--platform)
- [Auth](#auth)
- [Specialized](#specialized)

---

## Frontend / Full-Stack

### astro-blog-starter-template
- **Description**: Personal website, blog, or portfolio with Astro
- **Services**: Workers Assets
- **Cost tier**: Very low (static assets + edge compute)
- **Best for**: Content sites, blogs, portfolios
- **Not for**: Apps needing a database or API

### next-starter-template
- **Description**: Full-stack web app with Next.js
- **Services**: Workers, Workers Assets
- **Cost tier**: Low-medium (SSR adds compute)
- **Best for**: Teams already using Next.js, SEO-heavy apps
- **Note**: Uses OpenNext adapter for Cloudflare compatibility

### react-router-starter-template
- **Description**: Full-stack web app with React Router 7
- **Services**: Workers, Workers Assets
- **Cost tier**: Low-medium
- **Best for**: SPAs and full-stack React apps without heavy backend needs

### react-router-hono-fullstack-template
- **Description**: Full-stack with Hono backend, React Router frontend, shadcn/ui + Tailwind
- **Services**: Workers, Workers Assets
- **Cost tier**: Low-medium
- **Best for**: Complete apps that need both a nice UI and a proper API layer
- **Standout**: Comes with shadcn/ui components pre-configured

### remix-starter-template
- **Description**: Full-stack web app with Remix
- **Services**: Workers, Workers Assets
- **Cost tier**: Low-medium
- **Best for**: Remix users, form-heavy apps

### vite-react-template
- **Description**: React app with Vite and Hono backend
- **Services**: Workers, Workers Assets
- **Cost tier**: Low-medium
- **Best for**: Lightweight React apps with an API

### saas-admin-template
- **Description**: Admin dashboard with Astro, shadcn/ui, and Cloudflare stack
- **Services**: Workers, Workers Assets, D1, KV, R2 (varies)
- **Cost tier**: Medium (uses multiple services)
- **Best for**: Internal tools, admin panels, SaaS dashboards

### microfrontend-template
- **Description**: Route requests to different Workers by path pattern
- **Services**: Multiple Workers
- **Cost tier**: Medium (multiple Workers = multiple billing units)
- **Best for**: Large teams splitting a frontend across teams
- **Not for**: Simple apps — this is an architecture pattern, not a starter

---

## API / Backend

### chanfana-openapi-template
- **Description**: Backend API with Hono + Chanfana + D1 + Vitest
- **Services**: Workers, D1
- **Cost tier**: Low (D1 free tier is generous)
- **Best for**: API-first projects that want auto-generated OpenAPI docs
- **Standout**: Comes with testing setup (Vitest)

### nodejs-http-server-template
- **Description**: Node.js HTTP server on Workers
- **Services**: Workers
- **Cost tier**: Very low
- **Best for**: Porting existing Node.js HTTP servers to the edge

---

## Database

### d1-template
- **Description**: Cloudflare D1 (serverless SQLite) starter
- **Services**: Workers, D1
- **Cost tier**: Low (free tier: 5M reads/day, 100k writes/day)
- **Best for**: Any project needing a SQL database without external dependencies
- **Recommended as default database option**

### d1-starter-sessions-api-template
- **Description**: D1 with Sessions API for read replication
- **Services**: Workers, D1
- **Cost tier**: Low
- **Best for**: Read-heavy apps that need low-latency global reads
- **Note**: Sessions API enables reading from replicas closer to the user

### postgres-hyperdrive-template
- **Description**: Connect to external PostgreSQL via Hyperdrive
- **Services**: Workers, Hyperdrive
- **Cost tier**: Medium-high (external Postgres costs + Hyperdrive)
- **Best for**: Projects with an existing PostgreSQL database
- **Not for**: New projects — use D1 instead unless you need Postgres-specific features

### mysql-hyperdrive-template
- **Description**: Connect to external MySQL via Hyperdrive
- **Services**: Workers, Hyperdrive
- **Cost tier**: Medium-high (external MySQL costs + Hyperdrive)
- **Best for**: Projects with an existing MySQL database
- **Not for**: New projects — use D1 instead

### react-postgres-fullstack-template
- **Description**: Book library app with React + Postgres
- **Services**: Workers, Workers Assets, Hyperdrive
- **Cost tier**: Medium-high
- **Best for**: Full-stack apps that need Postgres specifically

### react-router-postgres-ssr-template
- **Description**: SSR book library with React Router + Postgres
- **Services**: Workers, Workers Assets, Hyperdrive
- **Cost tier**: Medium-high
- **Best for**: SSR apps needing Postgres

---

## Real-Time / Stateful

### durable-chat-template
- **Description**: Real-time chat with Durable Objects + PartyKit
- **Services**: Workers, Durable Objects
- **Cost tier**: Medium-high (DO billing: per-request + wall-clock duration)
- **Best for**: Chat apps, collaborative features, real-time sync
- **Cost note**: Durable Objects charge for both requests AND time the object is active. For high-traffic chat, costs can scale quickly

### multiplayer-globe-template
- **Description**: Real-time visitor globe with Durable Objects + PartyKit
- **Services**: Workers, Durable Objects
- **Cost tier**: Medium-high
- **Best for**: Real-time visualization, collaborative/multiplayer experiences

### hello-world-do-template
- **Description**: Basic Durable Objects example
- **Services**: Workers, Durable Objects
- **Cost tier**: Medium
- **Best for**: Learning Durable Objects, prototyping stateful logic

---

## AI

### llm-chat-app-template
- **Description**: Chat app powered by Workers AI
- **Services**: Workers, Workers AI
- **Cost tier**: Usage-based (model inference pricing)
- **Best for**: AI chatbots, LLM-powered features
- **Cost note**: Workers AI is billed per token/inference. Cost depends heavily on model choice and traffic

### text-to-image-template
- **Description**: Generate images from text prompts
- **Services**: Workers, Workers AI
- **Cost tier**: Usage-based (image generation is more expensive than text)
- **Best for**: AI image generation features

### nlweb-template
- **Description**: NL Web components with Workers
- **Services**: Workers, Workers AI
- **Cost tier**: Usage-based
- **Best for**: Natural language web interfaces

---

## Storage

### r2-explorer-template
- **Description**: Google Drive-like interface for R2 buckets
- **Services**: Workers, Workers Assets, R2
- **Cost tier**: Low-medium (R2 has no egress fees, 10GB free storage)
- **Best for**: File management UIs, internal tools for R2 content
- **Standout**: No egress fees — much cheaper than S3 for serving files

### to-do-list-kv-template
- **Description**: To-do list with KV storage and Remix
- **Services**: Workers, Workers Assets, KV
- **Cost tier**: Very low (KV free tier: 100k reads/day)
- **Best for**: Simple apps with key-value storage needs

---

## Infrastructure / Platform

### containers-template
- **Description**: Container-enabled Worker
- **Services**: Workers, Containers
- **Cost tier**: Variable (container runtime costs)
- **Best for**: Workloads that need a full container runtime (e.g., running binaries, specific runtimes)

### worker-publisher-template
- **Description**: Deploy Workers to a Dispatch Namespace via SDK
- **Services**: Workers, Workers for Platforms
- **Cost tier**: Variable
- **Best for**: Building platforms that let users deploy their own Workers

### workers-for-platforms-template
- **Description**: Website hosting platform with Workers for Platforms
- **Services**: Workers, Workers for Platforms
- **Cost tier**: Variable
- **Best for**: Building a hosting service, multi-tenant platforms

### workflows-starter-template
- **Description**: Cloudflare Workflows with real-time status updates
- **Services**: Workers, Workflows
- **Cost tier**: Low (Workflows are priced per step execution)
- **Best for**: Multi-step background jobs, orchestration, retryable pipelines

### workers-builds-notifications-template
- **Description**: Build status notifications to Slack/Discord via webhooks
- **Services**: Workers, Event Subscriptions
- **Cost tier**: Very low
- **Best for**: CI/CD notification pipelines

---

## Auth

### openauth-template
- **Description**: OpenAuth server on Workers
- **Services**: Workers
- **Cost tier**: Low
- **Best for**: Adding authentication to your Cloudflare apps
- **Note**: Self-hosted auth — no external auth service costs

---

## Specialized

### x402-proxy-template
- **Description**: Payment-gated proxy using x402 protocol + JWT
- **Services**: Workers
- **Cost tier**: Low (Worker itself is cheap; payment processing is external)
- **Best for**: Monetized APIs, paywalled content

### cli
- **Description**: CLI for developing templates
- **Services**: Workers
- **Cost tier**: N/A (development tool)
- **Best for**: Template authors, not end users
- **Note**: This is a meta-template for building other templates — rarely what users want
