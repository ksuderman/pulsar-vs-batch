---
title: Pulsar vs Direct GCP Batch - RNASeq
---

# Pulsar vs Direct GCP Batch: RNASeq

**[Interactive Charts](charts.html)** | **[Cost Summary](../costs.md)**

## Experiment Setup

- **Workflow:** RNASeq (12 unique tool types)
- **Galaxy version:** 26.1
- **Infrastructure:** GCE VM on RKE2 Kubernetes, jobs dispatched to GCP Batch VMs (us-east4)
- **Custom VM image:** `galaxy-k8s-minimal-debian12-v2026-03-05` (CVMFS pre-installed)
- **Batch server:** http://34.48.93.121
- **Pulsar server:** http://35.245.29.195
- **Date:** 2026-03-13 to 2026-03-13

### Runners Compared

| Runner | Type | Job Dispatch | File Transfer |
|--------|------|-------------|---------------|
| **GCP Batch** (direct) | `GoogleCloudBatchJobRunner` | Galaxy submits directly to GCP Batch API | Galaxy handles staging natively |
| **Pulsar** (AMQP sidecar) | `PulsarGcpBatchJobRunner` | Galaxy sends AMQP message; Pulsar sidecar stages inputs, runs tool, collects outputs, sends AMQP callback | HTTP upload/download via `remote_transfer` |

### Workflow Runs

6 workflow invocations, 103 total jobs (72 succeeded, 31 failed/errored).

### Failed/Errored Jobs

| Cloud | Tool | State | Count |
|-------|------|-------|-------|
| pulsar | bamFilter | deleted | 3 |
| pulsar | compose_text_param | deleted | 1 |
| pulsar | compose_text_param | deleting | 2 |
| pulsar | cutadapt | error | 1 |
| pulsar | map_param_value | deleted | 1 |
| pulsar | map_param_value | deleting | 11 |
| pulsar | param_value_from_file | error | 9 |
| pulsar | revertR2orientationInBam | deleted | 1 |
| pulsar | revertR2orientationInBam | deleting | 2 |

## Results Summary

### All Runs

| Runner | Run | Input Sizes | Wall Clock | Compute Time | Scheduling Overhead | Steps OK |
|--------|-----|-------------|-----------|-------------|-------------------|----------|
| batch | 1 | SRR24043307-50 SRR24043307-80 | 129.1 min | 162.1 min | -33.0 min (-26%) | 20/20 |
| batch | 1 | SRR24043307-50 SRR24043307-80 SRR24043307-full | 208.4 min | 274.0 min | -65.6 min (-31%) | 20/20 |
| batch | 1 | SRR24043307-80 | 115.4 min | 126.2 min | -10.8 min (-9%) | 20/20 |
| pulsar | 1 | SRR24043307-50 SRR24043307-80 | 80.4 min | 42.1 min | 38.3 min (48%) | 4/15 |
| pulsar | 1 | SRR24043307-50 SRR24043307-80 SRR24043307-full | 127.7 min | 69.2 min | 58.5 min (46%) | 4/14 |
| pulsar | 1 | SRR24043307-80 | 75.7 min | 54.8 min | 21.0 min (28%) | 4/14 |

### Head-to-Head: SRR24043307-50 SRR24043307-80

| Metric | GCP Batch | Pulsar | Difference |
|--------|-----------|--------|------------|
| **Wall clock** | **129.1 min** | **80.4 min** | **-48.7 min (-38%)** |
| **Compute time** | **162.1 min** | **42.1 min** | **-120.0 min (-74%)** |
| **Scheduling overhead** | **-33.0 min** | **38.3 min** | **71.3 min (-216%)** |
| Steps completed | 20/20 | 4/15 | -- |

### Head-to-Head: SRR24043307-50 SRR24043307-80 SRR24043307-full

| Metric | GCP Batch | Pulsar | Difference |
|--------|-----------|--------|------------|
| **Wall clock** | **208.4 min** | **127.7 min** | **-80.7 min (-39%)** |
| **Compute time** | **274.0 min** | **69.2 min** | **-204.8 min (-75%)** |
| **Scheduling overhead** | **-65.6 min** | **58.5 min** | **124.1 min (-189%)** |
| Steps completed | 20/20 | 4/14 | -- |

### Head-to-Head: SRR24043307-80

| Metric | GCP Batch | Pulsar | Difference |
|--------|-----------|--------|------------|
| **Wall clock** | **115.4 min** | **75.7 min** | **-39.7 min (-34%)** |
| **Compute time** | **126.2 min** | **54.8 min** | **-71.4 min (-57%)** |
| **Scheduling overhead** | **-10.8 min** | **21.0 min** | **31.8 min (-294%)** |
| Steps completed | 20/20 | 4/14 | -- |

## Per-Step Compute Time (runtime_seconds)

### SRR24043307-50 SRR24043307-80

| Tool | Batch | Pulsar | Diff | Diff% |
|------|-------|--------|------|-------|
| cufflinks * | 4176s | 0s | -4176s | -100% |
| rna_star | 2664s | 2160s | -504s | -19% |
| bamFilter * | 1103s | 0s | -1103s | -100% |
| revertR2orientationInBam * | 471s | 0s | -471s | -100% |
| cutadapt | 429s | 359s | -70s | -16% |
| bedtools_genomecoveragebed * | 742s | 0s | -742s | -100% |
| wig_to_bigWig * | 70s | 0s | -70s | -100% |
| multiqc | 16s | 8s | -8s | -50% |
| compose_text_param * | 9s | 0s | -9s | -100% |
| param_value_from_file * | 9s | 0s | -9s | -100% |
| map_param_value * | 37s | 0s | -37s | -100% |
| tp_awk_tool | 1s | 0s | -1s | -- |
| **Total** | **9727s** | **2527s** | **-7200s** | **-74%** |

