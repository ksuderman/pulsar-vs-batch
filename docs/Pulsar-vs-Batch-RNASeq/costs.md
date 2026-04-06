---
title: RNASeq Cost Summary
---

# RNASeq Cost Summary

**[Home](../index.html)** | **[Interactive Cost Charts](cost-charts.html)** | **[Performance Report](index.html)** | **[Performance Charts](charts.html)**

**Period:** 2026-03-31 01:03:07 to 2026-04-06 03:51:55 UTC  
**Region:** us-east4  
**Total Jobs:** 240 (ok)

## Estimated Cost (Wallclock)

Cost based on total VM lifetime per job (Galaxy create_time to update_time), including VM provisioning, image pull, file staging, compute, and shutdown.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 60 | 45.9h | $5.85 | $3.44 | $0.00 | $0.19 | **$9.48** |
| **Pulsar** | 60 | 50.4h | $6.13 | $3.67 | $1.02 | $0.21 | **$11.03** |
| **Pulsar+K8s** | 60 | 27.0h | $4.65 | $2.87 | $0.00 | $0.11 | **$7.63** |
| **Batch+K8s** | 60 | 27.6h | $4.20 | $2.63 | $0.00 | $0.11 | **$6.94** |
| **Total** | 240 | 150.9h | $20.82 | $12.61 | $1.02 | $0.63 | **$35.08** |

### Galaxy Host VM Cost

Each runner requires a Galaxy host VM (e2-standard-4, 4 vCPU, 16 GB). Duration is summed per-run (per workflow invocation), not the full experiment window.

| Runner | Duration | Galaxy VM Cost |
|--------|----------|----------------|
| **Batch** | 7.3h | $1.00 |
| **Pulsar** | 6.7h | $0.92 |
| **Pulsar+K8s** | 6.7h | $0.92 |
| **Batch+K8s** | 7.4h | $1.02 |

### Total Estimated Cost (Batch Jobs + Galaxy VM)

| Runner | Job Cost | Galaxy VM Cost | **Total** |
|--------|----------|----------------|-----------|
| **Batch** | $9.48 | $1.00 | **$10.48** |
| **Pulsar** | $11.03 | $0.92 | **$11.95** |
| **Pulsar+K8s** | $7.63 | $0.92 | **$8.56** |
| **Batch+K8s** | $6.94 | $1.02 | **$7.96** |

## Compute-Only Cost (cgroups)

Cost based on cgroups `runtime_seconds` — actual CPU time inside the container.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 60 | 9.1h | $2.57 | $1.38 | $0.00 | $0.04 | **$3.99** |
| **Pulsar** | 60 | 7.2h | $1.90 | $1.02 | $0.15 | $0.03 | **$3.09** |
| **Pulsar+K8s** | 60 | 6.0h | $1.82 | $0.98 | $0.00 | $0.03 | **$2.82** |
| **Batch+K8s** | 60 | 6.3h | $2.12 | $1.14 | $0.00 | $0.03 | **$3.28** |
| **Total** | 240 | 28.7h | $8.40 | $4.51 | $0.15 | $0.12 | **$13.18** |

### Wallclock vs Compute Overhead

| Runner | Compute Cost | Wallclock Cost | Overhead Ratio |
|--------|-------------|----------------|----------------|
| **Batch** | $3.99 | $9.48 | 2.4x |
| **Pulsar** | $3.09 | $11.03 | 3.6x |
| **Pulsar+K8s** | $2.82 | $7.63 | 2.7x |
| **Batch+K8s** | $3.28 | $6.94 | 2.1x |

## Per-Tool Cost Comparison (Wallclock)

| Tool | vCPU | Batch Jobs | Batch Cost | Batch $/Job | Pulsar Jobs | Pulsar Cost | Pulsar $/Job | Pulsar+K8s Jobs | Pulsar+K8s Cost | Pulsar+K8s $/Job | Batch+K8s Jobs | Batch+K8s Cost | Batch+K8s $/Job | Rainstone Est. |
|------|------| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| rna_star | 16 | 3 | $2.65 | $0.8833 | 3 | $2.74 | $0.9118 | 3 | $2.67 | $0.8887 | 3 | $2.81 | $0.9372 | $0.9108 |
| cufflinks | 8 | 3 | $2.80 | $0.9343 | 3 | $2.75 | $0.9154 | 3 | $2.61 | $0.8705 | 3 | $1.92 | $0.6409 | $0.2317 |
| wig_to_bigWig | 2 | 9 | $0.72 | $0.0805 | 9 | $1.17 | $0.1297 | 9 | $1.02 | $0.1128 | 9 | $1.02 | $0.1131 | -- |
| multiqc | 2 | 3 | $0.48 | $0.1587 | 3 | $0.58 | $0.1945 | 3 | $0.51 | $0.1692 | 3 | $0.50 | $0.1678 | $0.0013 |
| bamFilter | 2 | 3 | $0.46 | $0.1545 | 3 | $0.58 | $0.1921 | 3 | $0.48 | $0.1601 | 3 | $0.49 | $0.1636 | -- |
| tp_awk_tool | 2 | 6 | $0.69 | $0.1154 | 6 | $0.89 | $0.1477 | 6 | $0.00 | $0.0000 | 6 | $0.00 | $0.0000 | $0.0017 |
| bedtools_genomecoveragebed | 2 | 9 | $0.51 | $0.0564 | 9 | $0.80 | $0.0891 | 9 | $0.00 | $0.0000 | 9 | $0.00 | $0.0000 | $0.0016 |
| revertR2orientationInBam | 2 | 3 | $0.53 | $0.1754 | 3 | $0.69 | $0.2306 | 3 | $0.00 | $0.0000 | 3 | $0.00 | $0.0000 | -- |
| cutadapt | 8 | 3 | $0.19 | $0.0645 | 3 | $0.37 | $0.1230 | 3 | $0.35 | $0.1170 | 3 | $0.19 | $0.0648 | $0.0182 |
| param_value_from_file | 2 | 3 | $0.37 | $0.1227 | 3 | $0.44 | $0.1473 | 3 | $0.00 | $0.0000 | 3 | $0.00 | $0.0000 | $0.0003 |
| map_param_value | 2 | 12 | $0.06 | $0.0051 | 12 | $0.03 | $0.0021 | 12 | $0.00 | $0.0000 | 12 | $0.00 | $0.0000 | -- |
| compose_text_param | 2 | 3 | $0.01 | $0.0050 | 3 | $0.00 | $0.0014 | 3 | $0.00 | $0.0000 | 3 | $0.00 | $0.0000 | -- |

