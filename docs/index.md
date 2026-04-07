---
title: Galaxy GCP Batch Benchmarks
---

# Galaxy GCP Batch Benchmarks

Benchmarking strategies for dispatching Galaxy jobs to Google Cloud Platform.

**[Summary Charts](summary-chart.html)**

## Runners Compared

| Runner | Description | File Transfer |
|--------|-------------|---------------|
| **Direct** | Galaxy submits directly to GCP Batch API | NFS (shared filesystem) |
| **Pulsar** | AMQP to Pulsar sidecar on GCP Batch VM | HTTP upload/download to local SSD |
| **Direct+K8s** | GCP Batch for heavy tools, k8s for lightweight | NFS + local k8s |
| **Pulsar+K8s** | *(extrapolated)* Pulsar with lightweight tools on k8s | HTTP + local k8s |
| **K8s-Only** | All jobs run on the GKE Kubernetes cluster (no GCP Batch) | Local k8s |

All GCP Batch runners use Galaxy 26.1 on GCE (e2-standard-4) with RKE2 Kubernetes in us-east4. Direct and Pulsar provision per-job N2 VMs. Direct+K8s and Pulsar+K8s route lightweight single-core tools to the local k8s runner at zero additional cost. K8s-Only runs everything on a single n2-standard-16 GKE Standard node.

## Experiments

### Variant Calling

12-step pipeline: fastp, bwa_mem, picard, lofreq, snpEff, samtools, multiqc. 36 jobs per runner (3 sizes x 12 tools).

| | Direct | Pulsar | Pulsar+K8s | Direct+K8s | K8s-Only |
|---|---|---|---|---|---|
| Wallclock cost | $16.97 | $21.59 | $18.40 | **$15.33** | $15.00 |
| Compute cost | $3.58 | $3.50 | $3.18 | $3.40 | -- |

[Performance](Pulsar-vs-Batch-Variant/index.html) | [Charts](Pulsar-vs-Batch-Variant/charts.html) | [Costs](Pulsar-vs-Batch-Variant/costs.html) | [Cost Charts](Pulsar-vs-Batch-Variant/cost-charts.html)

### RNASeq

12-step pipeline: cutadapt, rna_star, cufflinks, bamFilter, bedtools, multiqc, and parameter tools. 60 jobs per runner (3 sizes x 20 steps).

| | Direct | Pulsar | Pulsar+K8s | Direct+K8s | K8s-Only |
|---|---|---|---|---|---|
| Wallclock cost | $9.48 | $11.03 | $7.63 | **$6.94** | $7.39 |
| Compute cost | $3.99 | $3.09 | $2.82 | $3.28 | -- |

[Performance](Pulsar-vs-Batch-RNASeq/index.html) | [Charts](Pulsar-vs-Batch-RNASeq/charts.html) | [Costs](Pulsar-vs-Batch-RNASeq/costs.html) | [Cost Charts](Pulsar-vs-Batch-RNASeq/cost-charts.html)

### ChIP-seq

7-step pipeline: fastp, bowtie2, samtool_filter2, macs2_callpeak, wig_to_bigWig, multiqc, tp_grep_tool. 21 jobs per runner (3 sizes x 7 tools).

| | Direct | Pulsar | Pulsar+K8s | Direct+K8s | K8s-Only |
|---|---|---|---|---|---|
| Wallclock cost | $6.15 | $8.77 | $6.96 | **$5.55** | $5.73 |
| Compute cost | $2.01 | $2.02 | $1.91 | $2.02 | -- |

[Performance](Pulsar-vs-Batch-ChiPSeq/index.html) | [Charts](Pulsar-vs-Batch-ChiPSeq/charts.html) | [Costs](Pulsar-vs-Batch-ChiPSeq/costs.html) | [Cost Charts](Pulsar-vs-Batch-ChiPSeq/cost-charts.html)

## K8s-Only Deployment Estimate

