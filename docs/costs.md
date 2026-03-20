---
title: Variant Analysis Cost Summary
---

# Variant Analysis Cost Summary

**[Interactive Cost Charts](cost-charts.html)** | **[Performance Report](index.html)** | **[Performance Charts](charts.html)**

**Period:** 2026-03-16 19:36:51 to 2026-03-17 16:33:35 UTC  
**Region:** us-east4  
**Total Jobs:** 96 (ok)

## Runner Summary

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 56 | 19.1h | $3.06 | $1.70 | $0.00 | $0.08 | **$4.85** |
| **Pulsar** | 40 | 15.6h | $2.41 | $1.32 | $0.31 | $0.06 | **$4.11** |
| **Total** | 96 | 34.6h | $5.47 | $3.03 | $0.31 | $0.14 | **$8.95** |

Pulsar costs **$4.11** vs Batch **$4.85** (0.8x).

### Cost Component Breakdown

| Component | Batch | Pulsar | Total | % |
|-----------|-------|--------|-------|---|
| vCPU | $3.06 | $2.41 | $5.47 | 61% |
| Memory | $1.70 | $1.32 | $3.03 | 34% |
| Local SSD | $0.00 | $0.31 | $0.31 | 4% |
| Boot Disk | $0.08 | $0.06 | $0.14 | 2% |
| **Total** | **$4.85** | **$4.11** | **$8.95** | |

Note: Batch jobs use NFS for file staging (no local SSD cost). Pulsar jobs each provision a 375 GB local SSD.

## Per-Tool Cost Comparison

### Tools on Both Runners

