---
title: Pulsar vs Direct GCP Batch - Variant Analysis
---

# Pulsar vs Direct GCP Batch: Variant Analysis

**[Interactive Charts](charts.html)** | **[Cost Analysis](costs.md)** | **[Cost Charts](costs.html)**

## Experiment Setup

- **Workflow:** Variant Analysis (12 unique tool types)
- **Galaxy version:** 26.1
- **Infrastructure:** GCE VM on RKE2 Kubernetes, jobs dispatched to GCP Batch VMs (us-east4)
- **Custom VM image:** `galaxy-k8s-minimal-debian12-v2026-03-05` (CVMFS pre-installed)
- **Batch server:** http://34.11.12.196
- **Pulsar server:** http://35.194.76.109
- **Date:** 2026-03-16 to 2026-03-17

### Runners Compared

| Runner | Type | Job Dispatch | File Transfer |
|--------|------|-------------|---------------|
| **GCP Batch** (direct) | `GoogleCloudBatchJobRunner` | Galaxy submits directly to GCP Batch API | Galaxy handles staging natively |
| **Pulsar** (AMQP sidecar) | `PulsarGcpBatchJobRunner` | Galaxy sends AMQP message; Pulsar sidecar stages inputs, runs tool, collects outputs, sends AMQP callback | HTTP upload/download via `remote_transfer` |

### Workflow Runs

6 workflow invocations, 72 total jobs. All completed successfully.

## Results Summary

### All Runs

| Runner | Run | Input Sizes | Wall Clock | Compute Time | Scheduling Overhead | Steps OK |
|--------|-----|-------------|-----------|-------------|-------------------|----------|
| batch | 1 | 10GB | 522.9 min | 501.6 min | 21.3 min (4%) | 12/12 |
| batch | 1 | 2GB | 201.6 min | 182.9 min | 18.7 min (9%) | 12/12 |
| batch | 1 | 5GB | 339.4 min | 320.1 min | 19.3 min (6%) | 12/12 |
| pulsar | 1 | 10GB | 582.5 min | 449.7 min | 132.8 min (23%) | 12/12 |
| pulsar | 1 | 2GB | 230.6 min | 155.3 min | 75.3 min (33%) | 12/12 |
| pulsar | 1 | 5GB | 372.4 min | 276.0 min | 96.5 min (26%) | 12/12 |

### Head-to-Head: 10GB

| Metric | GCP Batch | Pulsar | Difference |
|--------|-----------|--------|------------|
| **Wall clock** | **522.9 min** | **582.5 min** | **59.6 min (+11%)** |
| **Compute time** | **501.6 min** | **449.7 min** | **-51.9 min (-10%)** |
| **Scheduling overhead** | **21.3 min** | **132.8 min** | **111.5 min (+524%)** |
| Steps completed | 12/12 | 12/12 | -- |

### Head-to-Head: 2GB

| Metric | GCP Batch | Pulsar | Difference |
|--------|-----------|--------|------------|
| **Wall clock** | **201.6 min** | **230.6 min** | **29.0 min (+14%)** |
| **Compute time** | **182.9 min** | **155.3 min** | **-27.6 min (-15%)** |
| **Scheduling overhead** | **18.7 min** | **75.3 min** | **56.6 min (+303%)** |
| Steps completed | 12/12 | 12/12 | -- |

### Head-to-Head: 5GB

| Metric | GCP Batch | Pulsar | Difference |
|--------|-----------|--------|------------|
| **Wall clock** | **339.4 min** | **372.4 min** | **33.1 min (+10%)** |
| **Compute time** | **320.1 min** | **276.0 min** | **-44.1 min (-14%)** |
| **Scheduling overhead** | **19.3 min** | **96.5 min** | **77.2 min (+400%)** |
| Steps completed | 12/12 | 12/12 | -- |

## Per-Step Compute Time (runtime_seconds)

### 10GB

| Tool | Batch | Pulsar | Diff | Diff% |
|------|-------|--------|------|-------|
| lofreq_call | 14529s | 14527s | -2s | -0% |
| bwa_mem | 8617s | 8237s | -380s | -4% |
| picard_MarkDuplicates | 2527s | 1363s | -1164s | -46% |
| lofreq_viterbi | 1215s | 1044s | -171s | -14% |
| snpEff_build_gb | 1187s | 177s | -1010s | -85% |
| lofreq_indelqual | 668s | 490s | -178s | -27% |
| fastp | 482s | 477s | -5s | -1% |
| samtools_view | 621s | 455s | -166s | -27% |
| samtools_stats | 235s | 204s | -31s | -13% |
| multiqc | 8s | 3s | -5s | -62% |
| snpEff | 7s | 6s | -1s | -14% |
| lofreq_filter | 2s | 0s | -2s | -100% |
| **Total** | **30098s** | **26983s** | **-3115s** | **-10%** |

### 2GB

| Tool | Batch | Pulsar | Diff | Diff% |
|------|-------|--------|------|-------|
| lofreq_call | 3939s | 3840s | -99s | -3% |
| bwa_mem | 4417s | 4260s | -157s | -4% |
| picard_MarkDuplicates | 547s | 292s | -255s | -47% |
| lofreq_viterbi | 363s | 287s | -76s | -21% |
| snpEff_build_gb | 1097s | 176s | -921s | -84% |
| lofreq_indelqual | 250s | 158s | -92s | -37% |
| fastp | 164s | 157s | -7s | -4% |
| samtools_view | 136s | 101s | -35s | -26% |
| samtools_stats | 48s | 43s | -5s | -10% |
| multiqc | 9s | 3s | -6s | -67% |
| snpEff | 5s | 4s | -1s | -20% |
| lofreq_filter | 1s | 0s | -1s | -- |
| **Total** | **10976s** | **9321s** | **-1655s** | **-15%** |

