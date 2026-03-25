---
title: Variant Calling Cost Summary
---

# Variant Calling Cost Summary

**[Interactive Cost Charts](cost-charts.html)** | **[Performance Report](index.html)** | **[Performance Charts](charts.html)**

**Period:** 2026-03-16 19:36:51 to 2026-03-17 15:23:30 UTC  
**Region:** us-east4  
**Total Jobs:** 72 (ok)

## Estimated Cost (Wallclock)

Cost based on total VM lifetime per job (Galaxy create_time to update_time). This is what users pay for on GCP Batch — it includes VM provisioning, image pull, file staging, compute, and shutdown.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 36 | 111.5h | $9.45 | $6.95 | $0.00 | $0.46 | **$16.86** |
| **Pulsar** | 36 | 123.8h | $10.47 | $7.73 | $2.51 | $0.52 | **$21.22** |
| **Total** | 72 | 235.3h | $19.91 | $14.68 | $2.51 | $0.98 | **$38.08** |

### Galaxy Host VM Cost

Each runner requires a Galaxy host VM (e2-standard-4, 4 vCPU, 16 GB) running for the duration of the experiment. This cost is not included in the per-tool or compute-time calculations above.

| Runner | Duration | Galaxy VM Cost |
|--------|----------|----------------|
| **Batch** | 17.7h | $2.44 |
| **Pulsar** | 19.8h | $2.72 |

### Total Estimated Cost (Batch Jobs + Galaxy VM)

| Runner | Batch Job Cost | Galaxy VM Cost | **Total** |
|--------|---------------|----------------|-----------|
| **Batch** | $16.86 | $2.44 | **$19.30** |
| **Pulsar** | $21.22 | $2.72 | **$23.94** |

Pulsar costs **$23.94** vs Batch **$19.30** (1.2x) including Galaxy VM.

## Compute-Only Cost (cgroups)

Cost based on cgroups `runtime_seconds` only — the actual CPU time reported by the container. Excludes VM boot, scheduling, and staging overhead.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 36 | 16.7h | $2.21 | $1.24 | $0.00 | $0.07 | **$3.52** |
| **Pulsar** | 36 | 14.7h | $1.98 | $1.09 | $0.30 | $0.06 | **$3.43** |
| **Total** | 72 | 31.4h | $4.18 | $2.33 | $0.30 | $0.13 | **$6.95** |

Pulsar costs **$3.43** vs Batch **$3.52** (1.0x).

### Wallclock vs Compute Overhead

| Runner | Compute Cost | Wallclock Cost | Overhead Ratio |
|--------|-------------|----------------|----------------|
| **Batch** | $3.52 | $16.86 | 4.8x |
| **Pulsar** | $3.43 | $21.22 | 6.2x |

The overhead ratio shows how much more users pay compared to pure compute. This includes VM provisioning (~2-5 min per job), container image pull, file staging (Pulsar: HTTP upload/download; Batch: NFS), and Galaxy scheduling delays.

### Cost Component Breakdown (Wallclock)

| Component | Batch | Pulsar | Total | % |
|-----------|-------|--------|-------|---|
| vCPU | $9.45 | $10.47 | $19.91 | 52% |
| Memory | $6.95 | $7.73 | $14.68 | 39% |
| Local SSD | $0.00 | $2.51 | $2.51 | 7% |
| Boot Disk | $0.46 | $0.52 | $0.98 | 3% |
| **Total** | **$16.86** | **$21.22** | **$38.08** | |

Note: Batch jobs use NFS for file staging (no local SSD cost). Pulsar jobs each provision a 375 GB local SSD.

## Per-Tool Cost Comparison (Wallclock)