## Rainstone Comparison

Per-job compute cost comparison against [Rainstone](https://rainstone.anvilproject.org) historical averages from usegalaxy.org. Rainstone data reflects median costs across thousands of production runs.

| Tool | Batch $/Job | Pulsar $/Job | Pulsar+K8s $/Job | Batch+K8s $/Job | Rainstone Avg | Rainstone Median | Rainstone P95 | usegalaxy.org Jobs |
|------| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| rna_star | $0.7060 | $0.4917 | $0.4793 | $0.7604 | $0.9108 | $0.2144 | $4.3362 | 124,843 |
| cufflinks | $0.4943 | $0.4056 | $0.3857 | $0.2441 | $0.2317 | $0.0413 | $1.0701 | 29,585 |
| wig_to_bigWig | $0.0009 | $0.0009 | $0.0008 | $0.0009 | -- | -- | -- | -- |
| multiqc | $0.0006 | $0.0004 | $0.0003 | $0.0005 | $0.0013 | $0.0005 | $0.0036 | 75,021 |
| bamFilter | $0.0341 | $0.0333 | $0.0277 | $0.0360 | -- | -- | -- | -- |
| tp_awk_tool | $0.0000 | $0.0000 | $0.0000 | $0.0000 | $0.0017 | $0.0002 | $0.0074 | 16,297 |
| bedtools_genomecoveragebed | $0.0077 | $0.0078 | $0.0000 | $0.0000 | $0.0016 | $0.0003 | $0.0056 | 47,439 |
| revertR2orientationInBam | $0.0152 | $0.0182 | $0.0000 | $0.0000 | -- | -- | -- | -- |
| cutadapt | $0.0516 | $0.0473 | $0.0450 | $0.0503 | $0.0182 | $0.0028 | $0.0703 | 167,606 |
| param_value_from_file | $0.0003 | $0.0010 | $0.0000 | $0.0000 | $0.0003 | $0.0002 | $0.0004 | 11,628 |
| map_param_value | $0.0002 | $0.0013 | $0.0000 | $0.0000 | -- | -- | -- | -- |
| compose_text_param | $0.0003 | $0.0013 | $0.0000 | $0.0000 | -- | -- | -- | -- |

## Deployment Model Comparison

GCP Batch approach (Galaxy + per-job VMs) vs traditional deployment (single n2-standard-20 VM running for the experiment duration).

| Model | Runner | Duration | Job Cost | Galaxy VM | **Total** |
|-------|--------|----------|----------|-----------|-----------|
| **GCP Batch** | Batch | 7.3h | $9.48 | $1.00 | **$10.48** |
| **Local VM** | Batch | 7.3h | -- | $7.08 | **$7.08** |
| **GCP Batch** | Pulsar | 6.7h | $11.03 | $0.92 | **$11.95** |
| **Local VM** | Pulsar | 6.7h | -- | $6.53 | **$6.53** |
| **GCP Batch** | Pulsar+K8s | 6.7h | $7.63 | $0.92 | **$8.56** |
| **Local VM** | Pulsar+K8s | 6.7h | -- | $6.53 | **$6.53** |
| **GCP Batch** | Batch+K8s | 7.4h | $6.94 | $1.02 | **$7.96** |
| **Local VM** | Batch+K8s | 7.4h | -- | $7.23 | **$7.23** |

**Batch**: GCP Batch is **48% more expensive** than a local n2-standard-20 ($10.48 vs $7.08).
**Pulsar**: GCP Batch is **83% more expensive** than a local n2-standard-20 ($11.95 vs $6.53).
**Pulsar+K8s**: GCP Batch is **31% more expensive** than a local n2-standard-20 ($8.56 vs $6.53).
**Batch+K8s**: GCP Batch is **10% more expensive** than a local n2-standard-20 ($7.96 vs $7.23).

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
