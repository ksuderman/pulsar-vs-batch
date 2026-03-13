---
title: GCP Batch Cost Summary
---

# GCP Batch Cost Summary

**Period:** 48 hours ending 2026-03-13 19:10 UTC  
**Region:** us-east4  
**Total Jobs:** 203

## Runner Summary

| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |
|--------|------|----------|-----------|-------------|----------|-----------|------------|
| **Batch** | 128 | 62.8h | $13.39 | $7.63 | $0.00 | $0.26 | **$21.28** |
| **Pulsar** | 75 | 245.4h | $20.72 | $11.40 | $9.94 | $1.01 | **$43.06** |
| **Total** | **203** | **308.2h** | **$34.11** | **$19.03** | **$9.94** | **$1.27** | **$64.34** |

Pulsar costs **$43.06** vs Batch **$21.28** (2.0x). However, **$40.25** (93% of Pulsar spend) was wasted on stuck jobs caused by the input staging bug.

### Cost Component Breakdown

| Component | Batch | Pulsar | Total | % |
|-----------|-------|--------|-------|---|
| vCPU | $13.39 | $20.72 | $34.11 | 53% |
| Memory | $7.63 | $11.40 | $19.03 | 30% |
| Local SSD | $0.00 | $9.94 | $9.94 | 15% |
| Boot Disk | $0.26 | $1.01 | $1.27 | 2% |
| **Total** | **$21.28** | **$43.06** | **$64.34** | |

Note: Batch jobs use NFS for file staging (no local SSD cost). Pulsar jobs each provision a 750 GB local SSD.

## Per-Tool Cost Comparison

### Tools on Both Runners

| Tool | vCPU | Batch Jobs | Batch Hrs | Batch Cost | Pulsar Jobs | Pulsar Hrs | Pulsar Cost | Diff |
|------|------|-----------|-----------|------------|------------|------------|-------------|------|
| map_param_value | 2 | 12 | 0.2h | $0.02 | 12 | 168.8h | $23.92 | +124835% |
| bwa_mem | 8 | 7 | 34.8h | $13.65 | 4 | 17.2h | $7.45 | -45% |
| compose_text_param | 2 | 3 | 0.0h | $0.00 | 3 | 42.2h | $5.98 | - |
| rna_star | 16 | 3 | 3.0h | $2.31 | 3 | 3.0h | $2.47 | +7% |
| lofreq_call | 2 | 5 | 11.1h | $1.12 | 3 | 5.7h | $0.81 | -28% |
| snpEff_build_gb | 8 | 7 | 2.4h | $1.27 | 5 | 0.6h | $0.34 | -73% |
| fastp | 4 | 7 | 0.7h | $0.26 | 5 | 1.5h | $0.63 | +144% |
| picard_MarkDuplicates | 4 | 5 | 1.8h | $0.35 | 5 | 1.1h | $0.27 | -22% |
| cutadapt | 8 | 3 | 0.4h | $0.16 | 4 | 0.9h | $0.40 | +145% |
| lofreq_viterbi | 4 | 5 | 1.0h | $0.19 | 3 | 1.0h | $0.24 | +27% |
| bamFilter | 2 | 3 | 1.0h | $0.14 | 3 | 1.2h | $0.21 | +49% |
| lofreq_indelqual | 2 | 5 | 0.6h | $0.08 | 3 | 0.8h | $0.13 | +74% |
| samtools_view | 2 | 5 | 0.5h | $0.05 | 3 | 0.5h | $0.07 | +51% |
| multiqc | 2 | 8 | 0.1h | $0.01 | 7 | 0.4h | $0.08 | +607% |
| samtools_stats | 2 | 5 | 0.2h | $0.02 | 3 | 0.3h | $0.04 | +119% |
| tp_awk_tool | 2 | 6 | 0.0h | $0.00 | 3 | 0.1h | $0.01 | - |
| snpEff | 2 | 6 | 0.1h | $0.01 | 3 | 0.0h | $0.01 | -23% |
| lofreq_filter | 2 | 6 | 0.0h | $0.01 | 3 | 0.0h | $0.01 | +16% |
| **Total** | | **101** | | **$19.65** | **75** | | **$43.06** | **+119%** |

### Batch Only

| Tool | vCPU | Jobs | VM-Hours | Cost |
|------|------|------|----------|------|
| cufflinks | 8 | 3 | 3.8h | $1.49 |
| bedtools_genomecoveragebed | 2 | 9 | 0.7h | $0.07 |
| revertR2orientationInBam | 2 | 3 | 0.5h | $0.05 |
| wig_to_bigWig | 4 | 9 | 0.1h | $0.02 |
| param_value_from_file | 2 | 3 | 0.0h | $0.00 |

## Cost Anomalies

**19 stuck/long-running jobs** consumed **$40.25** (63% of total spend). These were Pulsar jobs for lightweight parameter tools (`map_param_value`, `compose_text_param`) that hung indefinitely due to the input staging bug — files were never transferred to the GCP Batch VM because the tool's `command_line` was `None`.

| Job ID | Tool | Machine Type | Hours Running | Cost |
|--------|------|-------------|---------------|------|
| galaxy-job-1773339605-a0d77725 | bwa_mem | n2-standard-8 | 24.8h | $9.74 |
| pulsar-36-1773373566 | compose_text_param | n2-standard-2 | 15.4h | $2.18 |
| pulsar-38-1773373566 | map_param_value | n2-standard-2 | 15.4h | $2.18 |
| pulsar-39-1773373565 | map_param_value | n2-standard-2 | 15.4h | $2.18 |
| pulsar-37-1773373565 | map_param_value | n2-standard-2 | 15.4h | $2.18 |
| pulsar-40-1773373566 | map_param_value | n2-standard-2 | 15.4h | $2.18 |
| pulsar-50-1773378114 | compose_text_param | n2-standard-2 | 14.1h | $2.00 |
| pulsar-53-1773378115 | map_param_value | n2-standard-2 | 14.1h | $2.00 |
| pulsar-52-1773378115 | map_param_value | n2-standard-2 | 14.1h | $2.00 |
| pulsar-51-1773378115 | map_param_value | n2-standard-2 | 14.1h | $2.00 |
| pulsar-54-1773378115 | map_param_value | n2-standard-2 | 14.1h | $2.00 |
| pulsar-67-1773382951 | map_param_value | n2-standard-2 | 12.7h | $1.81 |
| pulsar-65-1773382950 | compose_text_param | n2-standard-2 | 12.7h | $1.81 |
| pulsar-68-1773382951 | map_param_value | n2-standard-2 | 12.7h | $1.81 |
| pulsar-66-1773382950 | map_param_value | n2-standard-2 | 12.7h | $1.81 |
| pulsar-69-1773382952 | map_param_value | n2-standard-2 | 12.7h | $1.81 |
| galaxy-job-1773423280-f2fdd8ee | bwa_mem | n2-standard-8 | 1.6h | $0.61 |
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
