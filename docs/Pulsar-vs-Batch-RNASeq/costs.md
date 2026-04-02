---
title: RNASeq Cost Summary
---

# RNASeq Cost Summary

**[Home](../index.html)** | **[Interactive Cost Charts](cost-charts.html)** | **[Performance Report](index.html)** | **[Performance Charts](charts.html)**

**Period:** 2026-03-31 01:03:07 to 2026-03-31 08:30:55 UTC  
**Region:** us-east4  
**Total Jobs:** 126 (ok)

## Estimated Cost (Wallclock)

Cost based on total VM lifetime per job (Galaxy create_time to update_time), including VM provisioning, image pull, file staging, compute, and shutdown.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 46 | 26.5h | $3.48 | $2.02 | $0.00 | $0.11 | **$5.61** |
| **Pulsar** | 20 | 11.1h | $1.42 | $0.84 | $0.23 | $0.05 | **$2.53** |
| **Single** | 60 | 27.6h | $4.20 | $2.63 | $0.00 | $0.11 | **$6.94** |
| **Total** | 126 | 65.2h | $9.10 | $5.49 | $0.23 | $0.27 | **$15.08** |

### Galaxy Host VM Cost

Each runner requires a Galaxy host VM (e2-standard-4, 4 vCPU, 16 GB). Duration is summed per-run (per workflow invocation), not the full experiment window.

| Runner | Duration | Galaxy VM Cost |
|--------|----------|----------------|
| **Batch** | 4.4h | $0.60 |
| **Pulsar** | 1.6h | $0.22 |
| **Single** | 7.4h | $1.02 |

### Total Estimated Cost (Batch Jobs + Galaxy VM)

| Runner | Job Cost | Galaxy VM Cost | **Total** |
|--------|----------|----------------|-----------|
| **Batch** | $5.61 | $0.60 | **$6.21** |
| **Pulsar** | $2.53 | $0.22 | **$2.75** |
| **Single** | $6.94 | $1.02 | **$7.96** |

## Compute-Only Cost (cgroups)

Cost based on cgroups `runtime_seconds` — actual CPU time inside the container.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 46 | 5.1h | $1.56 | $0.84 | $0.00 | $0.02 | **$2.41** |
| **Pulsar** | 20 | 1.6h | $0.51 | $0.27 | $0.03 | $0.01 | **$0.82** |
| **Single** | 60 | 6.3h | $2.12 | $1.14 | $0.00 | $0.03 | **$3.28** |
| **Total** | 126 | 13.0h | $4.18 | $2.25 | $0.03 | $0.05 | **$6.52** |

### Wallclock vs Compute Overhead

| Runner | Compute Cost | Wallclock Cost | Overhead Ratio |
|--------|-------------|----------------|----------------|
| **Batch** | $2.41 | $5.61 | 2.3x |
| **Pulsar** | $0.82 | $2.53 | 3.1x |
| **Single** | $3.28 | $6.94 | 2.1x |

## Per-Tool Cost Comparison (Wallclock)

| Tool | vCPU | Batch Jobs | Batch Cost | Batch $/Job | Pulsar Jobs | Pulsar Cost | Pulsar $/Job | Single Jobs | Single Cost | Single $/Job | Rainstone Est. |
|------|------| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| rna_star | 16 | 2 | $1.68 | $0.8393 | 1 | $0.72 | $0.7209 | 3 | $2.81 | $0.9372 | $0.9108 |
| cufflinks | 8 | 2 | $1.58 | $0.7877 | 1 | $0.64 | $0.6441 | 3 | $1.92 | $0.6409 | $0.2317 |
| wig_to_bigWig | 2 | 6 | $0.32 | $0.0530 | 3 | $0.19 | $0.0627 | 9 | $1.02 | $0.1131 | -- |
| multiqc | 2 | 2 | $0.30 | $0.1512 | 1 | $0.15 | $0.1536 | 3 | $0.50 | $0.1678 | $0.0013 |
| bamFilter | 2 | 2 | $0.27 | $0.1356 | 1 | $0.13 | $0.1324 | 3 | $0.49 | $0.1636 | -- |
| tp_awk_tool | 2 | 4 | $0.44 | $0.1097 | 2 | $0.23 | $0.1165 | 6 | $0.00 | $0.0000 | $0.0017 |
| revertR2orientationInBam | 2 | 2 | $0.30 | $0.1504 | 1 | $0.15 | $0.1508 | 3 | $0.00 | $0.0000 | -- |
| cutadapt | 8 | 3 | $0.19 | $0.0648 | 1 | $0.06 | $0.0574 | 3 | $0.19 | $0.0648 | $0.0182 |
| param_value_from_file | 2 | 2 | $0.23 | $0.1171 | 1 | $0.12 | $0.1158 | 3 | $0.00 | $0.0000 | $0.0003 |
| bedtools_genomecoveragebed | 2 | 6 | $0.22 | $0.0363 | 3 | $0.13 | $0.0425 | 9 | $0.00 | $0.0000 | $0.0016 |
| map_param_value | 2 | 12 | $0.06 | $0.0051 | 4 | $0.01 | $0.0023 | 12 | $0.00 | $0.0000 | -- |
| compose_text_param | 2 | 3 | $0.02 | $0.0054 | 1 | $0.00 | $0.0015 | 3 | $0.00 | $0.0000 | -- |

