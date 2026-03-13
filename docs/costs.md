---
title: GCP Batch Cost Summary
---

# GCP Batch Cost Summary

**Period:** 48 hours ending 2026-03-13 20:28 UTC  
**Region:** us-east4  
**Total Jobs:** 203

## Runner Summary

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 128 | 65.4h | $14.05 | $7.99 | $0.00 | $0.27 | **$22.30** |
| **Pulsar** | 75 | 264.9h | $21.95 | $12.06 | $10.73 | $1.09 | **$45.82** |
| **Total** | **203** | **330.3h** | **$36.00** | **$20.05** | **$10.73** | **$1.36** | **$68.13** |

Pulsar costs **$45.82** vs Batch **$22.30** (2.1x). However, **$44.04** (96% of Pulsar spend) was wasted on stuck jobs caused by the input staging bug.

### Cost Component Breakdown

| Component | Batch | Pulsar | Total | % |
|-----------|-------|--------|-------|---|
| vCPU | $14.05 | $21.95 | $36.00 | 53% |
| Memory | $7.99 | $12.06 | $20.05 | 29% |
| Local SSD | $0.00 | $10.73 | $10.73 | 16% |
| Boot Disk | $0.27 | $1.09 | $1.36 | 2% |
| **Total** | **$22.30** | **$45.82** | **$68.13** | |

Note: Batch jobs use NFS for file staging (no local SSD cost). Pulsar jobs each provision a 750 GB local SSD.

## Per-Tool Cost Comparison

### Tools on Both Runners