*Tools only on Batch: cufflinks, bamFilter, revertR2orientationInBam, bedtools_genomecoveragebed, wig_to_bigWig, compose_text_param, param_value_from_file, map_param_value*

### SRR24043307-50 SRR24043307-80 SRR24043307-full

| Tool | Batch | Pulsar | Diff | Diff% |
|------|-------|--------|------|-------|
| cufflinks * | 6842s | 0s | -6842s | -100% |
| rna_star | 4240s | 3431s | -809s | -19% |
| bamFilter * | 2107s | 0s | -2107s | -100% |
| revertR2orientationInBam * | 911s | 0s | -911s | -100% |
| cutadapt | 837s | 714s | -123s | -15% |
| bedtools_genomecoveragebed * | 1337s | 0s | -1337s | -100% |
| wig_to_bigWig * | 98s | 0s | -98s | -100% |
| multiqc | 17s | 8s | -9s | -53% |
| compose_text_param * | 10s | 0s | -10s | -100% |
| param_value_from_file * | 9s | 0s | -9s | -100% |
| map_param_value * | 34s | 0s | -34s | -100% |
| tp_awk_tool | 0s | 0s | +0s | -- |
| **Total** | **16442s** | **4153s** | **-12289s** | **-75%** |

*Tools only on Batch: cufflinks, bamFilter, revertR2orientationInBam, bedtools_genomecoveragebed, wig_to_bigWig, compose_text_param, param_value_from_file, map_param_value*

### SRR24043307-80

| Tool | Batch | Pulsar | Diff | Diff% |
|------|-------|--------|------|-------|
| cufflinks * | 2600s | 0s | -2600s | -100% |
| rna_star | 3691s | 3131s | -560s | -15% |
| bamFilter * | 449s | 0s | -449s | -100% |
| revertR2orientationInBam * | 209s | 0s | -209s | -100% |
| cutadapt | 174s | 146s | -28s | -16% |
| bedtools_genomecoveragebed * | 332s | 0s | -332s | -100% |
| wig_to_bigWig * | 42s | 0s | -42s | -100% |
| multiqc | 16s | 8s | -8s | -50% |
| compose_text_param * | 9s | 0s | -9s | -100% |
| param_value_from_file * | 10s | 0s | -10s | -100% |
| map_param_value * | 38s | 0s | -38s | -100% |
| tp_awk_tool | 0s | 0s | +0s | -- |
| **Total** | **7570s** | **3285s** | **-4285s** | **-57%** |

*Tools only on Batch: cufflinks, bamFilter, revertR2orientationInBam, bedtools_genomecoveragebed, wig_to_bigWig, compose_text_param, param_value_from_file, map_param_value*

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
| wig_to_bigWig | 1 |
| multiqc | 1 |
| compose_text_param | 1 |
| param_value_from_file | 1 |
| map_param_value | 1 |
| tp_awk_tool | 1 |

### Runtime Ratio Analysis (SRR24043307-50 SRR24043307-80)

| Tool | Batch Slots | Pulsar/Batch Ratio | Expected if 1 Thread |
|------|------------|-------------------|---------------------|
| rna_star | 10 | 0.81x | ~10x |
| cutadapt | 8 | 0.84x | ~8x |
| multiqc | 1 | 0.50x | ~1x |

## Wall Clock vs Compute Time Analysis

| Runner | Input | Wall Clock | Compute | Overhead | Overhead % |
|--------|-------|-----------|---------|----------|------------|
| batch R1 | SRR24043307-50 SRR24043307-80 | 129.1m | 162.1m | -33.0m | -26% |
| batch R1 | SRR24043307-50 SRR24043307-80 SRR24043307-full | 208.4m | 274.0m | -65.6m | -31% |
| batch R1 | SRR24043307-80 | 115.4m | 126.2m | -10.8m | -9% |
| pulsar R1 | SRR24043307-50 SRR24043307-80 | 80.4m | 42.1m | 38.3m | 48% |
| pulsar R1 | SRR24043307-50 SRR24043307-80 SRR24043307-full | 127.7m | 69.2m | 58.5m | 46% |
| pulsar R1 | SRR24043307-80 | 75.7m | 54.8m | 21.0m | 28% |

## Batch Scaling Analysis

| Input | Wall Clock | Compute |
|-------|-----------|---------|
| SRR24043307-50 SRR24043307-80 | 129.1m | 162.1m |
| SRR24043307-50 SRR24043307-80 SRR24043307-full | 208.4m | 274.0m |
| SRR24043307-80 | 115.4m | 126.2m |

## Key Findings

### 1. SRR24043307-50 SRR24043307-80: Pulsar is -38% slower (wall clock)

- Wall clock: 80.4m vs 129.1m
- Compute: 42.1m vs 162.1m (-74%)

### 2. SRR24043307-50 SRR24043307-80 SRR24043307-full: Pulsar is -39% slower (wall clock)

- Wall clock: 127.7m vs 208.4m
- Compute: 69.2m vs 274.0m (-75%)

### 3. SRR24043307-80: Pulsar is -34% slower (wall clock)

- Wall clock: 75.7m vs 115.4m
- Compute: 54.8m vs 126.2m (-57%)

### 4. Several tools are faster on Pulsar

- **multiqc** (SRR24043307-50 SRR24043307-80): -50% (8s vs 16s)

### 5. Scheduling overhead is Pulsar's major cost

- Batch: -1.8 min/step avg
- Pulsar: 2.7 min/step avg

## Implications

- **Pulsar's staging overhead is inherent** to the AMQP sidecar architecture. Dominates for short multi-step workflows, negligible for long-running single-step jobs.
- **Pulsar's I/O model has advantages.** Local SSD staging benefits I/O-bound tools.