The Rainstone Est. column shows the average cost per job from the [Rainstone cost API](https://rainstone.anvilproject.org/api/docs), based on historical usegalaxy.org usage.

| Tool | vCPU | Batch Jobs | Batch Cost | Batch $/Job | Pulsar Jobs | Pulsar Cost | Pulsar $/Job | Rainstone Est. |
|------|------|-----------|------------|-------------|------------|-------------|--------------|----------------|
| bwa_mem | 8 | 3 | $2.59 | $0.8621 | 3 | $2.96 | $0.9874 | $0.1313 |
| snpEff | 2 | 3 | $2.40 | $0.7989 | 3 | $3.07 | $1.0237 | -- |
| lofreq_filter | 2 | 3 | $2.38 | $0.7936 | 3 | $3.05 | $1.0155 | $0.0002 |
| lofreq_call | 2 | 3 | $1.77 | $0.5905 | 3 | $2.36 | $0.7871 | $0.0555 |
| lofreq_viterbi | 4 | 3 | $1.84 | $0.6144 | 3 | $2.25 | $0.7491 | $0.0093 |
| picard_MarkDuplicates | 4 | 3 | $1.68 | $0.5608 | 3 | $1.95 | $0.6516 | -- |
| lofreq_indelqual | 2 | 3 | $1.33 | $0.4436 | 3 | $1.76 | $0.5860 | $0.0008 |
| multiqc | 2 | 3 | $1.16 | $0.3879 | 3 | $1.49 | $0.4972 | $0.0013 |
| samtools_stats | 2 | 3 | $0.74 | $0.2463 | 3 | $1.01 | $0.3351 | $0.0009 |
| samtools_view | 2 | 3 | $0.72 | $0.2393 | 3 | $0.95 | $0.3178 | $0.0020 |
| fastp | 4 | 3 | $0.10 | $0.0325 | 3 | $0.28 | $0.0919 | $0.0080 |
| snpEff_build_gb | 2 | 3 | $0.15 | $0.0489 | 3 | $0.10 | $0.0319 | -- |
| **Total** | | **36** | **$16.86** | | **36** | **$21.22** | | |

## Per-Tool Cost Comparison (Compute-Only)

| Tool | vCPU | Batch Jobs | Batch Cost | Batch $/Job | Pulsar Jobs | Pulsar Cost | Pulsar $/Job | Rainstone Est. |
|------|------|-----------|------------|-------------|------------|-------------|--------------|----------------|
| bwa_mem | 8 | 3 | $2.09 | $0.6969 | 3 | $2.08 | $0.6933 | $0.1313 |
| snpEff | 2 | 3 | $0.00 | $0.0002 | 3 | $0.00 | $0.0002 | -- |
| lofreq_filter | 2 | 3 | $0.00 | $0.0001 | 3 | $0.00 | $0.0000 | $0.0002 |
| lofreq_call | 2 | 3 | $0.76 | $0.2535 | 3 | $0.90 | $0.3008 | $0.0555 |
| lofreq_viterbi | 4 | 3 | $0.13 | $0.0426 | 3 | $0.12 | $0.0394 | $0.0093 |
| picard_MarkDuplicates | 4 | 3 | $0.24 | $0.0814 | 3 | $0.14 | $0.0481 | -- |
| lofreq_indelqual | 2 | 3 | $0.05 | $0.0168 | 3 | $0.04 | $0.0137 | $0.0008 |
| multiqc | 2 | 3 | $0.00 | $0.0004 | 3 | $0.00 | $0.0001 | $0.0013 |
| samtools_stats | 2 | 3 | $0.01 | $0.0037 | 3 | $0.01 | $0.0040 | $0.0009 |
| samtools_view | 2 | 3 | $0.03 | $0.0103 | 3 | $0.03 | $0.0089 | $0.0020 |
| fastp | 4 | 3 | $0.07 | $0.0246 | 3 | $0.08 | $0.0263 | $0.0080 |
| snpEff_build_gb | 2 | 3 | $0.13 | $0.0426 | 3 | $0.02 | $0.0076 | -- |
| **Total** | | **36** | **$3.52** | | **36** | **$3.43** | | |

## Rainstone Comparison

Per-job compute cost comparison against [Rainstone](https://rainstone.anvilproject.org) historical averages from usegalaxy.org. Rainstone data reflects median costs across thousands of production runs.

| Tool | Batch $/Job | Pulsar $/Job | Rainstone Avg | Rainstone Median | Rainstone P95 | usegalaxy.org Jobs |
|------|-------------|--------------|---------------|-----------------|---------------|------------|
| bwa_mem | $0.6969 | $0.6933 | $0.1313 | $0.0097 | $0.5610 | 158,991 |
| snpEff | $0.0002 | $0.0002 | -- | -- | -- | -- |
| lofreq_filter | $0.0001 | $0.0000 | $0.0002 | $0.0001 | $0.0004 | 60,578 |
| lofreq_call | $0.2535 | $0.3008 | $0.0555 | $0.0103 | $0.1374 | 70,976 |
| lofreq_viterbi | $0.0426 | $0.0394 | $0.0093 | $0.0023 | $0.0311 | 49,601 |
| picard_MarkDuplicates | $0.0814 | $0.0481 | -- | -- | -- | -- |
| lofreq_indelqual | $0.0168 | $0.0137 | $0.0008 | $0.0003 | $0.0018 | 46,590 |
| multiqc | $0.0004 | $0.0001 | $0.0013 | $0.0005 | $0.0036 | 75,021 |
| samtools_stats | $0.0037 | $0.0040 | $0.0009 | $0.0003 | $0.0033 | 88,828 |
| samtools_view | $0.0103 | $0.0089 | $0.0020 | $0.0004 | $0.0051 | 83,527 |
| fastp | $0.0246 | $0.0263 | $0.0080 | $0.0020 | $0.0350 | 212,086 |
| snpEff_build_gb | $0.0426 | $0.0076 | -- | -- | -- | -- |

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
| **GCP Batch** | Batch | 17.7h | $16.86 | $2.44 | **$19.30** |
| **Local VM** | Batch | 17.7h | -- | $17.23 | **$17.23** |
| **GCP Batch** | Pulsar | 19.8h | $21.22 | $2.72 | **$23.94** |
| **Local VM** | Pulsar | 19.8h | -- | $19.21 | **$19.21** |

**Batch**: GCP Batch is **12% more expensive** than a local n2-standard-20 ($19.30 vs $17.23).
**Pulsar**: GCP Batch is **25% more expensive** than a local n2-standard-20 ($23.94 vs $19.21).

Local VM pricing: n2-standard-20 at $0.9712/hour (20 vCPU × $0.031611/h + 80 GB × $0.004237/h).
