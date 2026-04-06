---
title: ChiPSeq Benchmark
---

# ChiPSeq Benchmark

**[Home](../index.html)** | **[Interactive Charts](charts.html)** | **[Cost Summary](costs.html)** | **[Cost Charts](cost-charts.html)**

## Experiment Setup

- **Workflow:** ChiPSeq (7 unique tool types)
- **Galaxy version:** 26.1
- **Infrastructure:** GCE VM on RKE2 Kubernetes (us-east4)
- **Runners:** batch, pulsar, single
- **Batch server:** http://34.11.12.196
- **Pulsar server:** http://35.188.245.115
- **Batch+K8s server:** http://35.194.88.166
- **Date:** 2026-03-30 to 2026-03-30

### Workflow Runs

9 workflow invocations, 63 total jobs. All completed successfully.

## Results Summary

### All Runs

| Runner | Run | Input Size | Wall Clock | Compute Time | Scheduling Overhead | Steps OK |
|--------|-----|------------|-----------|-------------|-------------------|----------|
| batch | 1 | 2GB | 56.6 min | 44.3 min | 12.2 min (22%) | 7/7 |
| batch | 1 | 5GB | 120.5 min | 107.2 min | 13.3 min (11%) | 7/7 |
| batch | 1 | 10GB | 212.6 min | 196.8 min | 15.8 min (7%) | 7/7 |
| pulsar | 1 | 2GB | 74.0 min | 40.1 min | 33.8 min (46%) | 7/7 |
| pulsar | 1 | 5GB | 154.7 min | 98.3 min | 56.3 min (36%) | 7/7 |
| pulsar | 1 | 10GB | 281.2 min | 187.6 min | 93.6 min (33%) | 7/7 |
| single | 1 | 2GB | 55.8 min | 44.2 min | 11.6 min (21%) | 7/7 |
| single | 1 | 5GB | 120.2 min | 106.9 min | 13.3 min (11%) | 7/7 |
| single | 1 | 10GB | 215.9 min | 198.8 min | 17.1 min (8%) | 7/7 |

### Comparison: 2GB

| Metric | Batch | Pulsar | Batch+K8s |
|--------| ----- | ------ | --------- |
| **Wall clock** | 56.6 min | 74.0 min | 55.8 min |
| **Compute time** | 44.3 min | 40.1 min | 44.2 min |
| **Scheduling overhead** | 12.2 min | 33.8 min | 11.6 min |
| Steps completed | 7/7 | 7/7 | 7/7 |

### Comparison: 5GB

| Metric | Batch | Pulsar | Batch+K8s |
|--------| ----- | ------ | --------- |
| **Wall clock** | 120.5 min | 154.7 min | 120.2 min |
| **Compute time** | 107.2 min | 98.3 min | 106.9 min |
| **Scheduling overhead** | 13.3 min | 56.3 min | 13.3 min |
| Steps completed | 7/7 | 7/7 | 7/7 |

### Comparison: 10GB

| Metric | Batch | Pulsar | Batch+K8s |
|--------| ----- | ------ | --------- |
| **Wall clock** | 212.6 min | 281.2 min | 215.9 min |
| **Compute time** | 196.8 min | 187.6 min | 198.8 min |
| **Scheduling overhead** | 15.8 min | 93.6 min | 17.1 min |
| Steps completed | 7/7 | 7/7 | 7/7 |

## Per-Step Compute Time (runtime_seconds)

### 2GB

| Tool | Batch | Pulsar | Batch+K8s |
|------| ------- | ------- | ------- |
| bowtie2 | 2053s | 1898s | 2061s |
| macs2_callpeak | 231s | 190s | 225s |
| samtool_filter2 | 181s | 140s | 172s |
| fastp | 123s | 119s | 122s |
| wig_to_bigWig | 46s | 46s | 47s |
| multiqc | 26s | 16s | 25s |
| tp_grep_tool | 0s | 0s | 0s |
| **Total** | **2660s** | **2409s** | **2652s** |

### 5GB

| Tool | Batch | Pulsar | Batch+K8s |
|------| ------- | ------- | ------- |
| bowtie2 | 5087s | 4753s | 5048s |
| macs2_callpeak | 496s | 409s | 526s |
| samtool_filter2 | 423s | 339s | 418s |
| fastp | 300s | 292s | 301s |
| wig_to_bigWig | 96s | 93s | 98s |
| multiqc | 29s | 14s | 25s |
| tp_grep_tool | 0s | 0s | 0s |
| **Total** | **6431s** | **5900s** | **6416s** |

### 10GB

| Tool | Batch | Pulsar | Batch+K8s |
|------| ------- | ------- | ------- |
| bowtie2 | 9638s | 9380s | 9795s |
| macs2_callpeak | 857s | 751s | 845s |
| samtool_filter2 | 815s | 652s | 780s |
| fastp | 343s | 332s | 348s |
| wig_to_bigWig | 131s | 126s | 132s |
| multiqc | 27s | 15s | 28s |
| tp_grep_tool | 0s | 0s | 0s |
| **Total** | **11811s** | **11256s** | **11928s** |

## Wall Clock vs Compute Time

| Runner | Input | Wall Clock | Compute | Overhead | Overhead % |
|--------|-------|-----------|---------|----------|------------|
| batch R1 | 2GB | 56.6m | 44.3m | 12.2m | 22% |
| batch R1 | 5GB | 120.5m | 107.2m | 13.3m | 11% |
| batch R1 | 10GB | 212.6m | 196.8m | 15.8m | 7% |
| pulsar R1 | 2GB | 74.0m | 40.1m | 33.8m | 46% |
| pulsar R1 | 5GB | 154.7m | 98.3m | 56.3m | 36% |
| pulsar R1 | 10GB | 281.2m | 187.6m | 93.6m | 33% |
| single R1 | 2GB | 55.8m | 44.2m | 11.6m | 21% |
| single R1 | 5GB | 120.2m | 106.9m | 13.3m | 11% |
| single R1 | 10GB | 215.9m | 198.8m | 17.1m | 8% |

## Batch Scaling Analysis

| Input | Wall Clock | Compute |
|-------|-----------|---------|
| 2GB | 56.6m | 44.3m |
| 5GB | 120.5m | 107.2m |
| 10GB | 212.6m | 196.8m |

## Pulsar Scaling Analysis

| Input | Wall Clock | Compute |
|-------|-----------|---------|
| 2GB | 74.0m | 40.1m |
| 5GB | 154.7m | 98.3m |
| 10GB | 281.2m | 187.6m |

## Batch+K8s Scaling Analysis

| Input | Wall Clock | Compute |
|-------|-----------|---------|
| 2GB | 55.8m | 44.2m |
| 5GB | 120.2m | 106.9m |
| 10GB | 215.9m | 198.8m |

## Key Findings

### 1. 2GB: Wall clock comparison

- **Batch**: 56.6m (+1%)
- **Pulsar**: 74.0m (+32%)
- **Batch+K8s**: 55.8m (fastest)

### 2. 5GB: Wall clock comparison

- **Batch**: 120.5m (+0%)
- **Pulsar**: 154.7m (+29%)
- **Batch+K8s**: 120.2m (fastest)

### 3. 10GB: Wall clock comparison

- **Batch**: 212.6m (fastest)
- **Pulsar**: 281.2m (+32%)
- **Batch+K8s**: 215.9m (+2%)

### 4. Scheduling overhead per step

- **Batch**: 2.0 min/step avg
- **Pulsar**: 8.7 min/step avg
- **Batch+K8s**: 2.0 min/step avg
