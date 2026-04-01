---
title: RNASeq Benchmark
---

# RNASeq Benchmark

**[Home](../index.html)** | **[Interactive Charts](charts.html)** | **[Cost Summary](costs.html)** | **[Cost Charts](cost-charts.html)**

## Experiment Setup

- **Workflow:** RNASeq (12 unique tool types)
- **Galaxy version:** 26.1
- **Infrastructure:** GCE VM on RKE2 Kubernetes (us-east4)
- **Runners:** batch, pulsar, single
- **Batch server:** http://34.11.12.196
- **Pulsar server:** http://35.188.245.115
- **Single server:** http://35.194.88.166
- **Date:** 2026-03-31 to 2026-03-31

### Workflow Runs

7 workflow invocations, 137 total jobs (126 succeeded, 11 failed/errored).

### Failed/Errored Jobs

| Cloud | Tool | State | Count |
|-------|------|-------|-------|
| batch | bamFilter | error | 1 |
| batch | cufflinks | error | 1 |
| batch | multiqc | queued | 1 |
| batch | param_value_from_file | new | 1 |
| batch | revertR2orientationInBam | paused | 1 |
| batch | rna_star | error | 1 |
| batch | rna_star | new | 1 |
| batch | tp_awk_tool | error | 2 |
| batch | tp_awk_tool | new | 2 |

## Results Summary

### All Runs

| Runner | Run | Input Size | Wall Clock | Compute Time | Scheduling Overhead | Steps OK |
|--------|-----|------------|-----------|-------------|-------------------|----------|
| batch | 1 | 2GB | 94.9 min | 106.1 min | -11.3 min (-12%) | 20/20 |
| batch | 1 | 5GB | 152.0 min | 184.9 min | -32.9 min (-22%) | 20/20 |
| batch | 1 | 10GB | 69.8 min | 14.5 min | 55.3 min (79%) | 6/17 |
| pulsar | 1 | 2GB | 95.1 min | 96.3 min | -1.2 min (-1%) | 20/20 |
| single | 1 | 2GB | 95.1 min | 112.5 min | -17.4 min (-18%) | 20/20 |
| single | 1 | 5GB | 149.5 min | 190.8 min | -41.3 min (-28%) | 20/20 |
| single | 1 | 10GB | 202.0 min | 171.8 min | 30.2 min (15%) | 20/20 |

### Comparison: 2GB

| Metric | Batch | Pulsar | Single |
|--------| ----- | ------ | ------ |
| **Wall clock** | 94.9 min | 95.1 min | 95.1 min |
| **Compute time** | 106.1 min | 96.3 min | 112.5 min |
| **Scheduling overhead** | -11.3 min | -1.2 min | -17.4 min |
| Steps completed | 20/20 | 20/20 | 20/20 |

### Comparison: 5GB

| Metric | Batch | Single |
|--------| ----- | ------ |
| **Wall clock** | 152.0 min | 149.5 min |
| **Compute time** | 184.9 min | 190.8 min |
| **Scheduling overhead** | -32.9 min | -41.3 min |
| Steps completed | 20/20 | 20/20 |

### Comparison: 10GB

| Metric | Batch | Single |
|--------| ----- | ------ |
| **Wall clock** | 69.8 min | 202.0 min |
| **Compute time** | 14.5 min | 171.8 min |
| **Scheduling overhead** | 55.3 min | 30.2 min |
| Steps completed | 6/17 | 20/20 |

## Per-Step Compute Time (runtime_seconds)

### 2GB

| Tool | Batch | Pulsar | Single |
|------| ------- | ------- | ------- |
| rna_star | 2618s | 2332s | 2600s |
| cufflinks | 2501s | 2130s | 2527s |
| bamFilter | 440s | 366s | 444s |
| revertR2orientationInBam | 191s | 211s | 246s |
| cutadapt | 171s | 147s | 170s |
| bedtools_genomecoveragebed | 331s | 310s | 493s |
| compose_text_param | 10s | 39s | 42s |
| map_param_value | 35s | 166s | 140s |
| param_value_from_file | 9s | 31s | 31s |
| wig_to_bigWig | 44s | 39s | 46s |
| multiqc | 16s | 8s | 14s |
| tp_awk_tool | 1s | 0s | 0s |
| **Total** | **6367s** | **5779s** | **6753s** |

### 5GB

| Tool | Batch | Single |
|------| ------- | ------- |
| rna_star | 3918s | 3903s |
| cufflinks | 4277s | 4188s |
| bamFilter | 1100s | 1059s |
| revertR2orientationInBam | 501s | 565s |
| cutadapt | 416s | 410s |
| bedtools_genomecoveragebed | 746s | 1008s |
| compose_text_param | 8s | 45s |
| map_param_value | 35s | 157s |
| param_value_from_file | 9s | 27s |
| wig_to_bigWig | 69s | 71s |
| multiqc | 14s | 13s |
| tp_awk_tool | 1s | 0s |
| **Total** | **11094s** | **11446s** |

### 10GB

| Tool | Batch | Single |
|------| ------- | ------- |
| rna_star | 0s | 4011s |
| cufflinks | 0s | 0s |
| bamFilter | 0s | 2337s |
| revertR2orientationInBam | 0s | 1118s |
| cutadapt | 820s | 803s |
| bedtools_genomecoveragebed | 0s | 1725s |
| compose_text_param | 12s | 40s |
| map_param_value | 36s | 138s |
| param_value_from_file | 0s | 26s |
| wig_to_bigWig | 0s | 97s |
| multiqc | 0s | 13s |
| tp_awk_tool | 0s | 0s |
| **Total** | **868s** | **10308s** |

## Wall Clock vs Compute Time

| Runner | Input | Wall Clock | Compute | Overhead | Overhead % |
|--------|-------|-----------|---------|----------|------------|
| batch R1 | 2GB | 94.9m | 106.1m | -11.3m | -12% |
| batch R1 | 5GB | 152.0m | 184.9m | -32.9m | -22% |
| batch R1 | 10GB | 69.8m | 14.5m | 55.3m | 79% |
| pulsar R1 | 2GB | 95.1m | 96.3m | -1.2m | -1% |
| single R1 | 2GB | 95.1m | 112.5m | -17.4m | -18% |
| single R1 | 5GB | 149.5m | 190.8m | -41.3m | -28% |
| single R1 | 10GB | 202.0m | 171.8m | 30.2m | 15% |

## Batch Scaling Analysis

| Input | Wall Clock | Compute |
|-------|-----------|---------|
| 2GB | 94.9m | 106.1m |
| 5GB | 152.0m | 184.9m |
| 10GB | 69.8m | 14.5m |

## Single Scaling Analysis

| Input | Wall Clock | Compute |
|-------|-----------|---------|
| 2GB | 95.1m | 112.5m |
| 5GB | 149.5m | 190.8m |
| 10GB | 202.0m | 171.8m |

## Key Findings

### 1. 2GB: Wall clock comparison

- **Batch**: 94.9m (fastest)
- **Pulsar**: 95.1m (+0%)
- **Single**: 95.1m (+0%)

### 2. 5GB: Wall clock comparison

- **Batch**: 152.0m (+2%)
- **Single**: 149.5m (fastest)

### 3. 10GB: Wall clock comparison

- **Batch**: 69.8m (fastest)
- **Single**: 202.0m (+189%)

### 4. Scheduling overhead per step

- **Batch**: 0.3 min/step avg
- **Pulsar**: -0.1 min/step avg
- **Single**: -0.5 min/step avg