### 5GB

| Tool | Batch | Pulsar | Diff | Diff% |
|------|-------|--------|------|-------|
| lofreq_call | 8559s | 8362s | -197s | -2% |
| bwa_mem | 6135s | 5639s | -496s | -8% |
| picard_MarkDuplicates | 1358s | 720s | -638s | -47% |
| lofreq_viterbi | 742s | 615s | -127s | -17% |
| snpEff_build_gb | 1122s | 175s | -947s | -84% |
| lofreq_indelqual | 424s | 302s | -122s | -29% |
| fastp | 394s | 393s | -1s | -0% |
| samtools_view | 337s | 238s | -99s | -29% |
| samtools_stats | 113s | 105s | -8s | -7% |
| multiqc | 12s | 3s | -9s | -75% |
| snpEff | 6s | 5s | -1s | -17% |
| lofreq_filter | 2s | 1s | -1s | -50% |
| **Total** | **19204s** | **16558s** | **-2646s** | **-14%** |

## Resource Allocation: VM Sizing vs GALAXY_SLOTS

### VM Right-Sizing (Working)

Pulsar correctly right-sizes GCP Batch VMs based on per-tool resource requirements. The TPV destination passes `cores: "{cores}"` and `mem: "{mem}"` to Pulsar's `parse_gcp_job_params()`, which calls `compute_machine_type()` to select an appropriate N2 machine type.

### GALAXY_SLOTS Reporting (Fixed)

Pulsar now correctly reports GALAXY_SLOTS. The fix injects the proper slot count into the Pulsar task environment, so Galaxy metrics accurately reflect the VM cores allocated to each job.

### Batch Resource Allocation (as reported by Galaxy)

| Tool | CPU Slots |
|------|-----------|
| lofreq_call | 2 |
| bwa_mem | 8 |
| picard_MarkDuplicates | 3 |
| lofreq_viterbi | 4 |
| snpEff_build_gb | 1 |
| lofreq_indelqual | 1 |
| fastp | 4 |
| samtools_view | 1 |
| samtools_stats | 2 |
| multiqc | 1 |
| snpEff | 1 |
| lofreq_filter | 1 |

### Runtime Ratio Analysis (10GB)

| Tool | Batch Slots | Pulsar/Batch Ratio | Expected if 1 Thread |
|------|------------|-------------------|---------------------|
| lofreq_call | 2 | 1.00x | ~2x |
| bwa_mem | 8 | 0.96x | ~8x |
| picard_MarkDuplicates | 3 | 0.54x | ~3x |
| lofreq_viterbi | 4 | 0.86x | ~4x |
| snpEff_build_gb | 1 | 0.15x | ~1x |
| lofreq_indelqual | 1 | 0.73x | ~1x |
| fastp | 4 | 0.99x | ~4x |
| samtools_view | 1 | 0.73x | ~1x |
| samtools_stats | 2 | 0.87x | ~2x |
| multiqc | 1 | 0.38x | ~1x |
| snpEff | 1 | 0.86x | ~1x |

## Wall Clock vs Compute Time Analysis

| Runner | Input | Wall Clock | Compute | Overhead | Overhead % |
|--------|-------|-----------|---------|----------|------------|
| batch R1 | 10GB | 522.9m | 501.6m | 21.3m | 4% |
| batch R1 | 2GB | 201.6m | 182.9m | 18.7m | 9% |
| batch R1 | 5GB | 339.4m | 320.1m | 19.3m | 6% |
| pulsar R1 | 10GB | 582.5m | 449.7m | 132.8m | 23% |
| pulsar R1 | 2GB | 230.6m | 155.3m | 75.3m | 33% |
| pulsar R1 | 5GB | 372.4m | 276.0m | 96.5m | 26% |

## Batch Scaling Analysis

| Input | Wall Clock | Compute |
|-------|-----------|---------|
| 10GB | 522.9m | 501.6m |
| 2GB | 201.6m | 182.9m |
| 5GB | 339.4m | 320.1m |

## Key Findings

### 1. 10GB: Pulsar is +11% slower (wall clock)

- Wall clock: 582.5m vs 522.9m
- Compute: 449.7m vs 501.6m (-10%)

### 2. 2GB: Pulsar is +14% slower (wall clock)

- Wall clock: 230.6m vs 201.6m
- Compute: 155.3m vs 182.9m (-15%)

### 3. 5GB: Pulsar is +10% slower (wall clock)

- Wall clock: 372.4m vs 339.4m
- Compute: 276.0m vs 320.1m (-14%)

### 4. Several tools are faster on Pulsar

- **picard_MarkDuplicates** (10GB): -46% (1363s vs 2527s)
- **snpEff_build_gb** (10GB): -85% (177s vs 1187s)
- **lofreq_indelqual** (10GB): -27% (490s vs 668s)
- **samtools_view** (10GB): -27% (455s vs 621s)
- **multiqc** (10GB): -62% (3s vs 8s)

### 5. Scheduling overhead is Pulsar's major cost

- Batch: 1.6 min/step avg
- Pulsar: 8.5 min/step avg

## Implications

- **Pulsar's staging overhead is inherent** to the AMQP sidecar architecture. Dominates for short multi-step workflows, negligible for long-running single-step jobs.
- **Pulsar's I/O model has advantages.** Local SSD staging benefits I/O-bound tools.
