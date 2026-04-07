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
- **Direct server:** http://34.11.12.196
- **Pulsar server:** http://35.188.245.115
- **Direct+K8s server:** http://35.194.88.166
- **Date:** 2026-03-31 to 2026-04-06

### Workflow Runs

9 workflow invocations, 180 total jobs. All completed successfully.

## Results Summary

### All Runs

| Runner | Run | Input Size | Wall Clock | Compute Time | Scheduling Overhead | Steps OK |
|--------|-----|------------|-----------|-------------|-------------------|----------|
| batch | 1 | 2GB | 94.9 min | 106.1 min | -11.3 min (-12%) | 20/20 |
| batch | 1 | 5GB | 152.0 min | 184.9 min | -32.9 min (-22%) | 20/20 |
| batch | 1 | 10GB | 190.6 min | 257.4 min | -66.8 min (-35%) | 20/20 |
| pulsar | 1 | 2GB | 95.1 min | 96.3 min | -1.2 min (-1%) | 20/20 |
| pulsar | 1 | 5GB | 126.1 min | 136.1 min | -10.0 min (-8%) | 20/20 |
| pulsar | 1 | 10GB | 182.1 min | 201.3 min | -19.2 min (-11%) | 20/20 |
| single | 1 | 2GB | 95.1 min | 112.5 min | -17.4 min (-18%) | 20/20 |
| single | 1 | 5GB | 149.5 min | 190.8 min | -41.3 min (-28%) | 20/20 |
| single | 1 | 10GB | 202.0 min | 171.8 min | 30.2 min (15%) | 20/20 |

### Comparison: 2GB

| Metric | Direct | Pulsar | Direct+K8s |
|--------| ------ | ------ | ---------- |
| **Wall clock** | 94.9 min | 95.1 min | 95.1 min |
| **Compute time** | 106.1 min | 96.3 min | 112.5 min |
| **Scheduling overhead** | -11.3 min | -1.2 min | -17.4 min |
| Steps completed | 20/20 | 20/20 | 20/20 |

### Comparison: 5GB

| Metric | Direct | Pulsar | Direct+K8s |
|--------| ------ | ------ | ---------- |
| **Wall clock** | 152.0 min | 126.1 min | 149.5 min |
| **Compute time** | 184.9 min | 136.1 min | 190.8 min |
| **Scheduling overhead** | -32.9 min | -10.0 min | -41.3 min |
| Steps completed | 20/20 | 20/20 | 20/20 |

### Comparison: 10GB

| Metric | Direct | Pulsar | Direct+K8s |
|--------| ------ | ------ | ---------- |
| **Wall clock** | 190.6 min | 182.1 min | 202.0 min |
| **Compute time** | 257.4 min | 201.3 min | 171.8 min |
| **Scheduling overhead** | -66.8 min | -19.2 min | 30.2 min |
| Steps completed | 20/20 | 20/20 | 20/20 |

## Per-Step Compute Time (runtime_seconds)

### 2GB

| Tool | Direct | Pulsar | Direct+K8s |
|------| ------- | ------- | ------- |
| cufflinks | 2501s | 2130s | 2527s |
| rna_star | 2618s | 2332s | 2600s |
| bamFilter | 440s | 366s | 444s |
| revertR2orientationInBam | 191s | 211s | 246s |
| cutadapt | 171s | 147s | 170s |
| bedtools_genomecoveragebed | 331s | 310s | 493s |
| compose_text_param | 10s | 39s | 42s |
| map_param_value | 35s | 166s | 140s |
| wig_to_bigWig | 44s | 39s | 46s |
| param_value_from_file | 9s | 31s | 31s |
| multiqc | 16s | 8s | 14s |
| tp_awk_tool | 1s | 0s | 0s |
| **Total** | **6367s** | **5779s** | **6753s** |

### 5GB

