---
title: Variant Cost Summary
---

# Variant Cost Summary

**[Home](../index.html)** | **[Interactive Cost Charts](cost-charts.html)** | **[Performance Report](index.html)** | **[Performance Charts](charts.html)**

**Period:** 2026-03-31 13:17:26 to 2026-04-01 09:08:15 UTC  
**Region:** us-east4  
**Total Jobs:** 98 (ok)

## Estimated Cost (Wallclock)

Cost based on total VM lifetime per job (Galaxy create_time to update_time), including VM provisioning, image pull, file staging, compute, and shutdown.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 26 | 60.6h | $5.21 | $3.69 | $0.00 | $0.25 | **$9.16** |
| **Pulsar** | 36 | 123.0h | $10.45 | $7.73 | $2.49 | $0.51 | **$21.18** |
| **Single** | 36 | 99.3h | $8.55 | $6.37 | $0.00 | $0.41 | **$15.33** |
| **Total** | 98 | 282.9h | $24.21 | $17.79 | $2.49 | $1.18 | **$45.67** |

### Galaxy Host VM Cost

Each runner requires a Galaxy host VM (e2-standard-4, 4 vCPU, 16 GB). Duration is summed per-run (per workflow invocation), not the full experiment window.

| Runner | Duration | Galaxy VM Cost |
|--------|----------|----------------|
| **Batch** | 9.4h | $1.29 |
| **Pulsar** | 19.8h | $2.73 |
| **Single** | 17.1h | $2.35 |

### Total Estimated Cost (Batch Jobs + Galaxy VM)

| Runner | Job Cost | Galaxy VM Cost | **Total** |
|--------|----------|----------------|-----------|
| **Batch** | $9.16 | $1.29 | **$10.45** |
| **Pulsar** | $21.18 | $2.73 | **$23.90** |
| **Single** | $15.33 | $2.35 | **$17.68** |

## Compute-Only Cost (cgroups)

Cost based on cgroups `runtime_seconds` — actual CPU time inside the container.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 26 | 8.9h | $1.21 | $0.70 | $0.00 | $0.04 | **$1.94** |
| **Pulsar** | 36 | 14.7h | $1.99 | $1.10 | $0.30 | $0.06 | **$3.44** |
| **Single** | 36 | 16.0h | $2.14 | $1.20 | $0.00 | $0.07 | **$3.40** |
| **Total** | 98 | 39.6h | $5.33 | $2.99 | $0.30 | $0.16 | **$8.79** |

### Wallclock vs Compute Overhead

| Runner | Compute Cost | Wallclock Cost | Overhead Ratio |
|--------|-------------|----------------|----------------|
| **Batch** | $1.94 | $9.16 | 4.7x |
| **Pulsar** | $3.44 | $21.18 | 6.2x |
| **Single** | $3.40 | $15.33 | 4.5x |

## Per-Tool Cost Comparison (Wallclock)

| Tool | vCPU | Batch Jobs | Batch Cost | Batch $/Job | Pulsar Jobs | Pulsar Cost | Pulsar $/Job | Single Jobs | Single Cost | Single $/Job | Rainstone Est. |
|------|------| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| bwa_mem | 8 | 2 | $1.53 | $0.7638 | 3 | $2.99 | $0.9981 | 3 | $2.46 | $0.8199 | $0.1313 |
| lofreq_filter | 2 | 2 | $1.21 | $0.6063 | 3 | $3.06 | $1.0192 | 3 | $2.30 | $0.7652 | $0.0002 |
| snpEff | 2 | 2 | $1.11 | $0.5538 | 3 | $3.08 | $1.0273 | 3 | $2.31 | $0.7705 | -- |
| lofreq_viterbi | 4 | 2 | $1.01 | $0.5057 | 3 | $2.28 | $0.7586 | 3 | $1.73 | $0.5762 | $0.0093 |
| lofreq_call | 2 | 2 | $0.90 | $0.4506 | 3 | $2.37 | $0.7902 | 3 | $1.71 | $0.5697 | $0.0555 |
| picard_MarkDuplicates | 4 | 2 | $0.93 | $0.4664 | 3 | $1.98 | $0.6616 | 3 | $1.58 | $0.5260 | -- |
| lofreq_indelqual | 2 | 2 | $0.73 | $0.3634 | 3 | $1.78 | $0.5924 | 3 | $1.25 | $0.4156 | $0.0008 |
| multiqc | 2 | 2 | $0.65 | $0.3229 | 3 | $1.46 | $0.4879 | 3 | $1.09 | $0.3636 | $0.0013 |
| samtools_stats | 2 | 2 | $0.43 | $0.2140 | 3 | $1.03 | $0.3420 | 3 | $0.70 | $0.2336 | $0.0009 |
| samtools_view | 2 | 2 | $0.42 | $0.2089 | 3 | $0.76 | $0.2538 | 3 | $0.00 | $0.0000 | $0.0020 |
| fastp | 4 | 3 | $0.10 | $0.0333 | 3 | $0.29 | $0.0959 | 3 | $0.10 | $0.0330 | $0.0080 |
| snpEff_build_gb | 2 | 3 | $0.15 | $0.0487 | 3 | $0.09 | $0.0316 | 3 | $0.11 | $0.0373 | -- |

