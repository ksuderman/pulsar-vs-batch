---
title: Variant Cost Summary
---

# Variant Cost Summary

**[Home](../index.html)** | **[Interactive Cost Charts](cost-charts.html)** | **[Performance Report](index.html)** | **[Performance Charts](charts.html)**

**Period:** 2026-03-31 13:17:26 to 2026-04-04 01:20:50 UTC  
**Region:** us-east4  
**Total Jobs:** 144 (ok)

## Estimated Cost (Wallclock)

Cost based on total VM lifetime per job (Galaxy create_time to update_time), including VM provisioning, image pull, file staging, compute, and shutdown.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 36 | 112.7h | $9.58 | $6.91 | $0.00 | $0.47 | **$16.97** |
| **Pulsar** | 36 | 125.3h | $10.65 | $7.88 | $2.54 | $0.52 | **$21.59** |
| **Pulsar+K8s** | 36 | 118.9h | $10.25 | $7.66 | $0.00 | $0.50 | **$18.40** |
| **Batch+K8s** | 36 | 99.3h | $8.55 | $6.37 | $0.00 | $0.41 | **$15.33** |
| **Total** | 144 | 456.3h | $39.03 | $28.82 | $2.54 | $1.90 | **$72.29** |

### Galaxy Host VM Cost

Each runner requires a Galaxy host VM (e2-standard-4, 4 vCPU, 16 GB). Duration is summed per-run (per workflow invocation), not the full experiment window.

| Runner | Duration | Galaxy VM Cost |
|--------|----------|----------------|
| **Batch** | 17.8h | $2.44 |
| **Pulsar** | 20.2h | $2.77 |
| **Pulsar+K8s** | 20.2h | $2.77 |
| **Batch+K8s** | 17.1h | $2.35 |

### Total Estimated Cost (Batch Jobs + Galaxy VM)

| Runner | Job Cost | Galaxy VM Cost | **Total** |
|--------|----------|----------------|-----------|
| **Batch** | $16.97 | $2.44 | **$19.41** |
| **Pulsar** | $21.59 | $2.77 | **$24.36** |
| **Pulsar+K8s** | $18.40 | $2.77 | **$21.17** |
| **Batch+K8s** | $15.33 | $2.35 | **$17.68** |

## Compute-Only Cost (cgroups)

Cost based on cgroups `runtime_seconds` — actual CPU time inside the container.

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 36 | 16.9h | $2.25 | $1.27 | $0.00 | $0.07 | **$3.58** |
| **Pulsar** | 36 | 14.9h | $2.02 | $1.12 | $0.30 | $0.06 | **$3.50** |
| **Pulsar+K8s** | 36 | 14.7h | $2.01 | $1.11 | $0.00 | $0.06 | **$3.18** |
| **Batch+K8s** | 36 | 16.0h | $2.14 | $1.20 | $0.00 | $0.07 | **$3.40** |
| **Total** | 144 | 62.5h | $8.41 | $4.69 | $0.30 | $0.26 | **$13.66** |

### Wallclock vs Compute Overhead

| Runner | Compute Cost | Wallclock Cost | Overhead Ratio |
|--------|-------------|----------------|----------------|
| **Batch** | $3.58 | $16.97 | 4.7x |
| **Pulsar** | $3.50 | $21.59 | 6.2x |
| **Pulsar+K8s** | $3.18 | $18.40 | 5.8x |
| **Batch+K8s** | $3.40 | $15.33 | 4.5x |

## Per-Tool Cost Comparison (Wallclock)

| Tool | vCPU | Batch Jobs | Batch Cost | Batch $/Job | Pulsar Jobs | Pulsar Cost | Pulsar $/Job | Pulsar+K8s Jobs | Pulsar+K8s Cost | Pulsar+K8s $/Job | Batch+K8s Jobs | Batch+K8s Cost | Batch+K8s $/Job | Rainstone Est. |
|------|------| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| bwa_mem | 8 | 3 | $2.68 | $0.8927 | 3 | $3.04 | $1.0146 | 3 | $2.89 | $0.9648 | 3 | $2.46 | $0.8199 | $0.1313 |
| lofreq_filter | 2 | 3 | $2.39 | $0.7956 | 3 | $3.11 | $1.0360 | 3 | $2.70 | $0.9011 | 3 | $2.30 | $0.7652 | $0.0002 |
| snpEff | 2 | 3 | $2.29 | $0.7624 | 3 | $3.13 | $1.0442 | 3 | $2.72 | $0.9081 | 3 | $2.31 | $0.7705 | -- |
| lofreq_viterbi | 4 | 3 | $1.86 | $0.6204 | 3 | $2.33 | $0.7771 | 3 | $2.12 | $0.7051 | 3 | $1.73 | $0.5762 | $0.0093 |
| lofreq_call | 2 | 3 | $1.78 | $0.5925 | 3 | $2.41 | $0.8036 | 3 | $2.01 | $0.6697 | 3 | $1.71 | $0.5697 | $0.0555 |
| picard_MarkDuplicates | 4 | 3 | $1.71 | $0.5690 | 3 | $2.04 | $0.6793 | 3 | $1.85 | $0.6164 | 3 | $1.58 | $0.5260 | -- |
| lofreq_indelqual | 2 | 3 | $1.34 | $0.4462 | 3 | $1.82 | $0.6062 | 3 | $1.58 | $0.5273 | 3 | $1.25 | $0.4156 | $0.0008 |
| multiqc | 2 | 3 | $1.18 | $0.3926 | 3 | $1.51 | $0.5019 | 3 | $1.31 | $0.4365 | 3 | $1.09 | $0.3636 | $0.0013 |
| samtools_stats | 2 | 3 | $0.76 | $0.2530 | 3 | $1.03 | $0.3447 | 3 | $0.86 | $0.2873 | 3 | $0.70 | $0.2336 | $0.0009 |
| samtools_view | 2 | 3 | $0.74 | $0.2465 | 3 | $0.78 | $0.2593 | 3 | $0.00 | $0.0000 | 3 | $0.00 | $0.0000 | $0.0020 |
| fastp | 4 | 3 | $0.10 | $0.0343 | 3 | $0.29 | $0.0963 | 3 | $0.27 | $0.0892 | 3 | $0.10 | $0.0330 | $0.0080 |
| snpEff_build_gb | 2 | 3 | $0.15 | $0.0507 | 3 | $0.10 | $0.0319 | 3 | $0.08 | $0.0278 | 3 | $0.11 | $0.0373 | -- |

