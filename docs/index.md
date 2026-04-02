---
title: Galaxy GCP Batch Benchmarks
---

# Galaxy GCP Batch Benchmarks

Benchmarking three strategies for running Galaxy jobs on Google Cloud Platform.

## Runners Compared

| Runner | Description | Job Dispatch | File Transfer |
|--------|-------------|-------------|---------------|
| **Batch** | `GoogleCloudBatchJobRunner` | Galaxy submits directly to GCP Batch API | NFS (shared filesystem) |
| **Pulsar** | `PulsarGcpBatchJobRunner` | AMQP message to Pulsar sidecar; Pulsar stages files, runs tool, returns results | HTTP upload/download to local SSD |
| **Single** | Local execution | Galaxy runs jobs locally on the host VM | Local filesystem |

All runners use Galaxy 26.1 on GCE VMs with RKE2 Kubernetes in us-east4. Batch and Pulsar provision per-job N2 VMs via the GCP Batch API. Single runs jobs directly on the Galaxy host VM.

## Experiments

### Variant Calling

12-step variant analysis pipeline (fastp, bwa_mem, picard, lofreq, snpEff, samtools, multiqc).

| | Batch | Pulsar | Single |
|---|---|---|---|
| Jobs | 26 ok | 36 ok | 36 ok |
| Wallclock cost | $9.16 | $21.18 | $15.33 |
| Compute cost | $1.94 | $3.44 | $3.40 |

[Performance Report](Pulsar-vs-Batch-Variant/index.html) | [Charts](Pulsar-vs-Batch-Variant/charts.html) | [Cost Analysis](Pulsar-vs-Batch-Variant/costs.html) | [Cost Charts](Pulsar-vs-Batch-Variant/cost-charts.html)

### RNASeq

12-step RNA-seq pipeline (cutadapt, rna_star, cufflinks, bamFilter, bedtools, multiqc, and parameter tools).

| | Batch | Pulsar | Single |
|---|---|---|---|
| Jobs | 46 ok | 20 ok | 60 ok |
| Wallclock cost | $5.61 | $2.53 | $6.94 |
| Compute cost | $2.41 | $0.82 | $3.28 |

[Performance Report](Pulsar-vs-Batch-RNASeq/index.html) | [Charts](Pulsar-vs-Batch-RNASeq/charts.html) | [Cost Analysis](Pulsar-vs-Batch-RNASeq/costs.html) | [Cost Charts](Pulsar-vs-Batch-RNASeq/cost-charts.html)

### ChIP-seq

7-step ChIP-seq pipeline (fastp, bowtie2, samtool_filter2, macs2_callpeak, wig_to_bigWig, multiqc, tp_grep_tool).

| | Batch | Pulsar | Single |
|---|---|---|---|
| Jobs | 21 ok | 21 ok | 21 ok |
| Wallclock cost | $6.15 | $8.77 | $5.55 |
| Compute cost | $2.01 | $2.02 | $2.02 |

[Performance Report](Pulsar-vs-Batch-ChiPSeq/index.html) | [Charts](Pulsar-vs-Batch-ChiPSeq/charts.html) | [Cost Analysis](Pulsar-vs-Batch-ChiPSeq/costs.html) | [Cost Charts](Pulsar-vs-Batch-ChiPSeq/cost-charts.html)

## Key Findings

1. **Compute costs are nearly identical across runners** — for ChIP-seq, all three runners cost within $0.01 of each other ($2.01-$2.02). The underlying computation is the same regardless of dispatch method.

2. **Wallclock overhead varies significantly** — Pulsar's AMQP staging and per-job SSD provisioning adds 30-130% overhead vs Batch. Single (local execution) avoids per-job VM provisioning entirely.

3. **Batch is cheapest for Variant Calling** ($9.16 wallclock) — NFS file sharing avoids per-job staging overhead.

4. **Pulsar is cheapest for RNASeq** ($2.53 wallclock) — but only has data at the 2GB size. Local SSD staging benefits I/O-bound tools.

5. **Single is cheapest for ChIP-seq** ($5.55 wallclock) — lightweight k8s/local tools run at zero additional cost on the Galaxy host.

Note: Jobs dispatched to the k8s runner or local runner (parameter tools, lightweight tools) are costed at $0 — their compute is covered by the Galaxy host VM.

## Infrastructure

- **Region:** us-east4
- **Galaxy version:** 26.1
- **Galaxy host:** e2-standard-4 (4 vCPU, 16 GB)
- **Job VMs:** N2 on-demand, right-sized per tool
- **Input data:** Paired-end reads at 2 GB, 5 GB, and 10 GB subsample sizes
