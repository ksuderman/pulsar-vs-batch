---
title: Variant Benchmark
---

# Variant Benchmark

**[Home](../index.html)** | **[Interactive Charts](charts.html)** | **[Cost Summary](costs.html)** | **[Cost Charts](cost-charts.html)**

## Experiment Setup

- **Workflow:** Variant (12 unique tool types)
- **Galaxy version:** 26.1
- **Infrastructure:** GCE VM on RKE2 Kubernetes (us-east4)
- **Runners:** batch, pulsar, single
- **Batch server:** http://34.11.12.196
- **Pulsar server:** http://35.188.245.115
- **Single server:** http://35.194.88.166
- **Date:** 2026-03-31 to 2026-04-01

### Workflow Runs

9 workflow invocations, 111 total jobs (98 succeeded, 13 failed/errored).

### Failed/Errored Jobs

| Cloud | Tool | State | Count |
|-------|------|-------|-------|
| batch | bwa_mem | error | 2 |
| batch | bwa_mem | new | 1 |
| batch | lofreq_call | paused | 1 |
| batch | lofreq_filter | paused | 1 |
| batch | lofreq_indelqual | paused | 1 |
| batch | lofreq_viterbi | paused | 1 |
| batch | multiqc | paused | 1 |
| batch | picard_MarkDuplicates | paused | 1 |
| batch | samtools_stats | paused | 1 |
| batch | samtools_view | error | 1 |
| batch | snpEff | paused | 1 |
| pulsar | samtools_view | error | 1 |

## Results Summary

### All Runs

| Runner | Run | Input Size | Wall Clock | Compute Time | Scheduling Overhead | Steps OK |
|--------|-----|------------|-----------|-------------|-------------------|----------|
| batch | 1 | 2GB | 205.6 min | 186.2 min | 19.4 min (9%) | 12/12 |
| batch | 1 | 5GB | 337.6 min | 320.9 min | 16.7 min (5%) | 12/12 |
| batch | 1 | 10GB | 111.5 min | 25.1 min | 86.4 min (77%) | 2/14 |
| pulsar | 1 | 2GB | 236.0 min | 157.1 min | 78.9 min (33%) | 12/13 |
| pulsar | 1 | 5GB | 374.4 min | 277.6 min | 96.9 min (26%) | 12/12 |
| pulsar | 1 | 10GB | 579.5 min | 447.7 min | 131.8 min (23%) | 12/12 |
| single | 1 | 2GB | 194.5 min | 177.5 min | 16.9 min (9%) | 12/12 |
| single | 1 | 5GB | 323.5 min | 309.8 min | 13.6 min (4%) | 12/12 |
| single | 1 | 10GB | 508.1 min | 491.5 min | 16.6 min (3%) | 12/12 |

### Comparison: 2GB

| Metric | Batch | Pulsar | Single |
|--------| ----- | ------ | ------ |
| **Wall clock** | 205.6 min | 236.0 min | 194.5 min |
| **Compute time** | 186.2 min | 157.1 min | 177.5 min |
| **Scheduling overhead** | 19.4 min | 78.9 min | 16.9 min |
| Steps completed | 12/12 | 12/13 | 12/12 |

### Comparison: 5GB

| Metric | Batch | Pulsar | Single |
|--------| ----- | ------ | ------ |
| **Wall clock** | 337.6 min | 374.4 min | 323.5 min |
| **Compute time** | 320.9 min | 277.6 min | 309.8 min |
| **Scheduling overhead** | 16.7 min | 96.9 min | 13.6 min |
| Steps completed | 12/12 | 12/12 | 12/12 |

### Comparison: 10GB

| Metric | Batch | Pulsar | Single |
|--------| ----- | ------ | ------ |
| **Wall clock** | 111.5 min | 579.5 min | 508.1 min |
| **Compute time** | 25.1 min | 447.7 min | 491.5 min |
| **Scheduling overhead** | 86.4 min | 131.8 min | 16.6 min |
| Steps completed | 2/14 | 12/12 | 12/12 |

## Per-Step Compute Time (runtime_seconds)

### 2GB

| Tool | Batch | Pulsar | Single |
|------| ------- | ------- | ------- |
| lofreq_call | 3948s | 3872s | 3973s |
| bwa_mem | 4496s | 4319s | 4409s |
| picard_MarkDuplicates | 491s | 298s | 473s |
| snpEff_build_gb | 1295s | 179s | 857s |
| lofreq_viterbi | 355s | 287s | 351s |
| lofreq_indelqual | 226s | 158s | 223s |
| fastp | 162s | 159s | 166s |
| samtools_view | 145s | 98s | 140s |
| samtools_stats | 46s | 47s | 46s |
| snpEff | 0s | 4s | 6s |
| multiqc | 8s | 3s | 7s |
| lofreq_filter | 1s | 0s | 1s |
| **Total** | **11173s** | **9424s** | **10652s** |

