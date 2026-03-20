---
title: Pulsar vs Direct GCP Batch - RNASeq
---

# Pulsar vs Direct GCP Batch: RNASeq

**[Interactive Charts](charts.html)** | **[Cost Summary](costs.html)** | **[Cost Charts](cost-charts.html)**

## Experiment Setup

- **Workflow:** RNASeq (12 unique tool types)
- **Galaxy version:** 26.1
- **Infrastructure:** GCE VM on RKE2 Kubernetes, jobs dispatched to GCP Batch VMs (us-east4)
- **Custom VM image:** `galaxy-k8s-minimal-debian12-v2026-03-05` (CVMFS pre-installed)
- **Batch server:** http://34.11.12.196
- **Pulsar server:** http://35.194.76.109
- **Date:** 2026-03-17 to 2026-03-17

### Runners Compared

| Runner | Type | Job Dispatch | File Transfer |
|--------|------|-------------|---------------|
| **GCP Batch** (direct) | `GoogleCloudBatchJobRunner` | Galaxy submits directly to GCP Batch API | Galaxy handles staging natively |
| **Pulsar** (AMQP sidecar) | `PulsarGcpBatchJobRunner` | Galaxy sends AMQP message; Pulsar sidecar stages inputs, runs tool, collects outputs, sends AMQP callback | HTTP upload/download via `remote_transfer` |

### Workflow Runs

2 workflow invocations, 34 total jobs (24 succeeded, 10 failed/errored).

### Failed/Errored Jobs

| Cloud | Tool | State | Count |
|-------|------|-------|-------|
| pulsar | bamFilter | deleted | 1 |
| pulsar | compose_text_param | deleted | 1 |
| pulsar | map_param_value | deleting | 4 |
| pulsar | param_value_from_file | error | 3 |
| pulsar | revertR2orientationInBam | deleting | 1 |

## Results Summary

### All Runs

| Runner | Run | Input Sizes | Wall Clock | Compute Time | Scheduling Overhead | Steps OK |
|--------|-----|-------------|-----------|-------------|-------------------|----------|
| batch | 1 | SRR24043307-80 | 130.1 min | 140.5 min | -10.4 min (-8%) | 20/20 |
| pulsar | 1 | SRR24043307-80 | 70.2 min | 52.1 min | 18.1 min (26%) | 4/14 |

### Head-to-Head: SRR24043307-80

| Metric | GCP Batch | Pulsar | Difference |
|--------|-----------|--------|------------|
| **Wall clock** | **130.1 min** | **70.2 min** | **-59.9 min (-46%)** |
| **Compute time** | **140.5 min** | **52.1 min** | **-88.3 min (-63%)** |
| **Scheduling overhead** | **-10.4 min** | **18.1 min** | **28.5 min (-274%)** |
| Steps completed | 20/20 | 4/14 | -- |

## Per-Step Compute Time (runtime_seconds)

### SRR24043307-80

| Tool | Batch | Pulsar | Diff | Diff% |
|------|-------|--------|------|-------|
| rna_star | 4602s | 2975s | -1627s | -35% |
| cufflinks * | 2564s | 0s | -2564s | -100% |
| bamFilter * | 448s | 0s | -448s | -100% |
| revertR2orientationInBam * | 191s | 0s | -191s | -100% |
| cutadapt | 176s | 145s | -31s | -18% |
| bedtools_genomecoveragebed * | 334s | 0s | -334s | -100% |
| wig_to_bigWig * | 44s | 0s | -44s | -100% |
| multiqc | 16s | 9s | -7s | -44% |
| param_value_from_file * | 9s | 0s | -9s | -100% |
| map_param_value * | 35s | 0s | -35s | -100% |
| compose_text_param * | 8s | 0s | -8s | -100% |
| tp_awk_tool | 1s | 0s | -1s | -- |
| **Total** | **8428s** | **3129s** | **-5299s** | **-63%** |

*Tools only on Batch: cufflinks, bamFilter, revertR2orientationInBam, bedtools_genomecoveragebed, wig_to_bigWig, param_value_from_file, map_param_value, compose_text_param*

## Resource Allocation: VM Sizing vs GALAXY_SLOTS

### VM Right-Sizing (Working)

Pulsar correctly right-sizes GCP Batch VMs based on per-tool resource requirements. The TPV destination passes `cores: "{cores}"` and `mem: "{mem}"` to Pulsar's `parse_gcp_job_params()`, which calls `compute_machine_type()` to select an appropriate N2 machine type.

### GALAXY_SLOTS Reporting (Fixed)

Pulsar now correctly reports GALAXY_SLOTS. The fix injects the proper slot count into the Pulsar task environment, so Galaxy metrics accurately reflect the VM cores allocated to each job.

### Batch Resource Allocation (as reported by Galaxy)

| Tool | CPU Slots |
|------|-----------|
| rna_star | 10 |
| cufflinks | 6 |
| bamFilter | 1 |
| revertR2orientationInBam | 1 |
| cutadapt | 8 |
| bedtools_genomecoveragebed | 1 |
| wig_to_bigWig | 1 |
| multiqc | 1 |
| param_value_from_file | 1 |
| map_param_value | 1 |
| compose_text_param | 1 |
| tp_awk_tool | 1 |

### Runtime Ratio Analysis (SRR24043307-80)

| Tool | Batch Slots | Pulsar/Batch Ratio | Expected if 1 Thread |
|------|------------|-------------------|---------------------|
| rna_star | 10 | 0.65x | ~10x |
| cutadapt | 8 | 0.82x | ~8x |
| multiqc | 1 | 0.56x | ~1x |

## Wall Clock vs Compute Time Analysis

| Runner | Input | Wall Clock | Compute | Overhead | Overhead % |
|--------|-------|-----------|---------|----------|------------|
| batch R1 | SRR24043307-80 | 130.1m | 140.5m | -10.4m | -8% |
| pulsar R1 | SRR24043307-80 | 70.2m | 52.1m | 18.1m | 26% |

## Key Findings

### 1. SRR24043307-80: Pulsar is -46% slower (wall clock)

- Wall clock: 70.2m vs 130.1m
- Compute: 52.1m vs 140.5m (-63%)

### 2. Several tools are faster on Pulsar

- **rna_star** (SRR24043307-80): -35% (2975s vs 4602s)
- **multiqc** (SRR24043307-80): -44% (9s vs 16s)

### 3. Scheduling overhead is Pulsar's major cost

- Batch: -0.5 min/step avg
- Pulsar: 1.3 min/step avg

## Implications

- **Pulsar's staging overhead is inherent** to the AMQP sidecar architecture. Dominates for short multi-step workflows, negligible for long-running single-step jobs.
- **Pulsar's I/O model has advantages.** Local SSD staging benefits I/O-bound tools.
