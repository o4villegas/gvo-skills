---
name: runpod
description: "Deploy and manage GPU/CPU pods, network volumes, and templates on RunPod. Use when the user asks to launch a GPU server, manage cloud compute, run ML training or inference on remote GPUs, or interact with the RunPod platform in any way. Triggers: runpod, gpu cloud, launch pod, spin up server, deploy gpu, remote training, cloud gpu, inference server."
---

# RunPod — Pod & Infrastructure Management

## Auth

Set `RUNPOD_API_KEY` environment variable, or prompt user for their API key.

```
Authorization: Bearer <RUNPOD_API_KEY>
```

## API Surface

Two APIs exist. **Use REST for everything unless noted otherwise.**

| API | Base URL | Use For |
|-----|----------|---------|
| **REST** (primary) | `https://rest.runpod.io/v1` | All CRUD operations on pods, volumes, templates |
| **GraphQL** | `https://api.runpod.io/graphql` | GPU availability queries, runtime metrics, spot instance deployment |

> **CAUTION:** `api.runpod.io` is GraphQL only. REST calls to `api.runpod.io` will fail silently. Always use `rest.runpod.io` for REST.

---

## 1. Check GPU Availability

Use GraphQL — REST has no availability filter.

```graphql
POST https://api.runpod.io/graphql

query {
  gpuTypes {
    id
    displayName
    memoryInGb
    communityPrice
    securePrice
    stockStatus        # LOW, MEDIUM, HIGH, or null (unavailable)
    communityCloud
    secureCloud
  }
}
```

### Common GPU IDs

| GPU | VRAM | ID | Notes |
|-----|------|----|-------|
| RTX 4090 | 24 GB | `NVIDIA GeForce RTX 4090` | Dev/testing, cheap |
| RTX 4000 Ada | 20 GB | `NVIDIA RTX 4000 Ada Generation` | Light inference |
| L40S | 48 GB | `NVIDIA L40S` | Best value for training |
| A40 | 48 GB | `NVIDIA A40` | Inference workhorse |
| RTX 6000 Ada | 48 GB | `NVIDIA RTX 6000 Ada Generation` | Alternative 48 GB |
| A100 80 GB | 80 GB | `NVIDIA A100 80GB PCIe` | Large models |
| A100 SXM | 80 GB | `NVIDIA A100-SXM4-80GB` | Higher bandwidth A100 |
| H100 SXM | 80 GB | `NVIDIA H100 80GB HBM3` | Fastest training |
| H100 NVL | 94 GB | `NVIDIA H100 NVL` | Max VRAM H100 |

> GPU availability is **seconds-level volatile** for premium cards (H100, A100, L40S). Always wrap deploys in retry logic with a fallback GPU list.

### Suggested Fallback Chains

| Use Case | Try In Order |
|----------|-------------|
| Training (48 GB+) | L40S → A40 → RTX 6000 Ada → A100 80 GB |
| Inference (24 GB+) | RTX 4090 → RTX 4000 Ada → L40S |
| Frontier models | H100 SXM → H100 NVL → A100 SXM → A100 80 GB |
| Budget dev | RTX 4090 → RTX 4000 Ada |

---

## 2. Create a Pod

### REST (preferred)

```
POST https://rest.runpod.io/v1/pods
Content-Type: application/json
Authorization: Bearer <API_KEY>
```

```json
{
  "name": "my-pod",
  "imageName": "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04",
  "gpuTypeIds": ["NVIDIA L40S"],
  "gpuCount": 1,
  "cloudType": "ALL",
  "containerDiskInGb": 50,
  "volumeInGb": 100,
  "volumeMountPath": "/workspace",
  "ports": ["8888/http", "22/tcp"],
  "env": {
    "JUPYTER_PASSWORD": "mypassword",
    "HF_TOKEN": "hf_..."
  }
}
```

**Returns 201** with full pod object including `id`.

