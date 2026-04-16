# Endpoint Presets

Derived from production endpoints as of 2026-04-11. Use these as starting points.

## Preset: heavy-analysis

Based on: `smokescan-analysis -fb` (endpoint `4fu896ozb83lxq`)
Best for: GPU-intensive vision/analysis workloads (smoke damage, water damage, multi-image analysis)

```
Template:
  image: <your-docker-hub-namespace>/<image>:<tag>
  containerDiskInGb: 150
  isServerless: true
  env:
    HF_TOKEN: (from environment)

Endpoint:
  gpuTypeIds: ["NVIDIA H100 PCIe", "NVIDIA H100 80GB HBM3", "NVIDIA H100 NVL", "NVIDIA A100 80GB PCIe", "NVIDIA A100-SXM4-80GB"]
  gpuCount: 1
  workersMin: 0
  workersMax: 2

Advanced (via update + patch):
  idleTimeout: 800
  scalerType: QUEUE_DELAY
  scalerValue: 4
  flashboot: true
  workersStandby: 2
  executionTimeoutMs: 600000
```

Cost profile: ~$2.69-2.99/hr per worker, scale-to-zero when idle.
Trade-offs: High standby (2) = fast response but costs ~$5.38-5.98/hr when both warm. 800s idle keeps workers alive through bursts.

---

## Preset: light-inference

Based on: `DocuDamage -fb` (endpoint `ctirfwuqnl37r8`)
Best for: Lighter inference tasks (document analysis, floorplan processing, single-image tasks)

```
Template:
  image: <your-docker-hub-namespace>/<image>:<tag>
  containerDiskInGb: 32
  isServerless: true
  env:
    HF_TOKEN: (from environment)

Endpoint:
  gpuTypeIds: ["NVIDIA GeForce RTX 4090", "NVIDIA GeForce RTX 5090"]
  gpuCount: 1
  workersMin: 0
  workersMax: 3

Advanced (via update + patch):
  idleTimeout: 5
  scalerType: QUEUE_DELAY
  scalerValue: 4
  flashboot: true
  workersStandby: 3
  executionTimeoutMs: 600000
```

Cost profile: ~$0.59/hr per worker, aggressive 5s idle timeout.
Trade-offs: 3 standby workers with 5s idle = high availability but rapid cycling. Consumer GPUs (4090/5090) are much cheaper than datacenter GPUs.

---

## Preset: vllm-endpoint

Based on: templates `cn2qc9h4h9` and `t2no6k07au`
Best for: OpenAI-compatible LLM serving with vLLM

```
Template:
  image: runpod/worker-vllm:stable-cuda12.1.0
  containerDiskInGb: 120
  isServerless: true
  env:
    MODEL_NAME: (user-specified)
    DTYPE: bfloat16
    GPU_MEMORY_UTILIZATION: "0.90"
    MAX_MODEL_LEN: "8192"
    TRUST_REMOTE_CODE: "1"
    HF_TOKEN: (from environment)

Endpoint:
  gpuTypeIds: ["NVIDIA H100 PCIe", "NVIDIA H100 80GB HBM3", "NVIDIA A100 80GB PCIe", "NVIDIA A100-SXM4-80GB"]
  gpuCount: 1
  workersMin: 0
  workersMax: 2

Advanced (via update + patch):
  idleTimeout: 800
  scalerType: QUEUE_DELAY
  scalerValue: 4
  flashboot: true
  workersStandby: 1
  executionTimeoutMs: 600000
```

Cost profile: ~$2.69-2.99/hr per worker. vLLM handles batching so fewer workers needed.
Trade-offs: 120GB container disk needed for large model weights baked into the image. 0.90 GPU utilization leaves headroom for spikes.

---

## Preset: budget-dev

For development and testing, not derived from existing endpoints.

```
Template:
  image: <your-docker-hub-namespace>/<image>:<tag>
  containerDiskInGb: 20
  isServerless: true

Endpoint:
  gpuTypeIds: ["NVIDIA GeForce RTX 4090"]
  gpuCount: 1
  workersMin: 0
  workersMax: 1

Advanced (via update + patch):
  idleTimeout: 5
  scalerType: QUEUE_DELAY
  scalerValue: 4
  flashboot: true
  workersStandby: 0
  executionTimeoutMs: 300000
```

Cost profile: ~$0.44/hr, true scale-to-zero (0 standby). Cold starts expected.
Trade-offs: No standby = every request hits cold start (30-60s). Good for testing, not production.

---

## GPU Selection Guide

| Workload | Recommended GPUs | VRAM | Cost Range |
|----------|-----------------|------|------------|
| Light inference (<7B params) | RTX 4090, RTX 5090 | 24GB | $0.44-0.69/hr |
| Medium inference (7-30B params) | L40S, A40, RTX 6000 Ada | 48GB | $0.69-1.14/hr |
| Heavy inference (30-70B params) | A100 80GB, H100 | 80GB | $1.89-2.99/hr |
| Multi-image vision models | H100, A100 80GB | 80GB | $1.89-2.99/hr |
| Fine-tuning | L40S, A100 80GB | 48-80GB | $0.69-1.89/hr |

## Scaling Cheat Sheet

| Pattern | idleTimeout | workersStandby | Use Case |
|---------|-------------|----------------|----------|
| Always warm | 800+ | = workersMax | Production, latency-critical |
| Burst ready | 60-120 | 1 | Moderate traffic, cost-conscious |
| Scale-to-zero | 5-15 | 0 | Dev/test, infrequent use |
| High availability | 300-800 | >= 2 | Production with traffic spikes |
