---
title: ChiPSeq Cost Summary
---

# ChiPSeq Cost Summary

**[Home](../index.html)** | **[Interactive Cost Charts](cost-charts.html)** | **[Performance Report](index.html)** | **[Performance Charts](charts.html)**

**Period:** 2026-03-30 01:02:48 to 2026-03-30 09:33:45 UTC  
**Region:** us-east4  
**Total Jobs:** 63 (ok)

## Estimated Cost (Wallclock)

Cost based on total VM lifetime per job (Galaxy create_time to update_time), including VM provisioning, image pull, file staging, compute, and shutdown.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 21 | 37.0h | $3.34 | $2.66 | $0.00 | $0.15 | **$6.15** |
| **Pulsar** | 21 | 47.5h | $4.21 | $3.40 | $0.96 | $0.20 | **$8.77** |
| **Single** | 21 | 30.8h | $2.96 | $2.46 | $0.00 | $0.13 | **$5.55** |
| **Total** | 63 | 115.3h | $10.51 | $8.51 | $0.96 | $0.48 | **$20.47** |

### Galaxy Host VM Cost

Each runner requires a Galaxy host VM (e2-standard-4, 4 vCPU, 16 GB). Duration is summed per-run (per workflow invocation), not the full experiment window.

| Runner | Duration | Galaxy VM Cost |
|--------|----------|----------------|
| **Batch** | 6.5h | $0.89 |
| **Pulsar** | 8.5h | $1.17 |
| **Single** | 6.5h | $0.90 |

### Total Estimated Cost (Batch Jobs + Galaxy VM)

| Runner | Job Cost | Galaxy VM Cost | **Total** |
|--------|----------|----------------|-----------|
| **Batch** | $6.15 | $0.89 | **$7.05** |
| **Pulsar** | $8.77 | $1.17 | **$9.94** |
| **Single** | $5.55 | $0.90 | **$6.44** |

## Compute-Only Cost (cgroups)

Cost based on cgroups `runtime_seconds` — actual CPU time inside the container.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 21 | 5.8h | $1.26 | $0.72 | $0.00 | $0.02 | **$2.01** |
| **Pulsar** | 21 | 5.4h | $1.20 | $0.68 | $0.11 | $0.02 | **$2.02** |
| **Single** | 21 | 5.8h | $1.27 | $0.73 | $0.00 | $0.02 | **$2.02** |
| **Total** | 63 | 17.1h | $3.74 | $2.13 | $0.11 | $0.07 | **$6.05** |

### Wallclock vs Compute Overhead

| Runner | Compute Cost | Wallclock Cost | Overhead Ratio |
|--------|-------------|----------------|----------------|
| **Batch** | $2.01 | $6.15 | 3.1x |
| **Pulsar** | $2.02 | $8.77 | 4.4x |
| **Single** | $2.02 | $5.55 | 2.7x |

## Per-Tool Cost Comparison (Wallclock)

| Tool | vCPU | Batch Jobs | Batch Cost | Batch $/Job | Pulsar Jobs | Pulsar Cost | Pulsar $/Job | Single Jobs | Single Cost | Single $/Job | Rainstone Est. |
|------|------| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| bowtie2 | 8 | 3 | $2.04 | $0.6784 | 3 | $2.51 | $0.8375 | 3 | $2.05 | $0.6848 | $0.1872 |
| wig_to_bigWig | 2 | 3 | $0.88 | $0.2925 | 3 | $1.32 | $0.4402 | 3 | $0.88 | $0.2941 | -- |
| multiqc | 2 | 3 | $0.88 | $0.2917 | 3 | $1.31 | $0.4354 | 3 | $0.88 | $0.2931 | $0.0013 |
| macs2_callpeak | 2 | 3 | $0.86 | $0.2861 | 3 | $1.27 | $0.4246 | 3 | $0.86 | $0.2878 | $0.0165 |
| samtool_filter2 | 2 | 3 | $0.78 | $0.2601 | 3 | $1.11 | $0.3685 | 3 | $0.79 | $0.2618 | $0.0034 |
| tp_grep_tool | 2 | 3 | $0.65 | $0.2167 | 3 | $1.02 | $0.3393 | 3 | $0.00 | $0.0000 | $0.0006 |
| fastp | 4 | 3 | $0.08 | $0.0252 | 3 | $0.24 | $0.0786 | 3 | $0.08 | $0.0271 | $0.0080 |

## Rainstone Comparison

Per-job compute cost comparison against [Rainstone](https://rainstone.anvilproject.org) historical averages from usegalaxy.org. Rainstone data reflects median costs across thousands of production runs.

| Tool | Batch $/Job | Pulsar $/Job | Single $/Job | Rainstone Avg | Rainstone Median | Rainstone P95 | usegalaxy.org Jobs |
|------| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| bowtie2 | $0.6100 | $0.6129 | $0.6146 | $0.1872 | $0.0334 | $0.8059 | 255,897 |
| wig_to_bigWig | $0.0034 | $0.0038 | $0.0035 | -- | -- | -- | -- |
| multiqc | $0.0010 | $0.0006 | $0.0010 | $0.0013 | $0.0005 | $0.0036 | 75,021 |
| macs2_callpeak | $0.0198 | $0.0194 | $0.0200 | $0.0165 | $0.0086 | $0.0552 | 63,329 |
| samtool_filter2 | $0.0178 | $0.0163 | $0.0171 | $0.0034 | $0.0015 | $0.0120 | 34,338 |
| tp_grep_tool | $0.0000 | $0.0000 | $0.0000 | $0.0006 | $0.0002 | $0.0017 | 16,283 |
| fastp | $0.0181 | $0.0190 | $0.0182 | $0.0080 | $0.0020 | $0.0350 | 212,086 |

## Deployment Model Comparison

GCP Batch approach (Galaxy + per-job VMs) vs traditional deployment (single n2-standard-20 VM running for the experiment duration).

| Model | Runner | Duration | Job Cost | Galaxy VM | **Total** |
|-------|--------|----------|----------|-----------|-----------|
| **GCP Batch** | Batch | 6.5h | $6.15 | $0.89 | **$7.05** |
| **Local VM** | Batch | 6.5h | -- | $6.31 | **$6.31** |
| **GCP Batch** | Pulsar | 8.5h | $8.77 | $1.17 | **$9.94** |
| **Local VM** | Pulsar | 8.5h | -- | $8.25 | **$8.25** |
| **GCP Batch** | Single | 6.5h | $5.55 | $0.90 | **$6.44** |
| **Local VM** | Single | 6.5h | -- | $6.34 | **$6.34** |

**Batch**: GCP Batch is **12% more expensive** than a local n2-standard-20 ($7.05 vs $6.31).
**Pulsar**: GCP Batch is **20% more expensive** than a local n2-standard-20 ($9.94 vs $8.25).
**Single**: GCP Batch is **2% more expensive** than a local n2-standard-20 ($6.44 vs $6.34).

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