The Rainstone Est. column shows the average cost per job from the [Rainstone cost API](https://rainstone.anvilproject.org/api/docs), based on historical AnVIL platform usage.

| Tool | vCPU | Batch Jobs | Batch Cost | Batch $/Job | Pulsar Jobs | Pulsar Cost | Pulsar $/Job | Rainstone Est. |
|------|------|-----------|------------|-------------|------------|-------------|--------------|----------------|
| map_param_value | 2 | 12 | $0.02 | $0.0016 | 12 | $26.13 | $2.1775 | - |
| bwa_mem | 8 | 7 | $14.67 | $2.0964 | 4 | $7.45 | $1.8617 | $0.1313 |
| compose_text_param | 2 | 3 | $0.00 | $0.0016 | 3 | $6.53 | $2.1777 | - |
| rna_star | 16 | 3 | $2.31 | $0.7698 | 3 | $2.47 | $0.8223 | $0.9108 |
| lofreq_call | 2 | 5 | $1.12 | $0.2242 | 3 | $0.81 | $0.2705 | $0.0555 |
| snpEff_build_gb | 8 | 7 | $1.27 | $0.1807 | 5 | $0.34 | $0.0675 | $0.0056 |
| fastp | 4 | 7 | $0.26 | $0.0371 | 5 | $0.63 | $0.1267 | $0.0080 |
| picard_MarkDuplicates | 4 | 5 | $0.35 | $0.0703 | 5 | $0.27 | $0.0547 | $0.0138 |
| cutadapt | 8 | 3 | $0.16 | $0.0541 | 4 | $0.40 | $0.0993 | $0.0182 |
| lofreq_viterbi | 4 | 5 | $0.19 | $0.0382 | 3 | $0.24 | $0.0810 | $0.0093 |
| bamFilter | 2 | 3 | $0.14 | $0.0462 | 3 | $0.21 | $0.0687 | $0.0030 |
| lofreq_indelqual | 2 | 5 | $0.08 | $0.0154 | 3 | $0.13 | $0.0445 | $0.0008 |
| samtools_view | 2 | 5 | $0.05 | $0.0093 | 3 | $0.07 | $0.0235 | $0.0020 |
| multiqc | 2 | 8 | $0.01 | $0.0013 | 7 | $0.08 | $0.0108 | $0.0013 |
| samtools_stats | 2 | 5 | $0.02 | $0.0036 | 3 | $0.04 | $0.0131 | $0.0009 |
| tp_awk_tool | 2 | 6 | $0.00 | $0.0003 | 3 | $0.01 | $0.0046 | $0.0017 |
| snpEff | 2 | 6 | $0.01 | $0.0015 | 3 | $0.01 | $0.0023 | $0.0056 |
| lofreq_filter | 2 | 6 | $0.01 | $0.0009 | 3 | $0.01 | $0.0020 | $0.0002 |
| **Total** | | **101** | **$20.67** | | **75** | **$45.82** | | |

### Batch Only

| Tool | vCPU | Jobs | VM-Hours | Cost | $/Job | Rainstone Est. |
|------|------|------|----------|------|-------|----------------|
| cufflinks | 8 | 3 | 3.8h | $1.49 | $0.4972 | $0.2317 |
| bedtools_genomecoveragebed | 2 | 9 | 0.7h | $0.07 | $0.0079 | $0.0016 |
| revertR2orientationInBam | 2 | 3 | 0.5h | $0.05 | $0.0153 | - |
| wig_to_bigWig | 4 | 9 | 0.1h | $0.02 | $0.0027 | $0.0084 |
| param_value_from_file | 2 | 3 | 0.0h | $0.00 | $0.0016 | $0.0003 |

## Rainstone Comparison

Per-job cost comparison against [Rainstone](https://rainstone.anvilproject.org) historical averages from the AnVIL platform. Rainstone data reflects median costs across thousands of production runs.

| Tool | Batch $/Job | Pulsar $/Job | Rainstone Avg | Rainstone Median | Rainstone P95 | AnVIL Jobs |
|------|-------------|--------------|---------------|-----------------|---------------|------------|
| rna_star | $0.7698 | $0.8223 | $0.9108 | $0.2144 | $4.3362 | 124,843 |
| cufflinks | $0.4972 | - | $0.2317 | $0.0413 | $1.0701 | 29,585 |
| bwa_mem | $2.0964 | $1.8617 | $0.1313 | $0.0097 | $0.5610 | 158,991 |
| lofreq_call | $0.2242 | $0.2705 | $0.0555 | $0.0103 | $0.1374 | 70,976 |
| cutadapt | $0.0541 | $0.0993 | $0.0182 | $0.0028 | $0.0703 | 167,606 |
| picard_MarkDuplicates | $0.0703 | $0.0547 | $0.0138 | $0.0029 | $0.0620 | 75,663 |
| lofreq_viterbi | $0.0382 | $0.0810 | $0.0093 | $0.0023 | $0.0311 | 49,601 |
| wig_to_bigWig | $0.0027 | - | $0.0084 | $0.0063 | $0.0236 | 14,711 |
| fastp | $0.0371 | $0.1267 | $0.0080 | $0.0020 | $0.0350 | 212,086 |
| snpEff | $0.0015 | $0.0023 | $0.0056 | $0.0023 | $0.0151 | 33,045 |
| snpEff_build_gb | $0.1807 | $0.0675 | $0.0056 | $0.0023 | $0.0151 | 33,045 |
| bamFilter | $0.0462 | $0.0687 | $0.0030 | $0.0003 | $0.0074 | 28,687 |
| samtools_view | $0.0093 | $0.0235 | $0.0020 | $0.0004 | $0.0051 | 83,527 |
| tp_awk_tool | $0.0003 | $0.0046 | $0.0017 | $0.0002 | $0.0074 | 16,297 |
| bedtools_genomecoveragebed | $0.0079 | - | $0.0016 | $0.0003 | $0.0056 | 47,439 |
| multiqc | $0.0013 | $0.0108 | $0.0013 | $0.0005 | $0.0036 | 75,021 |
| samtools_stats | $0.0036 | $0.0131 | $0.0009 | $0.0003 | $0.0033 | 88,828 |
| lofreq_indelqual | $0.0154 | $0.0445 | $0.0008 | $0.0003 | $0.0018 | 46,590 |
| param_value_from_file | $0.0016 | - | $0.0003 | $0.0002 | $0.0004 | 11,628 |
| lofreq_filter | $0.0009 | $0.0020 | $0.0002 | $0.0001 | $0.0004 | 60,578 |
| compose_text_param | $0.0016 | $2.1777 | - | - | - | - |
| map_param_value | $0.0016 | $2.1775 | - | - | - | - |
| revertR2orientationInBam | $0.0153 | - | - | - | - | - |

## Cost Anomalies

**19 stuck/long-running jobs** consumed **$44.04** (65% of total spend). These were Pulsar jobs for lightweight parameter tools (`map_param_value`, `compose_text_param`) that hung indefinitely due to the input staging bug — files were never transferred to the GCP Batch VM because the tool's `command_line` was `None`.

| Job ID | Tool | Machine Type | Hours Running | Cost |
|--------|------|-------------|---------------|------|
| galaxy-job-1773339605-a0d77725 | bwa_mem | n2-standard-8 | 26.1h | $10.25 |
| pulsar-36-1773373566 | compose_text_param | n2-standard-2 | 16.7h | $2.36 |
| pulsar-38-1773373566 | map_param_value | n2-standard-2 | 16.7h | $2.36 |
| pulsar-39-1773373565 | map_param_value | n2-standard-2 | 16.7h | $2.36 |
| pulsar-37-1773373565 | map_param_value | n2-standard-2 | 16.7h | $2.36 |
| pulsar-40-1773373566 | map_param_value | n2-standard-2 | 16.7h | $2.36 |
| pulsar-50-1773378114 | compose_text_param | n2-standard-2 | 15.4h | $2.18 |
| pulsar-53-1773378115 | map_param_value | n2-standard-2 | 15.4h | $2.18 |
| pulsar-52-1773378115 | map_param_value | n2-standard-2 | 15.4h | $2.18 |
| pulsar-51-1773378115 | map_param_value | n2-standard-2 | 15.4h | $2.18 |
| pulsar-54-1773378115 | map_param_value | n2-standard-2 | 15.4h | $2.18 |
| pulsar-67-1773382951 | map_param_value | n2-standard-2 | 14.0h | $1.99 |
| pulsar-65-1773382950 | compose_text_param | n2-standard-2 | 14.0h | $1.99 |
| pulsar-68-1773382951 | map_param_value | n2-standard-2 | 14.0h | $1.99 |
| pulsar-66-1773382950 | map_param_value | n2-standard-2 | 14.0h | $1.99 |
| pulsar-69-1773382952 | map_param_value | n2-standard-2 | 14.0h | $1.99 |
| galaxy-job-1773423280-f2fdd8ee | bwa_mem | n2-standard-8 | 2.9h | $1.12 |
| pulsar-90-1773424639 | fastp | n2-highmem-4 | 0.0h | $0.00 |
| pulsar-91-1773424639 | snpEff_build_gb | n2-highmem-8 | 0.0h | $0.00 |

## Pricing Assumptions

All costs are estimated using GCP N2 on-demand pricing for `us-east4`:

| Resource | Rate |
|----------|------|
| N2 vCPU | $0.031611/vCPU/hour |
| N2 Memory | $0.004237/GB/hour |
| Local SSD | $0.000054/GB/hour |
| Boot Disk (pd-balanced) | $0.10/GB/month |

Pulsar jobs each provision a 750 GB local SSD and a 30 GB boot disk. Batch jobs use NFS for staging (no local SSD). VM machine types are selected automatically based on tool CPU and memory requirements via `compute_machine_type()`.

Rainstone estimates are sourced from the [Rainstone Cost API](https://rainstone.anvilproject.org/api/docs) and reflect historical averages across AnVIL platform production workloads. Tools not found in the Rainstone database: `map_param_value`, `compose_text_param`, `revertR2orientationInBam`.