What if Galaxy ran all jobs on a GKE Standard Kubernetes cluster without GCP Batch? The cluster node must be large enough for the most resource-intensive tool (rna_star: 10 cores, 50 GB) plus ~4 cores and ~8 GB for Galaxy/Kubernetes overhead. All three workflows fit on an **n2-standard-16** (16 vCPU, 64 GB) at **$0.88/hour** (including GKE $0.10/hour management fee).

Jobs run sequentially (one at a time). Duration is estimated as the greater of the sum of cgroups compute times (for workflows that run tools concurrently) or the observed wallclock time.

| Workflow | 2GB | 5GB | 10GB | Total |
|---|---|---|---|---|
| Variant Calling | $2.84 (3.2h) | $4.73 (5.4h) | $7.43 (8.5h) | **$15.00** |
| RNASeq | $1.65 (1.9h)* | $2.79 (3.2h)* | $2.96 (3.4h) | **$7.39** |
| ChIP-seq | $0.82 (0.9h) | $1.75 (2.0h) | $3.16 (3.6h) | **$5.73** |

\* RNASeq at 2GB and 5GB run tools concurrently; sequential k8s execution takes longer than the observed wallclock.

### Total Cost Comparison

| Runner | Variant | RNASeq | ChIP-seq | **Total** |
|---|---|---|---|---|
| **Direct+K8s** | $15.33 | $6.94 | $5.55 | **$27.82** |
| **K8s-Only** (GKE Standard) | $15.00 | $7.39 | $5.73 | $28.11 |
| **Direct** | $16.97 | $9.48 | $6.15 | $32.60 |
| **Pulsar+K8s** | $18.40 | $7.63 | $6.96 | $32.99 |
| **Pulsar** | $21.59 | $11.03 | $8.77 | $41.39 |

Direct+K8s and K8s-Only are nearly identical at **$27.82** and **$28.11** respectively — within 1% of each other. Both are significantly cheaper than plain Direct ($32.60) or Pulsar ($41.39). The trade-off: K8s-Only avoids per-job VM provisioning but the n2-standard-16 sits partially idle and jobs cannot run concurrently.

## Key Findings

1. **Direct+K8s and K8s-Only are the cheapest deployments** at $27.82 and $28.11 respectively. With GKE Standard management fees, the two approaches are essentially equivalent in cost despite very different architectures.

2. **Routing lightweight tools to k8s significantly reduces GCP Batch costs.** Pulsar+K8s saves 15-31% over plain Pulsar by avoiding GCP Batch VM provisioning for single-core tools (tp_awk_tool, tp_grep_tool, samtools_view, bedtools_genomecoveragebed, revertR2orientationInBam).

3. **Direct+K8s is the cheapest GCP Batch strategy** ($27.82) — combining GCP Batch for heavy tools with zero-cost k8s for lightweight tools.

4. **Compute costs are nearly identical across all runners** — the underlying computation is the same regardless of dispatch method. The cost differences are entirely in scheduling and staging overhead.

5. **Plain Pulsar is the most expensive runner** ($41.39) due to per-job local SSD provisioning and AMQP staging overhead for every tool, including lightweight ones.

6. **GCP Batch excels for concurrent execution.** Workflows like RNASeq that dispatch tools in parallel benefit from on-demand per-job VMs. K8s-Only loses this advantage since the single cluster node runs jobs sequentially.

## Infrastructure

- **Region:** us-east4
- **Galaxy version:** 26.1
- **Galaxy host:** e2-standard-4 (4 vCPU, 16 GB)
- **Job VMs:** N2 on-demand, right-sized per tool
- **Input data:** Paired-end reads at 2 GB, 5 GB, and 10 GB subsample sizes
- **K8s zero-cost tools:** bedtools_genomecoveragebed, revertR2orientationInBam, samtools_view, tp_awk_tool, tp_grep_tool, compose_text_param, map_param_value, param_value_from_file
