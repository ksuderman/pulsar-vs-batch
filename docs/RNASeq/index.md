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
- **Pulsar server:** http://35.188.245.115
- **Date:** 2026-03-17 to 2026-03-23

### Runners Compared

| Runner | Type | Job Dispatch | File Transfer |
|--------|------|-------------|---------------|
| **GCP Batch** (direct) | `GoogleCloudBatchJobRunner` | Galaxy submits directly to GCP Batch API | Galaxy handles staging natively |
| **Pulsar** (AMQP sidecar) | `PulsarGcpBatchJobRunner` | Galaxy sends AMQP message; Pulsar sidecar stages inputs, runs tool, collects outputs, sends AMQP callback | HTTP upload/download via `remote_transfer` |

### Workflow Runs

6 workflow invocations, 114 total jobs (96 succeeded, 18 failed/errored).

### Failed/Errored Jobs

| Cloud | Tool | State | Count |
|-------|------|-------|-------|
| batch | bamFilter | deleted | 1 |
| batch | cufflinks | deleted | 1 |
| batch | cufflinks | deleting | 1 |
| batch | multiqc | deleting | 1 |
| batch | multiqc | error | 2 |
| batch | multiqc | queued | 1 |
| batch | param_value_from_file | deleted | 1 |
| batch | param_value_from_file | deleting | 1 |
| batch | revertR2orientationInBam | deleted | 1 |
| batch | rna_star | error | 3 |
| batch | tp_awk_tool | deleted | 1 |
| batch | tp_awk_tool | deleting | 1 |
| batch | tp_awk_tool | error | 3 |

## Results Summary

### All Runs

| Runner | Run | Input Sizes | Wall Clock | Compute Time | Scheduling Overhead | Steps OK |
|--------|-----|-------------|-----------|-------------|-------------------|----------|
| batch | 1 | 2GB | 130.1 min | 140.5 min | -10.4 min (-8%) | 20/20 |
| batch | 1 | 5GB | 72.5 min | 0.7 min | 71.8 min (99%) | 6/16 |
| batch | 1 | 10GB | 41.3 min | 25.2 min | 16.1 min (39%) | 10/18 |
| pulsar | 1 | 2GB | 85.8 min | 87.1 min | -1.3 min (-2%) | 20/20 |
| pulsar | 1 | 5GB | 139.7 min | 149.3 min | -9.6 min (-7%) | 20/20 |
| pulsar | 1 | 10GB | 202.4 min | 215.7 min | -13.2 min (-7%) | 20/20 |

### Head-to-Head: 2GB

| Metric | GCP Batch | Pulsar | Difference |
|--------|-----------|--------|------------|
| **Wall clock** | **130.1 min** | **85.8 min** | **-44.3 min (-34%)** |
| **Compute time** | **140.5 min** | **87.1 min** | **-53.4 min (-38%)** |
| **Scheduling overhead** | **-10.4 min** | **-1.3 min** | **9.1 min (-87%)** |
| Steps completed | 20/20 | 20/20 | -- |

### Head-to-Head: 5GB

| Metric | GCP Batch | Pulsar | Difference |
|--------|-----------|--------|------------|
| **Wall clock** | **72.5 min** | **139.7 min** | **67.3 min (+93%)** |
| **Compute time** | **0.7 min** | **149.3 min** | **148.6 min (+20730%)** |
| **Scheduling overhead** | **71.8 min** | **-9.6 min** | **-81.3 min (-113%)** |
| Steps completed | 6/16 | 20/20 | -- |

### Head-to-Head: 10GB

| Metric | GCP Batch | Pulsar | Difference |
|--------|-----------|--------|------------|
| **Wall clock** | **41.3 min** | **202.4 min** | **161.1 min (+390%)** |
| **Compute time** | **25.2 min** | **215.7 min** | **190.5 min (+756%)** |
| **Scheduling overhead** | **16.1 min** | **-13.2 min** | **-29.4 min (-182%)** |
| Steps completed | 10/18 | 20/20 | -- |

## Per-Step Compute Time (runtime_seconds)

### 2GB

| Tool | Batch | Pulsar | Diff | Diff% |
|------|-------|--------|------|-------|
| cufflinks | 2564s | 2146s | -418s | -16% |
| rna_star | 4602s | 1828s | -2774s | -60% |
| bamFilter | 448s | 360s | -88s | -20% |
| revertR2orientationInBam | 191s | 196s | +5s | +3% |
| cutadapt | 176s | 147s | -29s | -16% |
| bedtools_genomecoveragebed | 334s | 303s | -31s | -9% |
| param_value_from_file | 9s | 28s | +19s | +211% |
| compose_text_param | 8s | 38s | +30s | +375% |
| map_param_value | 35s | 131s | +96s | +274% |
| wig_to_bigWig | 44s | 40s | -4s | -9% |
| multiqc | 16s | 8s | -8s | -50% |
| tp_awk_tool | 1s | 0s | -1s | -- |
| **Total** | **8428s** | **5225s** | **-3203s** | **-38%** |

### 5GB

| Tool | Batch | Pulsar | Diff | Diff% |
|------|-------|--------|------|-------|
| cufflinks * | 0s | 3458s | +3458s | -- |
| rna_star * | 0s | 2850s | +2850s | -- |
| bamFilter * | 0s | 870s | +870s | -- |
| revertR2orientationInBam * | 0s | 470s | +470s | -- |
| cutadapt | 0s | 364s | +364s | -- |
| bedtools_genomecoveragebed * | 0s | 631s | +631s | -- |
| param_value_from_file * | 0s | 37s | +37s | -- |
| compose_text_param | 9s | 37s | +28s | +311% |
| map_param_value | 34s | 166s | +132s | +388% |
| wig_to_bigWig * | 0s | 65s | +65s | -- |
| multiqc * | 0s | 8s | +8s | -- |
| tp_awk_tool * | 0s | 1s | +1s | -- |
| **Total** | **43s** | **8957s** | **+8914s** | **+20730%** |