The Rainstone Est. column shows the average cost per job from the [Rainstone cost API](https://rainstone.anvilproject.org/api/docs), based on historical usegalaxy.org usage.

| Tool | vCPU | Batch Jobs | Batch Cost | Batch $/Job | Pulsar Jobs | Pulsar Cost | Pulsar $/Job | Rainstone Est. |
|------|------|-----------|------------|-------------|------------|-------------|--------------|----------------|
| bwa_mem | 8 | 3 | $2.09 | $0.6969 | 3 | $2.08 | $0.6933 | $0.1313 |
| lofreq_call | 2 | 3 | $0.76 | $0.2535 | 3 | $0.90 | $0.3008 | $0.0555 |
| rna_star | 16 | 1 | $1.00 | $0.9985 | 1 | $0.66 | $0.6622 | $0.9108 |
| picard_MarkDuplicates | 4 | 3 | $0.24 | $0.0814 | 3 | $0.14 | $0.0481 | -- |
| cufflinks | 8 | 1 | $0.28 | $0.2796 | 0 | $0.00 | $0.0000 | $0.2317 |
| lofreq_viterbi | 4 | 3 | $0.13 | $0.0426 | 3 | $0.12 | $0.0394 | $0.0093 |
| fastp | 4 | 3 | $0.07 | $0.0246 | 3 | $0.08 | $0.0263 | $0.0080 |
| snpEff_build_gb | 2 | 3 | $0.13 | $0.0426 | 3 | $0.02 | $0.0076 | -- |
| lofreq_indelqual | 2 | 3 | $0.05 | $0.0168 | 3 | $0.04 | $0.0137 | $0.0008 |
| samtools_view | 2 | 3 | $0.03 | $0.0103 | 3 | $0.03 | $0.0089 | $0.0020 |
| cutadapt | 8 | 1 | $0.02 | $0.0192 | 1 | $0.02 | $0.0166 | $0.0182 |
| samtools_stats | 2 | 3 | $0.01 | $0.0037 | 3 | $0.01 | $0.0040 | $0.0009 |
| bamFilter | 2 | 1 | $0.01 | $0.0126 | 0 | $0.00 | $0.0000 | -- |
| bedtools_genomecoveragebed | 2 | 3 | $0.01 | $0.0031 | 0 | $0.00 | $0.0000 | $0.0016 |
| revertR2orientationInBam | 2 | 1 | $0.01 | $0.0054 | 0 | $0.00 | $0.0000 | -- |
| multiqc | 2 | 4 | $0.00 | $0.0004 | 4 | $0.00 | $0.0002 | $0.0013 |
| wig_to_bigWig | 2 | 3 | $0.00 | $0.0006 | 0 | $0.00 | $0.0000 | -- |
| snpEff | 2 | 3 | $0.00 | $0.0002 | 3 | $0.00 | $0.0002 | -- |
| map_param_value | 2 | 4 | $0.00 | $0.0002 | 0 | $0.00 | $0.0000 | -- |
| param_value_from_file | 2 | 1 | $0.00 | $0.0003 | 0 | $0.00 | $0.0000 | $0.0003 |
| lofreq_filter | 2 | 3 | $0.00 | $0.0001 | 3 | $0.00 | $0.0000 | $0.0002 |
| compose_text_param | 2 | 1 | $0.00 | $0.0002 | 0 | $0.00 | $0.0000 | -- |
| tp_awk_tool | 2 | 2 | $0.00 | $0.0000 | 1 | $0.00 | $0.0000 | $0.0017 |
| **Total** | | **56** | **$4.85** | | **40** | **$4.11** | | |

## Rainstone Comparison

Per-job cost comparison against [Rainstone](https://rainstone.anvilproject.org) historical averages from usegalaxy.org. Rainstone data reflects median costs across thousands of production runs.

| Tool | Batch $/Job | Pulsar $/Job | Rainstone Avg | Rainstone Median | Rainstone P95 | usegalaxy.org Jobs |
|------|-------------|--------------|---------------|-----------------|---------------|------------|
| bwa_mem | $0.6969 | $0.6933 | $0.1313 | $0.0097 | $0.5610 | 158,991 |
| lofreq_call | $0.2535 | $0.3008 | $0.0555 | $0.0103 | $0.1374 | 70,976 |
| rna_star | $0.9985 | $0.6622 | $0.9108 | $0.2144 | $4.3362 | 124,843 |
| picard_MarkDuplicates | $0.0814 | $0.0481 | -- | -- | -- | -- |
| cufflinks | $0.2796 | $0.0000 | $0.2317 | $0.0413 | $1.0701 | 29,585 |
| lofreq_viterbi | $0.0426 | $0.0394 | $0.0093 | $0.0023 | $0.0311 | 49,601 |
| fastp | $0.0246 | $0.0263 | $0.0080 | $0.0020 | $0.0350 | 212,086 |
| snpEff_build_gb | $0.0426 | $0.0076 | -- | -- | -- | -- |
| lofreq_indelqual | $0.0168 | $0.0137 | $0.0008 | $0.0003 | $0.0018 | 46,590 |
| samtools_view | $0.0103 | $0.0089 | $0.0020 | $0.0004 | $0.0051 | 83,527 |
| cutadapt | $0.0192 | $0.0166 | $0.0182 | $0.0028 | $0.0703 | 167,606 |
| samtools_stats | $0.0037 | $0.0040 | $0.0009 | $0.0003 | $0.0033 | 88,828 |
| bamFilter | $0.0126 | $0.0000 | -- | -- | -- | -- |
| bedtools_genomecoveragebed | $0.0031 | $0.0000 | $0.0016 | $0.0003 | $0.0056 | 47,439 |
| revertR2orientationInBam | $0.0054 | $0.0000 | -- | -- | -- | -- |
| multiqc | $0.0004 | $0.0002 | $0.0013 | $0.0005 | $0.0036 | 75,021 |
| wig_to_bigWig | $0.0006 | $0.0000 | -- | -- | -- | -- |
| snpEff | $0.0002 | $0.0002 | -- | -- | -- | -- |
| map_param_value | $0.0002 | $0.0000 | -- | -- | -- | -- |
| param_value_from_file | $0.0003 | $0.0000 | $0.0003 | $0.0002 | $0.0004 | 11,628 |
| lofreq_filter | $0.0001 | $0.0000 | $0.0002 | $0.0001 | $0.0004 | 60,578 |
| compose_text_param | $0.0002 | $0.0000 | -- | -- | -- | -- |
| tp_awk_tool | $0.0000 | $0.0000 | $0.0017 | $0.0002 | $0.0074 | 16,297 |

## Pricing Assumptions

All costs are estimated using GCP N2 on-demand pricing for `us-east4`:

| Resource | Rate |
|----------|------|
| N2 vCPU | $0.031611/vCPU/hour |
| N2 Memory | $0.004237/GB/hour |
| Local SSD | $5.4e-05/GB/hour |
| Boot Disk (pd-balanced) | $0.1/GB/month |

Pulsar jobs each provision a 375 GB local SSD and a 30 GB boot disk. Batch jobs use NFS for staging (no local SSD). VM machine types are selected automatically based on tool CPU and memory requirements via `compute_machine_type()`.

Rainstone estimates are sourced from the [Rainstone Cost API](https://rainstone.anvilproject.org/api/docs) and reflect historical averages across usegalaxy.org production workloads.
