---
title: Pulsar vs Direct GCP Batch
---

# Pulsar vs Direct GCP Batch

Benchmarking two strategies for dispatching Galaxy jobs to Google Cloud Platform's Batch service.

## Overview

This project compares two GCP Batch job runner architectures available in [Galaxy](https://galaxyproject.org/) 26.1:

| | Direct GCP Batch | Pulsar GCP Batch |
|---|---|---|
| **Runner** | `GoogleCloudBatchJobRunner` | `PulsarGcpBatchJobRunner` |
| **How it works** | Galaxy submits jobs directly to the GCP Batch API | Galaxy sends an AMQP message to a Pulsar sidecar, which stages files, runs the tool on GCP Batch, and returns results via AMQP |
| **File transfer** | NFS (shared filesystem) | HTTP upload/download via `remote_transfer` to local SSD |
| **Galaxy host** | e2-standard-4 (4 vCPU, 16 GB) | e2-standard-4 (4 vCPU, 16 GB) |
| **Job VMs** | N2 on-demand, right-sized per tool | N2 on-demand, right-sized per tool + 375 GB local SSD |

Both runners provision per-job VMs on GCP Batch with machine types selected automatically based on each tool's CPU and memory requirements. The key difference is how input/output files are transferred: the direct Batch runner uses a shared NFS volume, while Pulsar stages files via HTTP to a local SSD on each job VM.

## Infrastructure

- **Region:** us-east4
- **Galaxy version:** 26.1
- **Kubernetes:** RKE2 on GCE
- **VM image:** `galaxy-k8s-boot-debian12-v2026-02-24` (CVMFS pre-installed)
- **Input data:** Paired-end WGS reads (SRR24043307) at 2 GB, 5 GB, and 10 GB subsample sizes

## Experiments

### Variant Calling

A 12-step variant analysis pipeline (fastp, bwa_mem, picard, lofreq, snpEff, samtools, multiqc) run at three input sizes on both runners.

- **72 jobs** (36 per runner), all completed successfully
- **3 input sizes:** 2 GB, 5 GB, 10 GB

| | Batch | Pulsar |
|---|---|---|
| Compute cost (cgroups) | $3.52 | $3.43 |
| Wallclock cost (VM billing) | $16.86 | $21.22 |
| Galaxy VM (e2-standard-4) | $2.44 | $2.72 |
| **Total** | **$19.30** | **$23.94** |

[Performance Report](Variant-Calling/index.html) | [Performance Charts](Variant-Calling/charts.html) | [Cost Analysis](Variant-Calling/costs.html) | [Cost Charts](Variant-Calling/cost-charts.html)

### RNASeq

A 12-step RNA-seq pipeline (cutadapt, rna_star, cufflinks, bamFilter, bedtools, multiqc, and parameter tools) run at three input sizes on both runners.

- **96 successful jobs** out of 114 total (18 failed on Batch at larger input sizes)
- **3 input sizes:** 2 GB, 5 GB, 10 GB

| | Batch | Pulsar |
|---|---|---|
| Compute cost (cgroups) | $1.65 | $3.34 |
| Wallclock cost (VM billing) | $3.94 | $11.68 |
| Galaxy VM (e2-standard-4) | $20.77 | $1.03 |
| **Total** | **$24.70** | **$12.71** |

[Performance Report](RNASeq/index.html) | [Performance Charts](RNASeq/charts.html) | [Cost Analysis](RNASeq/costs.html) | [Cost Charts](RNASeq/cost-charts.html)

## Key Findings

1. **Compute costs are similar** — When comparing only cgroups runtime (actual CPU usage), both runners produce nearly identical costs for Variant Calling ($3.52 vs $3.43). RNASeq shows Pulsar at 2x compute cost due to more completed jobs at larger input sizes.

2. **Wallclock overhead is significant** — Users pay for VM provisioning, image pull, file staging, and scheduling in addition to compute. Overhead ratios range from 4.8x (Batch) to 6.2x (Pulsar) for Variant Calling.

3. **Pulsar's local SSD staging adds cost** — Each Pulsar job provisions a 375 GB local SSD, adding ~7% to per-job cost. The HTTP file transfer also increases wallclock time relative to NFS.

4. **Galaxy VM cost varies by experiment duration** — For long-running experiments (RNASeq on Batch: 150+ hours), the always-on Galaxy host VM dominates total cost. For shorter experiments, per-job Batch VM costs dominate.

5. **GCP Batch can be cheaper than a single large VM** — For RNASeq on Batch, dispatching to on-demand VMs is 83% cheaper than running on a dedicated n2-standard-20 ($24.70 vs $146.65), because the Batch VMs are only alive during active computation.

## Cost Methodology

- **Compute cost**: Based on cgroups `runtime_seconds` — actual CPU time inside the container
- **Wallclock cost**: Based on Galaxy job lifetime (create_time to update_time) — includes VM boot, staging, compute, and shutdown
- **Galaxy VM cost**: e2-standard-4 running for the experiment duration (first job submitted to last result returned)
- **Pricing**: GCP N2/E2 on-demand rates for us-east4
- **Rainstone comparison**: Historical per-tool costs from [usegalaxy.org](https://rainstone.anvilproject.org) production workloads (compared against compute costs)