## Rainstone Comparison

Per-job compute cost comparison against [Rainstone](https://rainstone.anvilproject.org) historical averages from usegalaxy.org. Rainstone data reflects median costs across thousands of production runs.

| Tool | Batch $/Job | Pulsar $/Job | Single $/Job | Rainstone Avg | Rainstone Median | Rainstone P95 | usegalaxy.org Jobs |
|------| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| rna_star | $0.7091 | $0.5191 | $0.7604 | $0.9108 | $0.2144 | $4.3362 | 124,843 |
| cufflinks | $0.3696 | $0.2443 | $0.2441 | $0.2317 | $0.0413 | $1.0701 | 29,585 |
| wig_to_bigWig | $0.0007 | $0.0006 | $0.0009 | -- | -- | -- | -- |
| multiqc | $0.0006 | $0.0003 | $0.0005 | $0.0013 | $0.0005 | $0.0036 | 75,021 |
| bamFilter | $0.0217 | $0.0124 | $0.0360 | -- | -- | -- | -- |
| tp_awk_tool | $0.0000 | $0.0000 | $0.0000 | $0.0017 | $0.0002 | $0.0074 | 16,297 |
| revertR2orientationInBam | $0.0097 | $0.0071 | $0.0000 | -- | -- | -- | -- |
| cutadapt | $0.0512 | $0.0169 | $0.0503 | $0.0182 | $0.0028 | $0.0703 | 167,606 |
| param_value_from_file | $0.0003 | $0.0010 | $0.0000 | $0.0003 | $0.0002 | $0.0004 | 11,628 |
| bedtools_genomecoveragebed | $0.0051 | $0.0035 | $0.0000 | $0.0016 | $0.0003 | $0.0056 | 47,439 |
| map_param_value | $0.0002 | $0.0014 | $0.0000 | -- | -- | -- | -- |
| compose_text_param | $0.0003 | $0.0013 | $0.0000 | -- | -- | -- | -- |

## Deployment Model Comparison

GCP Batch approach (Galaxy + per-job VMs) vs traditional deployment (single n2-standard-20 VM running for the experiment duration).

| Model | Runner | Duration | Job Cost | Galaxy VM | **Total** |
|-------|--------|----------|----------|-----------|-----------|
| **GCP Batch** | Batch | 4.4h | $5.61 | $0.60 | **$6.21** |
| **Local VM** | Batch | 4.4h | -- | $4.25 | **$4.25** |
| **GCP Batch** | Pulsar | 1.6h | $2.53 | $0.22 | **$2.75** |
| **Local VM** | Pulsar | 1.6h | -- | $1.54 | **$1.54** |
| **GCP Batch** | Single | 7.4h | $6.94 | $1.02 | **$7.96** |
| **Local VM** | Single | 7.4h | -- | $7.23 | **$7.23** |

**Batch**: GCP Batch is **46% more expensive** than a local n2-standard-20 ($6.21 vs $4.25).
**Pulsar**: GCP Batch is **79% more expensive** than a local n2-standard-20 ($2.75 vs $1.54).
**Single**: GCP Batch is **10% more expensive** than a local n2-standard-20 ($7.96 vs $7.23).

## Pricing Assumptions

All costs estimated using GCP on-demand pricing for `us-east4`.

| Resource | Rate |
|----------|------|
| N2 vCPU | $0.031611/vCPU/hour |
| N2 Memory | $0.004237/GB/hour |
| Local SSD | $5.4e-05/GB/hour |
| Boot Disk (pd-balanced) | $0.1/GB/month |
| Galaxy VM (e2-standard-4) | $0.1375/hour |
| Local n2-standard-20 | $0.9712/hour |

Rainstone estimates are sourced from the [Rainstone Cost API](https://rainstone.anvilproject.org/api/docs) and reflect historical averages across usegalaxy.org production workloads.
