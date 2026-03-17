---
title: Variant Calling Cost Summary
---

# Variant Calling Cost Summary

**[Interactive Cost Charts](cost-chartss.html)** | **[Performance Report](index.html)** | **[Performance Charts](charts.html)**

**Period:** 2026-03-16 19:36 to 2026-03-17 15:23 UTC  
**Region:** us-east4  
**Total Jobs:** 72 (ok)

## Runner Summary

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 36 | 16.7h | $2.21 | $1.24 | $0.00 | $0.07 | **$3.52** |
| **Pulsar** | 36 | 14.7h | $1.98 | $1.09 | $0.30 | $0.06 | **$3.43** |
| **Total** | 72 | 31.4h | $4.18 | $2.33 | $0.30 | $0.13 | **$6.95** |

Pulsar costs **$3.43** vs Batch **$3.52** (1.0x).

### Cost Component Breakdown

| Component | Batch | Pulsar | Total | % |
|-----------|-------|--------|-------|---|
| vCPU | $2.21 | $1.98 | $4.18 | 60% |
| Memory | $1.24 | $1.09 | $2.33 | 34% |
| Local SSD | $0.00 | $0.30 | $0.30 | 4% |
| Boot Disk | $0.07 | $0.06 | $0.13 | 2% |
| **Total** | **$3.52** | **$3.43** | **$6.95** | |

Note: Batch jobs use NFS for file staging (no local SSD cost). Pulsar jobs each provision a 375 GB local SSD.

## Per-Tool Cost Comparison

### Tools on Both Runners

The Rainstone Est. column shows the average cost per job from the [Rainstone cost API](https://rainstone.anvilproject.org/api/docs), based on historical AnVIL platform usage.

| Tool | vCPU | Batch Jobs | Batch Cost | Batch $/Job | Pulsar Jobs | Pulsar Cost | Pulsar $/Job | Rainstone Est. |
|------|------|-----------|------------|-------------|------------|-------------|--------------|----------------|
| bwa_mem | 8 | 3 | $2.09 | $0.6969 | 3 | $2.08 | $0.6933 | $0.1313 |
| lofreq_call | 2 | 3 | $0.76 | $0.2535 | 3 | $0.90 | $0.3008 | $0.0555 |
| picard_MarkDuplicates | 4 | 3 | $0.24 | $0.0814 | 3 | $0.14 | $0.0481 | $0.0138 |
| snpEff_build_gb | 2 | 3 | $0.13 | $0.0426 | 3 | $0.02 | $0.0076 | $0.0040 |
| lofreq_viterbi | 4 | 3 | $0.13 | $0.0426 | 3 | $0.12 | $0.0394 | $0.0093 |
| fastp | 4 | 3 | $0.07 | $0.0246 | 3 | $0.08 | $0.0263 | $0.0080 |
| lofreq_indelqual | 2 | 3 | $0.05 | $0.0168 | 3 | $0.04 | $0.0137 | $0.0008 |
| samtools_view | 2 | 3 | $0.03 | $0.0103 | 3 | $0.03 | $0.0089 | $0.0020 |
| samtools_stats | 2 | 3 | $0.01 | $0.0037 | 3 | $0.01 | $0.0040 | $0.0009 |
| multiqc | 2 | 3 | $0.00 | $0.0004 | 3 | $0.00 | $0.0001 | $0.0013 |
| snpEff | 2 | 3 | $0.00 | $0.0002 | 3 | $0.00 | $0.0002 | $0.0056 |
| lofreq_filter | 2 | 3 | $0.00 | $0.0001 | 3 | $0.00 | $0.0000 | $0.0002 |
| **Total** | | **36** | **$3.52** | | **36** | **$3.43** | | |

## Rainstone Comparison

Per-job cost comparison against [Rainstone](https://rainstone.anvilproject.org) historical averages from the AnVIL platform. Rainstone data reflects median costs across thousands of production runs.

| Tool | Batch $/Job | Pulsar $/Job | Rainstone Avg | Rainstone Median | Rainstone P95 | AnVIL Jobs |
|------|-------------|--------------|---------------|-----------------|---------------|------------|
| bwa_mem | $0.6969 | $0.6933 | $0.1313 | $0.0097 | $0.5610 | 158,991 |
| lofreq_call | $0.2535 | $0.3008 | $0.0555 | $0.0103 | $0.1374 | 70,976 |
| picard_MarkDuplicates | $0.0814 | $0.0481 | $0.0138 | $0.0029 | $0.0620 | 75,663 |
| snpEff_build_gb | $0.0426 | $0.0076 | $0.0040 | $0.0006 | $0.0069 | 3,074 |
| lofreq_viterbi | $0.0426 | $0.0394 | $0.0093 | $0.0023 | $0.0311 | 49,601 |
| fastp | $0.0246 | $0.0263 | $0.0080 | $0.0020 | $0.0350 | 212,086 |
| lofreq_indelqual | $0.0168 | $0.0137 | $0.0008 | $0.0003 | $0.0018 | 46,590 |
| samtools_view | $0.0103 | $0.0089 | $0.0020 | $0.0004 | $0.0051 | 83,527 |
| samtools_stats | $0.0037 | $0.0040 | $0.0009 | $0.0003 | $0.0033 | 88,828 |
| multiqc | $0.0004 | $0.0001 | $0.0013 | $0.0005 | $0.0036 | 75,021 |
| snpEff | $0.0002 | $0.0002 | $0.0056 | $0.0023 | $0.0151 | 33,045 |
| lofreq_filter | $0.0001 | $0.0000 | $0.0002 | $0.0001 | $0.0004 | 60,578 |

## Pricing Assumptions

All costs are estimated using GCP N2 on-demand pricing for `us-east4`:

| Resource | Rate |
|----------|------|
| N2 vCPU | $0.031611/vCPU/hour |
| N2 Memory | $0.004237/GB/hour |
| Local SSD | $0.000054/GB/hour |
| Boot Disk (pd-balanced) | $0.10/GB/month |

Pulsar jobs each provision a 375 GB local SSD and a 30 GB boot disk. Batch jobs use NFS for staging (no local SSD). VM machine types are selected automatically based on tool CPU and memory requirements via `compute_machine_type()`.

Rainstone estimates are sourced from the [Rainstone Cost API](https://rainstone.anvilproject.org/api/docs) and reflect historical averages across AnVIL platform production workloads.