*Tools only on Pulsar: cufflinks, rna_star, bamFilter, revertR2orientationInBam, bedtools_genomecoveragebed, param_value_from_file, wig_to_bigWig, multiqc, tp_awk_tool*

### 10GB

| Tool | Batch | Pulsar | Diff | Diff% |
|------|-------|--------|------|-------|
| cufflinks * | 0s | 5096s | +5096s | -- |
| rna_star | 1467s | 3047s | +1580s | +108% |
| bamFilter | 0s | 1711s | +1711s | -- |
| revertR2orientationInBam | 0s | 910s | +910s | -- |
| cutadapt | 0s | 722s | +722s | -- |
| bedtools_genomecoveragebed * | 0s | 1160s | +1160s | -- |
| param_value_from_file * | 0s | 30s | +30s | -- |
| compose_text_param | 9s | 34s | +25s | +278% |
| map_param_value | 35s | 126s | +91s | +260% |
| wig_to_bigWig * | 0s | 98s | +98s | -- |
| multiqc * | 0s | 7s | +7s | -- |
| tp_awk_tool | 0s | 0s | +0s | -- |
| **Total** | **1511s** | **12941s** | **+11430s** | **+756%** |

*Tools only on Pulsar: cufflinks, bedtools_genomecoveragebed, param_value_from_file, wig_to_bigWig, multiqc*

## Resource Allocation: VM Sizing vs GALAXY_SLOTS

### VM Right-Sizing (Working)

Pulsar correctly right-sizes GCP Batch VMs based on per-tool resource requirements. The TPV destination passes `cores: "{cores}"` and `mem: "{mem}"` to Pulsar's `parse_gcp_job_params()`, which calls `compute_machine_type()` to select an appropriate N2 machine type.

### GALAXY_SLOTS Reporting (Fixed)

Pulsar now correctly reports GALAXY_SLOTS. The fix injects the proper slot count into the Pulsar task environment, so Galaxy metrics accurately reflect the VM cores allocated to each job.

### Batch Resource Allocation (as reported by Galaxy)

| Tool | CPU Slots |
|------|-----------|
| cufflinks | 6 |
| rna_star | 10 |
| bamFilter | 1 |
| revertR2orientationInBam | 1 |
| cutadapt | 8 |
| bedtools_genomecoveragebed | 1 |
| param_value_from_file | 1 |
| compose_text_param | 1 |
| map_param_value | 1 |
| wig_to_bigWig | 1 |
| multiqc | 1 |
| tp_awk_tool | 1 |

### Runtime Ratio Analysis (2GB)

| Tool | Batch Slots | Pulsar/Batch Ratio | Expected if 1 Thread |
|------|------------|-------------------|---------------------|
| cufflinks | 6 | 0.84x | ~6x |
| rna_star | 10 | 0.40x | ~10x |
| bamFilter | 1 | 0.80x | ~1x |
| revertR2orientationInBam | 1 | 1.03x | ~1x |
| cutadapt | 8 | 0.84x | ~8x |
| bedtools_genomecoveragebed | 1 | 0.91x | ~1x |
| param_value_from_file | 1 | 3.11x | ~1x |
| compose_text_param | 1 | 4.75x | ~1x |
| map_param_value | 1 | 3.74x | ~1x |
| wig_to_bigWig | 1 | 0.91x | ~1x |
| multiqc | 1 | 0.50x | ~1x |

## Wall Clock vs Compute Time Analysis

| Runner | Input | Wall Clock | Compute | Overhead | Overhead % |
|--------|-------|-----------|---------|----------|------------|
| batch R1 | 2GB | 130.1m | 140.5m | -10.4m | -8% |
| batch R1 | 5GB | 72.5m | 0.7m | 71.8m | 99% |
| batch R1 | 10GB | 41.3m | 25.2m | 16.1m | 39% |
| pulsar R1 | 2GB | 85.8m | 87.1m | -1.3m | -2% |
| pulsar R1 | 5GB | 139.7m | 149.3m | -9.6m | -7% |
| pulsar R1 | 10GB | 202.4m | 215.7m | -13.2m | -7% |

## Batch Scaling Analysis

| Input | Wall Clock | Compute |
|-------|-----------|---------|
| 2GB | 130.1m | 140.5m |
| 5GB | 72.5m | 0.7m |
| 10GB | 41.3m | 25.2m |

## Key Findings

### 1. 2GB: Pulsar is -34% slower (wall clock)

- Wall clock: 85.8m vs 130.1m
- Compute: 87.1m vs 140.5m (-38%)

### 2. 5GB: Pulsar is +93% slower (wall clock)

- Wall clock: 139.7m vs 72.5m
- Compute: 149.3m vs 0.7m (+20730%)

### 3. 10GB: Pulsar is +390% slower (wall clock)

- Wall clock: 202.4m vs 41.3m
- Compute: 215.7m vs 25.2m (+756%)

### 4. Several tools are faster on Pulsar

- **rna_star** (2GB): -60% (1828s vs 4602s)
- **multiqc** (2GB): -50% (8s vs 16s)

### 5. Scheduling overhead is Pulsar's major cost

- Batch: 1.6 min/step avg
- Pulsar: -0.4 min/step avg

## Implications

- **Pulsar's staging overhead is inherent** to the AMQP sidecar architecture. Dominates for short multi-step workflows, negligible for long-running single-step jobs.
- **Pulsar's I/O model has advantages.** Local SSD staging benefits I/O-bound tools.
