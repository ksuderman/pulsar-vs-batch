---
title: RNASeq Cost Summary
---

# RNASeq Cost Summary

**[Home](../index.html)** | **[Interactive Cost Charts](cost-charts.html)** | **[Performance Report](index.html)** | **[Performance Charts](charts.html)**

**Period:** 2026-03-17 13:21:55 to 2026-03-23 20:22:17 UTC  
**Region:** us-east4  
**Total Jobs:** 96 (ok)

## Estimated Cost (Wallclock)

Cost based on total VM lifetime per job (Galaxy create_time to update_time). This is what users pay for on GCP Batch — it includes VM provisioning, image pull, file staging, compute, and shutdown.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 36 | 17.5h | $2.47 | $1.40 | $0.00 | $0.07 | **$3.94** |
| **Pulsar** | 60 | 53.4h | $6.50 | $3.88 | $1.08 | $0.22 | **$11.68** |
| **Total** | 96 | 70.9h | $8.96 | $5.28 | $1.08 | $0.30 | **$15.62** |

### Galaxy Host VM Cost

Each runner requires a Galaxy host VM (e2-standard-4, 4 vCPU, 16 GB) running for the duration of the experiment. This cost is not included in the per-tool or compute-time calculations above.

| Runner | Duration | Galaxy VM Cost |
|--------|----------|----------------|
| **Batch** | 3.0h | $0.41 |
| **Pulsar** | 7.1h | $0.98 |

### Total Estimated Cost (Batch Jobs + Galaxy VM)

| Runner | Batch Job Cost | Galaxy VM Cost | **Total** |
|--------|---------------|----------------|-----------|
| **Batch** | $3.94 | $0.41 | **$4.35** |
| **Pulsar** | $11.68 | $0.98 | **$12.66** |

Pulsar costs **$12.66** vs Batch **$4.35** (2.9x) including Galaxy VM.

## Compute-Only Cost (cgroups)

Cost based on cgroups `runtime_seconds` only — the actual CPU time reported by the container. Excludes VM boot, scheduling, and staging overhead.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 36 | 2.8h | $1.07 | $0.57 | $0.00 | $0.01 | **$1.65** |
| **Pulsar** | 60 | 7.5h | $2.05 | $1.10 | $0.15 | $0.03 | **$3.34** |
| **Total** | 96 | 10.3h | $3.12 | $1.68 | $0.15 | $0.04 | **$4.99** |

Pulsar costs **$3.34** vs Batch **$1.65** (2.0x).

### Wallclock vs Compute Overhead

| Runner | Compute Cost | Wallclock Cost | Overhead Ratio |
|--------|-------------|----------------|----------------|
| **Batch** | $1.65 | $3.94 | 2.4x |
| **Pulsar** | $3.34 | $11.68 | 3.5x |

The overhead ratio shows how much more users pay compared to pure compute. This includes VM provisioning (~2-5 min per job), container image pull, file staging (Pulsar: HTTP upload/download; Batch: NFS), and Galaxy scheduling delays.

### Cost Component Breakdown (Wallclock)

| Component | Batch | Pulsar | Total | % |
|-----------|-------|--------|-------|---|
| vCPU | $2.47 | $6.50 | $8.96 | 57% |
| Memory | $1.40 | $3.88 | $5.28 | 34% |
| Local SSD | $0.00 | $1.08 | $1.08 | 7% |
| Boot Disk | $0.07 | $0.22 | $0.30 | 2% |
| **Total** | **$3.94** | **$11.68** | **$15.62** | |

Note: Batch jobs use NFS for file staging (no local SSD cost). Pulsar jobs each provision a 375 GB local SSD.

## Per-Tool Cost Comparison (Wallclock)