### Full Field Reference (REST POST /pods)

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `name` | string | `"my pod"` | Max 191 chars |
| `imageName` | string | **required** | Container image tag |
| `gpuTypeIds` | string[] | — | **Array.** GPU pods only |
| `gpuCount` | int | 1 | Multi-GPU: 2, 4, 8 |
| `gpuTypePriority` | string | `"availability"` | `availability` or `custom` (use ordering in array) |
| `computeType` | string | `"GPU"` | `GPU` or `CPU` |
| `cpuFlavorIds` | string[] | — | CPU pods only: `cpu3c`, `cpu3g`, `cpu3m`, `cpu5c`, `cpu5g`, `cpu5m` |
| `cloudType` | string | `"SECURE"` | `SECURE`, `COMMUNITY`, or omit for secure only |
| `containerDiskInGb` | int | 50 | **Ephemeral — wiped on every restart** |
| `volumeInGb` | int | 20 | Persists across restarts, mounted at `volumeMountPath` |
| `volumeMountPath` | string | `"/workspace"` | Where volume mounts |
| `networkVolumeId` | string | — | Attach a network volume (replaces local volume) |
| `ports` | string[] | `["8888/http","22/tcp"]` | Format: `port/protocol` |
| `env` | object | `{}` | `{"KEY": "value"}` format |
| `dockerEntrypoint` | string[] | `[]` | Override image ENTRYPOINT |
| `dockerStartCmd` | string[] | `[]` | Override image CMD |
| `templateId` | string | — | UUID from template list |
| `interruptible` | bool | false | Spot pricing (can be preempted at any time) |
| `locked` | bool | false | Prevents accidental stop/reset |
| `dataCenterIds` | string[] | all | e.g. `["US-TX-3","US-KS-2","EU-RO-1"]` |
| `dataCenterPriority` | string | `"availability"` | `availability` or `custom` |
| `countryCodes` | string[] | — | Filter by country |
| `allowedCudaVersions` | string[] | — | e.g. `["12.4","12.3"]` |
| `minRAMPerGPU` | int | 8 | GPU pods only |
| `minVCPUPerGPU` | int | 2 | GPU pods only |
| `vcpuCount` | int | 2 | CPU pods only |
| `supportPublicIp` | bool | — | Community Cloud only |
| `globalNetworking` | bool | false | Low-latency private networking (limited availability) |

### GraphQL (use for spot instances)

Spot instances (`podRentInterruptable`) are only available via GraphQL.

```graphql
POST https://api.runpod.io/graphql

mutation {
  podRentInterruptable(input: {
    name: "spot-training"
    imageName: "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04"
    gpuTypeId: "NVIDIA L40S"
    gpuCount: 1
    cloudType: SECURE
    bidPerGpu: 0.40
    containerDiskInGb: 50
    volumeInGb: 100
    volumeMountPath: "/workspace"
    ports: "8888/http,22/tcp"
    env: [{ key: "HF_TOKEN", value: "hf_..." }]
  }) {
    id
    machineId
    machine { podHostId }
  }
}
```

> **CRITICAL DIFFERENCE:** GraphQL `env` is `[{key, value}]` array. REST `env` is `{"key": "value"}` object. GraphQL `gpuTypeId` is singular string. REST `gpuTypeIds` is plural array. GraphQL `ports` is a single comma-separated string. REST `ports` is an array.

> **SPOT WARNING:** Interruptible pods can be terminated at any time with zero notice. Always checkpoint work to network volumes or external storage.

---

## 3. List Pods

### REST

```
GET https://rest.runpod.io/v1/pods
```

Returns array of pod objects with fields: `id`, `name`, `desiredStatus` (`RUNNING`/`EXITED`/`TERMINATED`), `costPerHr`, `gpu`, `image`, `ports`, `publicIp`, `portMappings`, `env`, `volumeInGb`, `containerDiskInGb`, `machine`, `lastStatusChange`, `interruptible`, `locked`.

### Get single pod

```
GET https://rest.runpod.io/v1/pods/{podId}
```

### Runtime metrics (GraphQL only)

REST doesn't return live GPU utilization or container metrics. Use GraphQL:

```graphql
query {
  myself {
    pods {
      id
      name
      desiredStatus
      costPerHr
      runtime {
        uptimeInSeconds
        ports { ip isIpPublic privatePort publicPort type }
        gpus { id gpuUtilPercent memoryUtilPercent }
        container { cpuPercent memoryPercent }
      }
    }
  }
}
```

---

## 4. Pod Lifecycle

