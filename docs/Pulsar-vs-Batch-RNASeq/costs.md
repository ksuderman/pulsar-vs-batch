---
title: RNASeq Cost Summary
---

# RNASeq Cost Summary

**[Interactive Cost Charts](cost-charts.html)** | **[Performance Report](index.html)** | **[Performance Charts](charts.html)**

**Period:** 2026-03-17 13:21:55 to 2026-03-17 16:33:35 UTC  
**Region:** us-east4  
**Total Jobs:** 24 (ok)

## Estimated Cost (Wallclock)

Cost based on total VM lifetime per job (Galaxy create_time to update_time). This is what users pay for on GCP Batch — it includes VM provisioning, image pull, file staging, compute, and shutdown.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 20 | 14.3h | $1.94 | $1.12 | $0.00 | $0.06 | **$3.12** |
| **Pulsar** | 4 | 3.5h | $0.73 | $0.43 | $0.07 | $0.01 | **$1.24** |
| **Total** | 24 | 17.8h | $2.67 | $1.55 | $0.07 | $0.07 | **$4.36** |

Pulsar costs **$1.24** vs Batch **$3.12** (0.4x).

## Compute-Only Cost (cgroups)

Cost based on cgroups `runtime_seconds` only — the actual CPU time reported by the container. Excludes VM boot, scheduling, and staging overhead.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 20 | 2.3h | $0.86 | $0.46 | $0.00 | $0.01 | **$1.33** |
| **Pulsar** | 4 | 0.9h | $0.43 | $0.23 | $0.02 | $0.00 | **$0.68** |
| **Total** | 24 | 3.2h | $1.29 | $0.69 | $0.02 | $0.01 | **$2.01** |

Pulsar costs **$0.68** vs Batch **$1.33** (0.5x).

### Wallclock vs Compute Overhead

| Runner | Compute Cost | Wallclock Cost | Overhead Ratio |
|--------|-------------|----------------|----------------|
| **Batch** | $1.33 | $3.12 | 2.3x |
| **Pulsar** | $0.68 | $1.24 | 1.8x |

The overhead ratio shows how much more users pay compared to pure compute. This includes VM provisioning (~2-5 min per job), container image pull, file staging (Pulsar: HTTP upload/download; Batch: NFS), and Galaxy scheduling delays.

### Cost Component Breakdown (Wallclock)

| Component | Batch | Pulsar | Total | % |
|-----------|-------|--------|-------|---|
| vCPU | $1.94 | $0.73 | $2.67 | 61% |
| Memory | $1.12 | $0.43 | $1.55 | 35% |
| Local SSD | $0.00 | $0.07 | $0.07 | 2% |
| Boot Disk | $0.06 | $0.01 | $0.07 | 2% |
| **Total** | **$3.12** | **$1.24** | **$4.36** | |

Note: Batch jobs use NFS for file staging (no local SSD cost). Pulsar jobs each provision a 375 GB local SSD.

## Per-Tool Cost Comparison (Wallclock)