The Rainstone Est. column shows the average cost per job from the [Rainstone cost API](https://rainstone.anvilproject.org/api/docs), based on historical usegalaxy.org usage.

| Tool | vCPU | Batch Jobs | Batch Cost | Batch $/Job | Pulsar Jobs | Pulsar Cost | Pulsar $/Job | Rainstone Est. |
|------|------|-----------|------------|-------------|------------|-------------|--------------|----------------|
| rna_star | 16 | 2 | $1.56 | $0.7815 | 3 | $2.96 | $0.9867 | $0.9108 |
| cufflinks | 8 | 1 | $0.83 | $0.8315 | 3 | $2.86 | $0.9550 | $0.2317 |
| wig_to_bigWig | 2 | 3 | $0.10 | $0.0332 | 9 | $1.20 | $0.1333 | -- |
| tp_awk_tool | 2 | 3 | $0.35 | $0.1155 | 6 | $0.94 | $0.1559 | $0.0017 |
| revertR2orientationInBam | 2 | 2 | $0.24 | $0.1179 | 3 | $0.73 | $0.2448 | -- |
| bedtools_genomecoveragebed | 2 | 3 | $0.06 | $0.0210 | 9 | $0.87 | $0.0967 | $0.0016 |
| bamFilter | 2 | 2 | $0.22 | $0.1115 | 3 | $0.62 | $0.2058 | -- |
| multiqc | 2 | 1 | $0.20 | $0.1969 | 3 | $0.63 | $0.2116 | $0.0013 |
| param_value_from_file | 2 | 1 | $0.15 | $0.1518 | 3 | $0.47 | $0.1575 | $0.0003 |
| cutadapt | 8 | 3 | $0.15 | $0.0504 | 3 | $0.37 | $0.1224 | $0.0182 |
| map_param_value | 2 | 12 | $0.06 | $0.0050 | 12 | $0.02 | $0.0019 | -- |
| compose_text_param | 2 | 3 | $0.02 | $0.0050 | 3 | $0.00 | $0.0013 | -- |
| **Total** | | **36** | **$3.94** | | **60** | **$11.68** | | |

## Per-Tool Cost Comparison (Compute-Only)

| Tool | vCPU | Batch Jobs | Batch Cost | Batch $/Job | Pulsar Jobs | Pulsar Cost | Pulsar $/Job | Rainstone Est. |
|------|------|-----------|------------|-------------|------------|-------------|--------------|----------------|
| rna_star | 16 | 2 | $1.32 | $0.6584 | 3 | $1.72 | $0.5732 | $0.9108 |
| cufflinks | 8 | 1 | $0.28 | $0.2796 | 3 | $1.23 | $0.4091 | $0.2317 |
| wig_to_bigWig | 2 | 3 | $0.00 | $0.0006 | 9 | $0.01 | $0.0010 | -- |
| tp_awk_tool | 2 | 3 | $0.00 | $0.0000 | 6 | $0.00 | $0.0000 | $0.0017 |
| revertR2orientationInBam | 2 | 2 | $0.01 | $0.0027 | 3 | $0.05 | $0.0177 | -- |
| bedtools_genomecoveragebed | 2 | 3 | $0.01 | $0.0031 | 9 | $0.07 | $0.0079 | $0.0016 |
| bamFilter | 2 | 2 | $0.01 | $0.0063 | 3 | $0.10 | $0.0331 | -- |
| multiqc | 2 | 1 | $0.00 | $0.0006 | 3 | $0.00 | $0.0003 | $0.0013 |
| param_value_from_file | 2 | 1 | $0.00 | $0.0003 | 3 | $0.00 | $0.0011 | $0.0003 |
| cutadapt | 8 | 3 | $0.02 | $0.0064 | 3 | $0.14 | $0.0471 | $0.0182 |
| map_param_value | 2 | 12 | $0.00 | $0.0002 | 12 | $0.01 | $0.0012 | -- |
| compose_text_param | 2 | 3 | $0.00 | $0.0002 | 3 | $0.00 | $0.0012 | -- |
| **Total** | | **36** | **$1.65** | | **60** | **$3.34** | | |

## Rainstone Comparison

Per-job compute cost comparison against [Rainstone](https://rainstone.anvilproject.org) historical averages from usegalaxy.org. Rainstone data reflects median costs across thousands of production runs.

| Tool | Batch $/Job | Pulsar $/Job | Rainstone Avg | Rainstone Median | Rainstone P95 | usegalaxy.org Jobs |
|------|-------------|--------------|---------------|-----------------|---------------|------------|
| rna_star | $0.6584 | $0.5732 | $0.9108 | $0.2144 | $4.3362 | 124,843 |
| cufflinks | $0.2796 | $0.4091 | $0.2317 | $0.0413 | $1.0701 | 29,585 |
| wig_to_bigWig | $0.0006 | $0.0010 | -- | -- | -- | -- |
| tp_awk_tool | $0.0000 | $0.0000 | $0.0017 | $0.0002 | $0.0074 | 16,297 |
| revertR2orientationInBam | $0.0027 | $0.0177 | -- | -- | -- | -- |
| bedtools_genomecoveragebed | $0.0031 | $0.0079 | $0.0016 | $0.0003 | $0.0056 | 47,439 |
| bamFilter | $0.0063 | $0.0331 | -- | -- | -- | -- |
| multiqc | $0.0006 | $0.0003 | $0.0013 | $0.0005 | $0.0036 | 75,021 |
| param_value_from_file | $0.0003 | $0.0011 | $0.0003 | $0.0002 | $0.0004 | 11,628 |
| cutadapt | $0.0064 | $0.0471 | $0.0182 | $0.0028 | $0.0703 | 167,606 |
| map_param_value | $0.0002 | $0.0012 | -- | -- | -- | -- |
| compose_text_param | $0.0002 | $0.0012 | -- | -- | -- | -- |

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

## Deployment Model Comparison

Comparison of our GCP Batch approach (Galaxy + Batch VMs) against the traditional deployment model where Galaxy runs jobs locally on a single large VM (n2-standard-20, 20 vCPU, 80 GB).

In the local model, the single VM must run for the entire experiment duration. In the Batch model, per-job VMs are provisioned on demand and the Galaxy host is a smaller e2-standard-4.

| Model | Runner | Duration | Job Cost | Galaxy VM | **Total** |
|-------|--------|----------|----------|-----------|-----------|
| **GCP Batch** | Batch | 3.0h | $3.94 | $0.41 | **$4.35** |
| **Local VM** | Batch | 3.0h | -- | $2.89 | **$2.89** |
| **GCP Batch** | Pulsar | 7.1h | $11.68 | $0.98 | **$12.66** |
| **Local VM** | Pulsar | 7.1h | -- | $6.93 | **$6.93** |

**Batch**: GCP Batch is **51% more expensive** than a local n2-standard-20 ($4.35 vs $2.89).
**Pulsar**: GCP Batch is **83% more expensive** than a local n2-standard-20 ($12.66 vs $6.93).

Local VM pricing: n2-standard-20 at $0.9712/hour (20 vCPU × $0.031611/h + 80 GB × $0.004237/h).