### Stop (releases GPU, preserves volume)

```
POST https://rest.runpod.io/v1/pods/{podId}/stop
```

### Start / Resume

```
POST https://rest.runpod.io/v1/pods/{podId}/start
```

### Restart (soft restart, keeps GPU)

```
POST https://rest.runpod.io/v1/pods/{podId}/restart
```

### Reset (wipes container disk, keeps volume)

```
POST https://rest.runpod.io/v1/pods/{podId}/reset
```

### Terminate (permanent deletion)

```
DELETE https://rest.runpod.io/v1/pods/{podId}
```

> **TERMINATE IS IRREVERSIBLE.** All data not on a network volume is permanently destroyed.

### Resume spot instance (GraphQL only)

```graphql
mutation {
  podBidResume(input: {
    podId: "abc123"
    bidPerGpu: 0.40
    gpuCount: 1
  }) {
    id
    desiredStatus
  }
}
```

---

## 5. Update a Pod

```
PATCH https://rest.runpod.io/v1/pods/{podId}
Content-Type: application/json
```

```json
{
  "env": {"NEW_VAR": "value"},
  "ports": ["8888/http", "22/tcp", "5000/http"],
  "volumeInGb": 200,
  "imageName": "runpod/pytorch:2.8.0-py3.11-cuda12.6-devel-ubuntu22.04"
}
```

Updatable fields: `containerDiskInGb`, `containerRegistryAuthId`, `dockerEntrypoint`, `dockerStartCmd`, `env`, `globalNetworking`, `imageName`, `locked`, `name`, `ports`, `volumeInGb`, `volumeMountPath`.

> **Updates may trigger a pod reset.** Warn user that running processes will be interrupted.

---

## 6. Network Volumes

Network volumes are persistent storage **independent of any pod**. They survive pod termination and can be attached to any pod in the same datacenter. Critical for ML workflows.

### Create

```
POST https://rest.runpod.io/v1/networkvolumes
```

```json
{
  "name": "training-data",
  "size": 100,
  "dataCenterId": "US-TX-3"
}
```

### List

```
GET https://rest.runpod.io/v1/networkvolumes
```

### Get

```
GET https://rest.runpod.io/v1/networkvolumes/{networkVolumeId}
```

### Update

```
PATCH https://rest.runpod.io/v1/networkvolumes/{networkVolumeId}
```

### Delete

```
DELETE https://rest.runpod.io/v1/networkvolumes/{networkVolumeId}
```

### Attach to pod at creation

Set `networkVolumeId` in the pod create call. This **replaces** the local volume — the network volume mounts at `volumeMountPath` (default `/workspace`).

```json
{
  "name": "my-pod",
  "imageName": "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04",
  "gpuTypeIds": ["NVIDIA L40S"],
  "networkVolumeId": "vol_abc123",
  "volumeMountPath": "/workspace"
}
```

### Gotchas

- **Cannot attach/detach after pod creation.** Must terminate and recreate.
- **Size cannot be decreased**, only increased. Over 4 TB requires support contact.
- **Concurrent writes from multiple pods corrupt data.** One writer at a time.
- **Pod and volume must be in the same datacenter.** Specify `dataCenterIds` on pod create to match.
- **$0.07/GB/month** for first TB, $0.05/GB/month after. Volumes with no payment method risk deletion.

---

## 7. Templates

### List

```
GET https://rest.runpod.io/v1/templates
```

### Create

```
POST https://rest.runpod.io/v1/templates
```

```json
{
  "name": "my-training-template",
  "imageName": "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04",
  "containerDiskInGb": 50,
  "volumeInGb": 100,
  "volumeMountPath": "/workspace",
  "ports": ["8888/http", "22/tcp"],
  "env": {"JUPYTER_PASSWORD": "default"},
  "dockerStartCmd": []
}
```

### Update

```
PATCH https://rest.runpod.io/v1/templates/{templateId}
```

### Delete

```
DELETE https://rest.runpod.io/v1/templates/{templateId}
```

> Template must not be in use by any pod or serverless endpoint.

---

## 8. Connecting to a Pod

### HTTP Proxy (easiest, has timeout)

```
https://{podId}-{internalPort}.proxy.runpod.net
```