The Rainstone Est. column shows the average cost per job from the [Rainstone cost API](https://rainstone.anvilproject.org/api/docs), based on historical usegalaxy.org usage.

| Tool | vCPU | Batch Jobs | Batch Cost | Batch $/Job | Pulsar Jobs | Pulsar Cost | Pulsar $/Job | Rainstone Est. |
|------|------|-----------|------------|-------------|------------|-------------|--------------|----------------|
| rna_star | 16 | 1 | $1.10 | $1.1020 | 1 | $0.87 | $0.8674 | $0.9108 |
| cufflinks | 8 | 1 | $0.83 | $0.8315 | 0 | $0.00 | $0.0000 | $0.2317 |
| tp_awk_tool | 2 | 2 | $0.29 | $0.1443 | 1 | $0.14 | $0.1380 | $0.0017 |
| multiqc | 2 | 1 | $0.20 | $0.1969 | 1 | $0.18 | $0.1805 | $0.0013 |
| revertR2orientationInBam | 2 | 1 | $0.17 | $0.1698 | 0 | $0.00 | $0.0000 | -- |
| bamFilter | 2 | 1 | $0.16 | $0.1602 | 0 | $0.00 | $0.0000 | -- |
| param_value_from_file | 2 | 1 | $0.15 | $0.1518 | 0 | $0.00 | $0.0000 | $0.0003 |
| wig_to_bigWig | 2 | 3 | $0.10 | $0.0332 | 0 | $0.00 | $0.0000 | -- |
| cutadapt | 8 | 1 | $0.03 | $0.0321 | 1 | $0.06 | $0.0556 | $0.0182 |
| bedtools_genomecoveragebed | 2 | 3 | $0.06 | $0.0210 | 0 | $0.00 | $0.0000 | $0.0016 |
| map_param_value | 2 | 4 | $0.02 | $0.0050 | 0 | $0.00 | $0.0000 | -- |
| compose_text_param | 2 | 1 | $0.01 | $0.0051 | 0 | $0.00 | $0.0000 | -- |
| **Total** | | **20** | **$3.12** | | **4** | **$1.24** | | |

## Per-Tool Cost Comparison (Compute-Only)

| Tool | vCPU | Batch Jobs | Batch Cost | Batch $/Job | Pulsar Jobs | Pulsar Cost | Pulsar $/Job | Rainstone Est. |
|------|------|-----------|------------|-------------|------------|-------------|--------------|----------------|
| rna_star | 16 | 1 | $1.00 | $0.9985 | 1 | $0.66 | $0.6622 | $0.9108 |
| cufflinks | 8 | 1 | $0.28 | $0.2796 | 0 | $0.00 | $0.0000 | $0.2317 |
| tp_awk_tool | 2 | 2 | $0.00 | $0.0000 | 1 | $0.00 | $0.0000 | $0.0017 |
| multiqc | 2 | 1 | $0.00 | $0.0006 | 1 | $0.00 | $0.0004 | $0.0013 |
| revertR2orientationInBam | 2 | 1 | $0.01 | $0.0054 | 0 | $0.00 | $0.0000 | -- |
| bamFilter | 2 | 1 | $0.01 | $0.0126 | 0 | $0.00 | $0.0000 | -- |
| param_value_from_file | 2 | 1 | $0.00 | $0.0003 | 0 | $0.00 | $0.0000 | $0.0003 |
| wig_to_bigWig | 2 | 3 | $0.00 | $0.0006 | 0 | $0.00 | $0.0000 | -- |
| cutadapt | 8 | 1 | $0.02 | $0.0192 | 1 | $0.02 | $0.0166 | $0.0182 |
| bedtools_genomecoveragebed | 2 | 3 | $0.01 | $0.0031 | 0 | $0.00 | $0.0000 | $0.0016 |
| map_param_value | 2 | 4 | $0.00 | $0.0002 | 0 | $0.00 | $0.0000 | -- |
| compose_text_param | 2 | 1 | $0.00 | $0.0002 | 0 | $0.00 | $0.0000 | -- |
| **Total** | | **20** | **$1.33** | | **4** | **$0.68** | | |

## Rainstone Comparison

Per-job wallclock cost comparison against [Rainstone](https://rainstone.anvilproject.org) historical averages from usegalaxy.org. Rainstone data reflects median costs across thousands of production runs.

| Tool | Batch $/Job | Pulsar $/Job | Rainstone Avg | Rainstone Median | Rainstone P95 | usegalaxy.org Jobs |
|------|-------------|--------------|---------------|-----------------|---------------|------------|
| rna_star | $1.1020 | $0.8674 | $0.9108 | $0.2144 | $4.3362 | 124,843 |
| cufflinks | $0.8315 | $0.0000 | $0.2317 | $0.0413 | $1.0701 | 29,585 |
| tp_awk_tool | $0.1443 | $0.1380 | $0.0017 | $0.0002 | $0.0074 | 16,297 |
| multiqc | $0.1969 | $0.1805 | $0.0013 | $0.0005 | $0.0036 | 75,021 |
| revertR2orientationInBam | $0.1698 | $0.0000 | -- | -- | -- | -- |
| bamFilter | $0.1602 | $0.0000 | -- | -- | -- | -- |
| param_value_from_file | $0.1518 | $0.0000 | $0.0003 | $0.0002 | $0.0004 | 11,628 |
| wig_to_bigWig | $0.0332 | $0.0000 | -- | -- | -- | -- |
| cutadapt | $0.0321 | $0.0556 | $0.0182 | $0.0028 | $0.0703 | 167,606 |
| bedtools_genomecoveragebed | $0.0210 | $0.0000 | $0.0016 | $0.0003 | $0.0056 | 47,439 |
| map_param_value | $0.0050 | $0.0000 | -- | -- | -- | -- |
| compose_text_param | $0.0051 | $0.0000 | -- | -- | -- | -- |

## Pricing Assumptions

All costs are estimated using GCP N2 on-demand pricing for `us-east4`:

| Resource | Rate |
|----------|------|
| N2 vCPU | $0.031611/vCPU/hour |
| N2 Memory | $0.004237/GB/hour |
| Local SSD | $5.4e-05/GB/hour |
| Boot Disk (pd-balanced) | $0.1/GB/month |

**Wallclock cost** uses the full Galaxy job lifetime (create_time to update_time) as the billing duration. This includes VM provisioning, container image pull, file staging, and scheduling overhead — all of which the user pays for on GCP Batch.

**Compute-only cost** uses cgroups `runtime_seconds` — the actual CPU time inside the container. This is a lower bound that excludes all infrastructure overhead.

Pulsar jobs each provision a 375 GB local SSD and a 30 GB boot disk. Batch jobs use NFS for staging (no local SSD). VM machine types are selected automatically based on tool CPU and memory requirements via `compute_machine_type()`.

Rainstone estimates are sourced from the [Rainstone Cost API](https://rainstone.anvilproject.org/api/docs) and reflect historical averages across usegalaxy.org production workloads.