| Tool | Direct | Pulsar | Direct+K8s |
|------| ------- | ------- | ------- |
| cufflinks | 4277s | 3481s | 4188s |
| rna_star | 3918s | 2029s | 3903s |
| bamFilter | 1100s | 872s | 1059s |
| revertR2orientationInBam | 501s | 473s | 565s |
| cutadapt | 416s | 367s | 410s |
| bedtools_genomecoveragebed | 746s | 630s | 1008s |
| compose_text_param | 8s | 40s | 45s |
| map_param_value | 35s | 173s | 157s |
| wig_to_bigWig | 69s | 65s | 71s |
| param_value_from_file | 9s | 24s | 27s |
| multiqc | 14s | 9s | 13s |
| tp_awk_tool | 1s | 1s | 0s |
| **Total** | **11094s** | **8164s** | **11446s** |

### 10GB

| Tool | Direct | Pulsar | Direct+K8s |
|------| ------- | ------- | ------- |
| cufflinks | 6818s | 4999s | 0s |
| rna_star | 3226s | 2266s | 4011s |
| bamFilter | 2097s | 1720s | 2337s |
| revertR2orientationInBam | 931s | 935s | 1118s |
| cutadapt | 831s | 723s | 803s |
| bedtools_genomecoveragebed | 1373s | 1138s | 1725s |
| compose_text_param | 9s | 36s | 40s |
| map_param_value | 36s | 129s | 138s |
| wig_to_bigWig | 97s | 89s | 97s |
| param_value_from_file | 10s | 34s | 26s |
| multiqc | 14s | 8s | 13s |
| tp_awk_tool | 0s | 1s | 0s |
| **Total** | **15442s** | **12078s** | **10308s** |

## Wall Clock vs Compute Time

| Runner | Input | Wall Clock | Compute | Overhead | Overhead % |
|--------|-------|-----------|---------|----------|------------|
| batch R1 | 2GB | 94.9m | 106.1m | -11.3m | -12% |
| batch R1 | 5GB | 152.0m | 184.9m | -32.9m | -22% |
| batch R1 | 10GB | 190.6m | 257.4m | -66.8m | -35% |
| pulsar R1 | 2GB | 95.1m | 96.3m | -1.2m | -1% |
| pulsar R1 | 5GB | 126.1m | 136.1m | -10.0m | -8% |
| pulsar R1 | 10GB | 182.1m | 201.3m | -19.2m | -11% |
| single R1 | 2GB | 95.1m | 112.5m | -17.4m | -18% |
| single R1 | 5GB | 149.5m | 190.8m | -41.3m | -28% |
| single R1 | 10GB | 202.0m | 171.8m | 30.2m | 15% |

## Direct Scaling Analysis

| Input | Wall Clock | Compute |
|-------|-----------|---------|
| 2GB | 94.9m | 106.1m |
| 5GB | 152.0m | 184.9m |
| 10GB | 190.6m | 257.4m |

## Pulsar Scaling Analysis

| Input | Wall Clock | Compute |
|-------|-----------|---------|
| 2GB | 95.1m | 96.3m |
| 5GB | 126.1m | 136.1m |
| 10GB | 182.1m | 201.3m |

## Direct+K8s Scaling Analysis

| Input | Wall Clock | Compute |
|-------|-----------|---------|
| 2GB | 95.1m | 112.5m |
| 5GB | 149.5m | 190.8m |
| 10GB | 202.0m | 171.8m |

## Key Findings

### 1. 2GB: Wall clock comparison

- **Direct**: 94.9m (fastest)
- **Pulsar**: 95.1m (+0%)
- **Direct+K8s**: 95.1m (+0%)

### 2. 5GB: Wall clock comparison

- **Direct**: 152.0m (+21%)
- **Pulsar**: 126.1m (fastest)
- **Direct+K8s**: 149.5m (+19%)

### 3. 10GB: Wall clock comparison

- **Direct**: 190.6m (+5%)
- **Pulsar**: 182.1m (fastest)
- **Direct+K8s**: 202.0m (+11%)

### 4. Scheduling overhead per step

- **Direct**: -1.8 min/step avg
- **Pulsar**: -0.5 min/step avg
- **Direct+K8s**: -0.5 min/step avg