### 5GB

| Tool | Batch | Pulsar | Single |
|------| ------- | ------- | ------- |
| lofreq_call | 8479s | 8383s | 8546s |
| bwa_mem | 6437s | 5704s | 6015s |
| picard_MarkDuplicates | 1258s | 710s | 1150s |
| snpEff_build_gb | 1095s | 176s | 832s |
| lofreq_viterbi | 734s | 617s | 722s |
| lofreq_indelqual | 406s | 304s | 400s |
| fastp | 401s | 403s | 402s |
| samtools_view | 318s | 237s | 379s |
| samtools_stats | 113s | 105s | 129s |
| snpEff | 6s | 11s | 7s |
| multiqc | 8s | 3s | 7s |
| lofreq_filter | 1s | 0s | 1s |
| **Total** | **19256s** | **16653s** | **18590s** |

### 10GB

| Tool | Batch | Pulsar | Single |
|------| ------- | ------- | ------- |
| lofreq_call | 0s | 14387s | 14641s |
| bwa_mem | 0s | 8253s | 8545s |
| picard_MarkDuplicates | 0s | 1365s | 2297s |
| snpEff_build_gb | 998s | 174s | 812s |
| lofreq_viterbi | 0s | 1047s | 1144s |
| lofreq_indelqual | 0s | 491s | 617s |
| fastp | 510s | 477s | 486s |
| samtools_view | 0s | 457s | 709s |
| samtools_stats | 0s | 204s | 225s |
| snpEff | 0s | 7s | 7s |
| multiqc | 0s | 2s | 7s |
| lofreq_filter | 0s | 0s | 2s |
| **Total** | **1508s** | **26864s** | **29492s** |

## Wall Clock vs Compute Time

| Runner | Input | Wall Clock | Compute | Overhead | Overhead % |
|--------|-------|-----------|---------|----------|------------|
| batch R1 | 2GB | 205.6m | 186.2m | 19.4m | 9% |
| batch R1 | 5GB | 337.6m | 320.9m | 16.7m | 5% |
| batch R1 | 10GB | 111.5m | 25.1m | 86.4m | 77% |
| pulsar R1 | 2GB | 236.0m | 157.1m | 78.9m | 33% |
| pulsar R1 | 5GB | 374.4m | 277.6m | 96.9m | 26% |
| pulsar R1 | 10GB | 579.5m | 447.7m | 131.8m | 23% |
| single R1 | 2GB | 194.5m | 177.5m | 16.9m | 9% |
| single R1 | 5GB | 323.5m | 309.8m | 13.6m | 4% |
| single R1 | 10GB | 508.1m | 491.5m | 16.6m | 3% |

## Batch Scaling Analysis

| Input | Wall Clock | Compute |
|-------|-----------|---------|
| 2GB | 205.6m | 186.2m |
| 5GB | 337.6m | 320.9m |
| 10GB | 111.5m | 25.1m |

## Pulsar Scaling Analysis

| Input | Wall Clock | Compute |
|-------|-----------|---------|
| 2GB | 236.0m | 157.1m |
| 5GB | 374.4m | 277.6m |
| 10GB | 579.5m | 447.7m |

## Single Scaling Analysis

| Input | Wall Clock | Compute |
|-------|-----------|---------|
| 2GB | 194.5m | 177.5m |
| 5GB | 323.5m | 309.8m |
| 10GB | 508.1m | 491.5m |

## Key Findings

### 1. 2GB: Wall clock comparison

- **Batch**: 205.6m (+6%)
- **Pulsar**: 236.0m (+21%)
- **Single**: 194.5m (fastest)

### 2. 5GB: Wall clock comparison

- **Batch**: 337.6m (+4%)
- **Pulsar**: 374.4m (+16%)
- **Single**: 323.5m (fastest)

### 3. 10GB: Wall clock comparison

- **Batch**: 111.5m (fastest)
- **Pulsar**: 579.5m (+420%)
- **Single**: 508.1m (+356%)

### 4. Scheduling overhead per step

- **Batch**: 3.1 min/step avg
- **Pulsar**: 8.4 min/step avg
- **Single**: 1.3 min/step avg