## Rainstone Comparison

Per-job compute cost comparison against [Rainstone](https://rainstone.anvilproject.org) historical averages from usegalaxy.org. Rainstone data reflects median costs across thousands of production runs.

| Tool | Batch $/Job | Pulsar $/Job | Single $/Job | Rainstone Avg | Rainstone Median | Rainstone P95 | usegalaxy.org Jobs |
|------| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| bwa_mem | $0.5962 | $0.6987 | $0.6896 | $0.1313 | $0.0097 | $0.5610 | 158,991 |
| lofreq_filter | $0.0000 | $0.0000 | $0.0001 | $0.0002 | $0.0001 | $0.0004 | 60,578 |
| snpEff | $0.0001 | $0.0003 | $0.0003 | -- | -- | -- | -- |
| lofreq_viterbi | $0.0300 | $0.0395 | $0.0407 | $0.0093 | $0.0023 | $0.0311 | 49,601 |
| lofreq_call | $0.1748 | $0.2998 | $0.2547 | $0.0555 | $0.0103 | $0.1374 | 70,976 |
| picard_MarkDuplicates | $0.0482 | $0.0480 | $0.0720 | -- | -- | -- | -- |
| lofreq_indelqual | $0.0119 | $0.0137 | $0.0155 | $0.0008 | $0.0003 | $0.0018 | 46,590 |
| multiqc | $0.0003 | $0.0001 | $0.0003 | $0.0013 | $0.0005 | $0.0036 | 75,021 |
| samtools_stats | $0.0022 | $0.0040 | $0.0038 | $0.0009 | $0.0003 | $0.0033 | 88,828 |
| samtools_view | $0.0065 | $0.0089 | $0.0000 | $0.0020 | $0.0004 | $0.0051 | 83,527 |
| fastp | $0.0254 | $0.0266 | $0.0249 | $0.0080 | $0.0020 | $0.0350 | 212,086 |
| snpEff_build_gb | $0.0424 | $0.0076 | $0.0313 | -- | -- | -- | -- |

## Deployment Model Comparison

GCP Batch approach (Galaxy + per-job VMs) vs traditional deployment (single n2-standard-20 VM running for the experiment duration).

| Model | Runner | Duration | Job Cost | Galaxy VM | **Total** |
|-------|--------|----------|----------|-----------|-----------|
| **GCP Batch** | Batch | 9.4h | $9.16 | $1.29 | **$10.45** |
| **Local VM** | Batch | 9.4h | -- | $9.10 | **$9.10** |
| **GCP Batch** | Pulsar | 19.8h | $21.18 | $2.73 | **$23.90** |
| **Local VM** | Pulsar | 19.8h | -- | $19.26 | **$19.26** |
| **GCP Batch** | Single | 17.1h | $15.33 | $2.35 | **$17.68** |
| **Local VM** | Single | 17.1h | -- | $16.61 | **$16.61** |

**Batch**: GCP Batch is **15% more expensive** than a local n2-standard-20 ($10.45 vs $9.10).
**Pulsar**: GCP Batch is **24% more expensive** than a local n2-standard-20 ($23.90 vs $19.26).
**Single**: GCP Batch is **6% more expensive** than a local n2-standard-20 ($17.68 vs $16.61).

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
