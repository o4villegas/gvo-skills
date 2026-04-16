---
name: runpod-workflow
description: "Build Docker images, push to Docker Hub, and create production-ready RunPod serverless endpoints with full settings including flashboot, standby workers, and scaling. Use when: create runpod endpoint, new endpoint, deploy new serverless, spin up new runpod, new runpod service, runpod workflow, build docker image, push to docker hub."
---

# RunPod Endpoint Creation Workflow

Create production-ready serverless endpoints using MCP tools + REST patch for advanced settings.

## Auth

RunPod API Key: `rpa_DVGCVRX6ZOINLJNT02EVNU2AFIYXNNOYHYJ2DLSN1x7ps3`
Docker Hub namespace: `gvo555`
User ID: `user_387e3LlpGJwOqIuJGo29wvxqiZV`

Use this key for any direct REST API calls (the MCP server handles its own auth separately).

## Entry Router

Determine which workflow to execute based on the user's request:

| User intent | Route to | Example triggers |
|-------------|----------|-----------------|
| Create a new endpoint from scratch | **New Endpoint Workflow** (Steps 1-5 below) | "create a runpod endpoint", "deploy new serverless", "spin up a new runpod" |
| Update an existing endpoint's image | **Image Update / Redeploy** (section below) | "update smokescan to v13", "push new image to endpoint", "redeploy with latest" |
| Build and push a Docker image only | **Step 1 only** (then stop) | "build docker image", "push to docker hub" |

If unclear, ask the user: "Are you creating a new endpoint or updating an existing one?"

---

## New Endpoint Workflow (Steps 1-5)

Execute these 5 steps in order. Do NOT skip steps. Confirm each step succeeded before proceeding.

### Step 1: Build & Push Docker Image

**Skip this step** if the user already has an image on Docker Hub. To check, run:
```bash
docker manifest inspect <image-name> 2>&1 | head -1
```
If it returns JSON (not "no such manifest"), the image exists — skip to Step 2. Otherwise, build it.

**Prerequisites:** Docker Desktop WSL integration must be enabled. Verify with:
```bash
docker info --format '{{.ServerVersion}}'
```

**1a. Locate or create the Dockerfile**

The project directory should contain a `Dockerfile`. If not, use this minimal template for a Python handler:

```dockerfile
FROM runpod/pytorch:2.1.0-py3.10-cuda12.1.1-devel-ubuntu22.04
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-u", "handler.py"]
```

For vLLM endpoints, skip the Dockerfile — use the pre-built `runpod/worker-vllm:stable-cuda12.1.0` image and go to Step 2.

For more Dockerfile patterns (model-baked, TGI, network volumes), see `~/.claude/skills/runpod-deployment/reference/templates.md`.

**1b. Build the image (linux/amd64)**

Always build for `linux/amd64` — RunPod GPUs are x86 only:

```bash
docker build --platform linux/amd64 -t gvo555/<image-name>:<tag> <build-context-path>
```

Tag conventions (match existing `gvo555/` images):
- Use semantic versions for production: `v1.0.0`, `v2.1.0`
- Use `latest` alongside the versioned tag
- Use descriptive suffixes for variants: `v3-gpu-failfast`, `v5-memory-opt`

**1c. Push to Docker Hub**

```bash
docker push gvo555/<image-name>:<tag>
```

If not logged in, prompt the user to run `! docker login` interactively.

**1d. Verify the push**

```bash
docker manifest inspect gvo555/<image-name>:<tag> --verbose 2>&1 | head -5
```

Confirm the manifest exists on the remote registry before proceeding.

**1e. Record outputs for downstream steps**

Save these values — they feed directly into Steps 2-3:

```bash
# Image name (required for Step 3: imageName)
IMAGE_NAME="gvo555/<image-name>:<tag>"

# Image size (informs Step 3: containerDiskInGb — must be at least 2x image size)
docker image inspect gvo555/<image-name>:<tag> --format '{{.Size}}' | awk '{printf "%.1f GB\n", $1/1024/1024/1024}'
```