Example: `https://abc123-8888.proxy.runpod.net` for Jupyter.

> **100-second hard timeout** enforced by Cloudflare. Long-running requests (large inference, file transfers) will be killed. Use TCP ports for these.

### TCP / Direct (no timeout)

Check port mappings from pod response: `portMappings` object maps internal → public ports.

```
ssh root@{publicIp} -p {mappedPort} -i ~/.ssh/id_ed25519
```

Or via `runpodctl`:

```bash
runpodctl ssh --podId abc123
```

### Symmetrical Port Mapping

Request internal ports ≥ 70000 to get matching external ports. Access via env var `$RUNPOD_TCP_PORT_70000`.

---

## 9. Billing

```
GET https://rest.runpod.io/v1/billing/pods
GET https://rest.runpod.io/v1/billing/endpoints
GET https://rest.runpod.io/v1/billing/networkvolumes
```

---

## 10. CLI Reference (runpodctl)

```bash
export RUNPOD_API_KEY="rpa_..."

runpodctl get pod                          # List pods
runpodctl start pod <podId>                # Start
runpodctl stop pod <podId>                 # Stop
runpodctl remove pod <podId>               # Terminate
runpodctl create pod <name> \
  --gpu-type "NVIDIA L40S" \
  --image "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04" \
  --gpu-count 1 \
  --volume-size 100                        # Create pod

runpodctl ssh --podId <podId>              # SSH into pod
runpodctl ssh-add-key                      # Add SSH public key
runpodctl send <file> --podId <podId>      # Upload file
runpodctl receive <file> --podId <podId>   # Download file
```

---

## Critical Gotchas

### "Zero GPU on Restart"

When you **stop** a pod, its GPU is released. If another user claims it before you restart, your pod cannot get a GPU. Your volume data remains stranded on that machine.

**Mitigation:** Use network volumes for all important data. Network volumes are decoupled from machines and can attach to any pod in the same datacenter.

### Storage Model

```
containerDiskInGb  →  EPHEMERAL. Wiped on every restart. For temp/build files.
volumeInGb         →  LOCAL PERSISTENT. Survives restarts at /workspace. Tied to one machine.
networkVolumeId    →  INDEPENDENT PERSISTENT. Survives pod termination. Portable across pods.
```

Always save checkpoints, model weights, and datasets to `/workspace` (volume) at minimum. For multi-session work, use network volumes.

### Spot Instance Preemption

`interruptible: true` pods can be terminated at any moment with zero warning. Always:
- Checkpoint every N steps to the volume or network volume
- Use a training framework with automatic resume (e.g. PyTorch Lightning, HF Accelerate)
- Set `bidPerGpu` competitively — too low and you get preempted faster

### Community vs Secure Cloud

| | Secure | Community |
|---|---|---|
| Hardware | RunPod-owned datacenters | Third-party providers |
| Price | Higher | 20–40% cheaper |
| Reliability | Higher uptime | Variable |
| Data | RunPod infrastructure | Third-party hardware |
| Public IP | Always available | Optional (`supportPublicIp`) |

### Port Timeout

HTTP proxy (`proxy.runpod.net`): **100-second Cloudflare timeout**. Use TCP ports for anything long-running.

### Rate Limits

No published rate limits, but rapid-fire pod creation may be throttled. Add 1–2 second delays between batch operations.

---

## Error Handling Patterns

### GPU Out of Stock

```
Response: 400 — insufficient availability
```

Retry strategy:
1. Try next GPU in fallback chain
2. Try `cloudType: "ALL"` (adds Community Cloud)
3. Try different `dataCenterIds`
4. If using REST, set `gpuTypePriority: "availability"` with multiple `gpuTypeIds`
5. Wait 30–60s and retry (availability changes fast)

### Pod Won't Resume After Stop

GPU was claimed by another user (Zero GPU problem). Options:
1. Wait and retry periodically
2. Terminate and create a new pod (data on local volume is lost)
3. Start without GPU to retrieve data from volume, then create new pod

### Network Volume Not Attaching

Volume and pod must be in the same datacenter. Verify with:
```
GET https://rest.runpod.io/v1/networkvolumes/{id}
```
Check `dataCenterId` matches your pod's `dataCenterIds`.