## Rainstone Comparison

Per-job compute cost comparison against [Rainstone](https://rainstone.anvilproject.org) historical averages from usegalaxy.org. Rainstone data reflects median costs across thousands of production runs.

| Tool | Batch $/Job | Pulsar $/Job | Pulsar+K8s $/Job | Batch+K8s $/Job | Rainstone Avg | Rainstone Median | Rainstone P95 | usegalaxy.org Jobs |
|------| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| bwa_mem | $0.7229 | $0.7134 | $0.6784 | $0.6896 | $0.1313 | $0.0097 | $0.5610 | 158,991 |
| lofreq_filter | $0.0001 | $0.0000 | $0.0000 | $0.0001 | $0.0002 | $0.0001 | $0.0004 | 60,578 |
| snpEff | $0.0002 | $0.0003 | $0.0003 | $0.0003 | -- | -- | -- | -- |
| lofreq_viterbi | $0.0416 | $0.0395 | $0.0359 | $0.0407 | $0.0093 | $0.0023 | $0.0311 | 49,601 |
| lofreq_call | $0.2546 | $0.3024 | $0.2520 | $0.2547 | $0.0555 | $0.0103 | $0.1374 | 70,976 |
| picard_MarkDuplicates | $0.0758 | $0.0502 | $0.0456 | $0.0720 | -- | -- | -- | -- |
| lofreq_indelqual | $0.0157 | $0.0140 | $0.0122 | $0.0155 | $0.0008 | $0.0003 | $0.0018 | 46,590 |
| multiqc | $0.0003 | $0.0001 | $0.0001 | $0.0003 | $0.0013 | $0.0005 | $0.0036 | 75,021 |
| samtools_stats | $0.0036 | $0.0040 | $0.0033 | $0.0038 | $0.0009 | $0.0003 | $0.0033 | 88,828 |
| samtools_view | $0.0101 | $0.0091 | $0.0000 | $0.0000 | $0.0020 | $0.0004 | $0.0051 | 83,527 |
| fastp | $0.0255 | $0.0267 | $0.0247 | $0.0249 | $0.0080 | $0.0020 | $0.0350 | 212,086 |
| snpEff_build_gb | $0.0438 | $0.0076 | $0.0066 | $0.0313 | -- | -- | -- | -- |

## K8s-Only Deployment Estimate

Cost if all jobs ran on a GKE Standard cluster (n2-standard-16, 16 vCPU, 64 GB) without GCP Batch. Jobs run sequentially. Duration is the greater of the sum of compute times or the observed wallclock (for workflows that run tools concurrently).

- **VM hourly rate:** $0.8769/hour (N2 compute $0.7769 + GKE management $0.10)
- **Duration:** 17.1h
- **Total cost:** $15.00

## Deployment Model Comparison

| Model | Duration | Cost |
|-------|----------|------|
| **K8s-Only** (GKE Standard, n2-standard-16) | 17.1h | **$15.00** |
| **Batch** (GCP Batch + e2-standard-4) | 17.8h | **$19.41** |
| **Pulsar** (GCP Batch + e2-standard-4) | 20.2h | **$24.36** |
| **Pulsar+K8s** (GCP Batch + e2-standard-4) | 20.2h | **$21.17** |
| **Batch+K8s** (GCP Batch + e2-standard-4) | 17.1h | **$17.68** |
| **Local VM** (n2-standard-20, Batch duration) | 17.8h | **$17.27** |

## Pricing Assumptions

All costs estimated using GCP on-demand pricing for `us-east4`.

| Resource | Rate |
|----------|------|
| N2 vCPU | $0.031611/vCPU/hour |
| N2 Memory | $0.004237/GB/hour |
| Local SSD | $5.4e-05/GB/hour |
| Boot Disk (pd-balanced) | $0.1/GB/month |
| Galaxy VM (e2-standard-4) | $0.1375/hour |
| GKE Standard mgmt fee | $0.1/hour |
| K8s-Only (16 vCPU, 64 GB + GKE) | $0.8769/hour |
| Local n2-standard-20 | $0.9712/hour |

Rainstone estimates are sourced from the [Rainstone Cost API](https://rainstone.anvilproject.org/api/docs) and reflect historical averages across usegalaxy.org production workloads.