If the image is >15GB, the preset's default `containerDiskInGb` may be too small — override it in Step 2.

### Step 2: Select Preset & Gather Config

Ask the user which preset to start from (see `reference/presets.md`):

| Preset | GPUs | Cost/hr | Best For |
|--------|------|---------|----------|
| **heavy-analysis** | H100, A100 80GB | $2.69-2.99 | Vision models, multi-image analysis, large models |
| **light-inference** | RTX 4090, RTX 5090 | $0.59 | Document analysis, single-image, <24GB VRAM tasks |
| **vllm-endpoint** | H100, A100 80GB | $2.69-2.99 | OpenAI-compatible LLM serving via vLLM |
| **budget-dev** | RTX 4090 | $0.44 | Development/testing, cold starts acceptable |
| **custom** | User-specified | Varies | Non-standard configurations |

Gather from user:
1. **Endpoint name** — descriptive, append `-fb` if flashboot enabled
2. **Docker image** — from Step 1, or user-provided existing image (`namespace/image:tag`)
3. **Environment variables** — at minimum `HF_TOKEN` if using HuggingFace models
4. **Any preset overrides** — GPU types, worker counts, scaling, etc.

### Step 3: Create Template

Read `reference/presets.md` now — extract the values for the user's chosen preset before calling the MCP tool.

Use MCP tool `mcp__runpod__create-template` with these exact parameters:

```
name:             "<endpoint-name>-template"
imageName:        "gvo555/<image-name>:<tag>"       ← from Step 1e or user-provided
containerDiskInGb: 150                               ← from preset; override if image size from Step 1e > half this value
isServerless:     true
volumeMountPath:  "/workspace"
env:              [                                  ← array of key-value objects
                    {"key": "HF_TOKEN", "value": "<user's HF token>"},
                    {"key": "MODEL_NAME", "value": "<if applicable>"}
                  ]
```

**Concrete example** (heavy-analysis preset, smokescan image):
```
name:             "smokescan-analysis-template"
imageName:        "gvo555/smokescan-analysis:v13"
containerDiskInGb: 150
isServerless:     true
volumeMountPath:  "/workspace"
env:              [{"key": "HF_TOKEN", "value": "hf_abc123"}]
```

**Save the returned `templateId`** — needed for Step 4.

**Validation:** The MCP tool returns a JSON response. Verify it contains an `id` field (the templateId). If the call returns an error:
- `imageName` not found → verify the image exists on Docker Hub (`docker manifest inspect <imageName>`)
- `containerDiskInGb` too small → increase to at least 2x image size
- `env` format wrong → must be an array of `{"key": "...", "value": "..."}` objects, not a flat object

### Step 4: Create Endpoint

Use MCP tool `mcp__runpod__create-endpoint` with these exact parameters:

```
templateId:   "<templateId from Step 3>"
name:         "<endpoint-name>"
gpuTypeIds:   ["NVIDIA H100 PCIe", "NVIDIA A100 80GB PCIe"]   ← from preset
gpuCount:     1                                                 ← from preset
workersMin:   0                                                 ← from preset
workersMax:   2                                                 ← from preset
```

**Concrete example** (heavy-analysis preset):
```
templateId:   "abc123def456"
name:         "smokescan-analysis-fb"
gpuTypeIds:   ["NVIDIA H100 PCIe", "NVIDIA H100 80GB HBM3", "NVIDIA H100 NVL", "NVIDIA A100 80GB PCIe", "NVIDIA A100-SXM4-80GB"]
gpuCount:     1
workersMin:   0
workersMax:   2
```

**Validation:** The MCP tool returns a JSON response. Verify it contains an `id` field (the endpointId).

**Save the returned `endpointId`** — needed for Steps 4b and 5.

Then IMMEDIATELY use MCP tool `mcp__runpod__update-endpoint` to set scaling:

```
endpointId:   "<endpointId from above>"
idleTimeout:  800                          ← from preset (seconds)
scalerType:   "QUEUE_DELAY"
scalerValue:  4                            ← from preset
```

### Step 5: Patch Advanced Settings

Run the patch script for fields the MCP server doesn't expose:

```bash
bash ~/.claude/skills/runpod-workflow/scripts/patch_endpoint.sh \
  "<endpointId>" \
  "<flashboot: true|false>" \
  "<workersStandby: number>" \
  "<executionTimeoutMs: number>"
```

Example for heavy-analysis preset:
```bash
bash ~/.claude/skills/runpod-workflow/scripts/patch_endpoint.sh \
  "endpoint_id_here" \
  true \
  2 \
  600000
```

**Validation:** Confirm the response shows the patched values. If it fails:
- Check `RUNPOD_API_KEY` is set in environment
- Verify the endpoint ID is correct
- Check the REST API base URL is `rest.runpod.io` (not `api.runpod.io`)

## Post-Creation Verification

After all 5 steps, call `mcp__runpod__list-endpoints` with `includeTemplate: true, includeWorkers: true`.

In the response JSON, verify each field against the values saved during Steps 2-5:

| Check | Field in response | Expected value |
|-------|-------------------|----------------|
| Endpoint name | `name` | matches Step 2 endpoint name |
| Template attached | `templateId` | matches Step 3 templateId |
| GPU types | `gpuTypeIds` | matches preset GPU list from Step 4 |
| Scaler type | `scalerType` | `"QUEUE_DELAY"` (from Step 4b) |
| Scaler value | `scalerValue` | matches preset (usually `4`) |
| Idle timeout | `idleTimeout` | matches preset (from Step 4b) |
| Flashboot | `flashboot` | `true` if requested in Step 5 |
| Workers min/max | `workersMin`, `workersMax` | matches preset from Step 4 |
| Workers standby | `workersStandby` | matches Step 5 value |

If any field doesn't match, stop and fix it before proceeding to the smoke test.

## Summary Output

After successful creation, display:

```
Endpoint Created Successfully
─────────────────────────────
Name:           <name>
Endpoint ID:    <id>
Template ID:    <template_id>
GPUs:           <gpu list>
Workers:        <min>/<standby>/<max> (min/standby/max)
Scaling:        <scalerType> = <scalerValue>
Idle Timeout:   <seconds>s
Flashboot:      <yes/no>
Exec Timeout:   <ms>ms
Cost:           ~$<cost>/hr per worker

API URL:        https://api.runpod.ai/v2/<endpoint_id>/run
OpenAI URL:     https://api.runpod.ai/v2/<endpoint_id>/openai/v1
Health URL:     https://api.runpod.ai/v2/<endpoint_id>/health
```

## Post-Deploy Smoke Test

After verification, send a test request to confirm the endpoint processes requests. Choose the test based on endpoint type:

| Endpoint type | How to identify | Test command |
|---------------|----------------|--------------|
| **vLLM** | Preset was `vllm-endpoint`, or image is `runpod/worker-vllm:*` | Use the `/openai/v1/models` check below |
| **Vision / analysis** | Image is `gvo555/smokescan-*`, `gvo555/docudamage-*`, `gvo555/floorplan-*` | Use the analysis handler check below |
| **Custom LLM handler** | Custom image with `handler.py` that accepts `prompt` | Use the generic handler check below |

### vLLM endpoints

```bash
curl -s --max-time 120 \
  "https://api.runpod.ai/v2/<endpoint_id>/openai/v1/models" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  | python3 -m json.tool
```
Expected: JSON with `"data"` array containing the model name. If timeout after 120s, the model is still loading — wait and retry.

### Vision / analysis endpoints

```bash
curl -s --max-time 120 -X POST \
  "https://api.runpod.ai/v2/<endpoint_id>/runsync" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"input": {"test": true}}' \
  | python3 -m json.tool
```
Expected: a response with `"status": "COMPLETED"`. The `{"test": true}` input triggers a health-check path in properly written handlers. If the handler doesn't support it, use a minimal real input instead.

### Custom LLM handlers

```bash
curl -s --max-time 120 -X POST \
  "https://api.runpod.ai/v2/<endpoint_id>/runsync" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"input": {"prompt": "test", "max_tokens": 5}}' \
  | python3 -m json.tool
```
Expected: `"status": "COMPLETED"` with an `"output"` field.

### All types — failure triage

If `"status": "FAILED"`, check the `"error"` field:

| Error pattern | Cause | Fix |
|---------------|-------|-----|
| `CUDA out of memory` | Model too large for GPU | Reduce `MAX_MODEL_LEN`, enable quantization, or use larger GPU |
| `No such file or directory` | Bad entrypoint in Dockerfile | Check `CMD` in Dockerfile matches handler filename |
| `401` or `token` errors | Missing `HF_TOKEN` for gated model | Add `HF_TOKEN` to template env |
| Timeout (no response in 120s) | Cold start + model loading | Wait 2-3 min for first request on scale-to-zero endpoints, then retry |

---

## Image Update / Redeploy

To deploy a new image version to an **existing** endpoint (the most common day-2 operation):

### 1. Build & push the new image (same as Step 1)

```bash
docker build --platform linux/amd64 -t gvo555/<image-name>:<new-tag> <build-context-path>
docker push gvo555/<image-name>:<new-tag>
```

### 2. Update the template

Use MCP tool `mcp__runpod__update-template`:
```
  templateId: (existing template ID — find via mcp__runpod__list-endpoints with includeTemplate: true)
  imageName: "gvo555/<image-name>:<new-tag>"
```

Optionally update `containerDiskInGb` if the new image is significantly larger.

### 3. Workers pick up the new image

- **With flashboot enabled:** Existing workers continue serving on the old image until they idle out. New workers boot with the new image. To force an immediate rollover, temporarily set `workersMin: 0` and `workersStandby: 0`, wait for workers to drain, then restore.
- **Without flashboot:** Workers pick up the new image on next cold start.

No need to recreate the endpoint or template — updating `imageName` on the template is sufficient.

---

## Error Recovery

| Error | Cause | Fix |
|-------|-------|-----|
| `docker: command not found` | WSL integration disabled | Enable in Docker Desktop → Settings → Resources → WSL Integration |
| `docker build` fails | Dockerfile issue or missing deps | Check Dockerfile syntax, verify base image exists |
| `docker push` denied | Not logged in to Docker Hub | Run `docker login` interactively (`! docker login`) |
| `docker push` timeout | Large image (>10GB) | Consider multi-stage builds, use `.dockerignore` to reduce context |
| Template create fails | Bad image name or env | Verify image exists on Docker Hub (Step 1d), check env format |
| Endpoint create fails | Invalid template ID | Re-run Step 3, use new template ID |
| Patch returns 401 | API key issue | Check `RUNPOD_API_KEY` env var |
| Patch returns 404 | Wrong endpoint ID | Verify endpoint ID from Step 4 |
| Patch returns 400 | Invalid field value | Check flashboot is boolean, workers/timeout are numbers |
| Workers won't start | GPU unavailable | Check GPU availability, try broader GPU list |

## Teardown (if needed)

To remove a failed or test endpoint:
1. `mcp__runpod__delete-endpoint` with the endpoint ID
2. `mcp__runpod__delete-template` with the template ID (only if not shared)

## Reference Files

- `reference/presets.md` — Full preset configurations derived from production endpoints
- `~/.claude/skills/runpod/SKILL.md` — RunPod infrastructure API reference
- `~/.claude/skills/runpod-deployment/SKILL.md` — ML deployment patterns and handlers
- `~/.claude/skills/runpod-deployment/reference/` — Deep dives on serverless, vLLM, cost, monitoring
- `~/.claude/skills/runpod-deployment/templates/runpod-worker.py` — Production handler template
