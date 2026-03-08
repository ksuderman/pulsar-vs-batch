# Pulsar vs Direct GCP Batch: Runtime Comparison

## Experiment Setup

- **Workflow:** Variant analysis on WGS PE data (12 steps)
- **Input data:** ERR3485802 paired-end reads + genome.genbank reference
- **Galaxy version:** 26.1
- **Infrastructure:** GCE VM running Galaxy on RKE2 Kubernetes, jobs dispatched to GCP Batch VMs (us-east4)
- **VM type:** n2-highcpu-16 (Batch), n2-standard-4 (Pulsar)
- **Custom VM image:** `galaxy-k8s-minimal-debian12-v2026-03-05` (CVMFS pre-installed)
- **Date:** 2026-03-07

### Runners Compared

| Runner | Type | Job Dispatch | File Transfer |
|--------|------|-------------|---------------|
| **GCP Batch** (direct) | `GoogleCloudBatchJobRunner` | Galaxy submits directly to GCP Batch API | Galaxy handles staging natively |
| **Pulsar** (AMQP sidecar) | `PulsarGcpBatchJobRunner` | Galaxy sends AMQP message; Pulsar sidecar on GCP Batch VM stages inputs, runs tool, collects outputs, sends AMQP callback | HTTP upload/download via `remote_transfer` |

Both workflows ran on the same Galaxy instance at the same time.

## Results Summary

| Metric | GCP Batch (direct) | Pulsar (AMQP) | Difference |
|--------|-------------------|---------------|------------|
| **Workflow wall clock** | **19.2 min** | **30.5 min** | **+11.3 min (+59%)** |
| Steps completed | 12/12 | 12/12 | -- |
| All jobs succeeded | Yes | Yes | -- |

## Per-Step Execution Time

Step execution time is measured as the elapsed time from the previous step's completion to this step's completion, capturing both scheduling overhead and actual compute time.

| # | Tool | Batch | Pulsar | Diff | Overhead |
|---|------|------:|-------:|-----:|---------:|
| 1 | fastp | 137s | 205s | +68s | +50% |
| 2 | snpEff_build_gb | 35s | 23s | -13s | -36% |
| 3 | bwa_mem | 109s | 185s | +76s | +70% |
| 4 | samtools_view | 116s | 195s | +79s | +68% |
| 5 | samtools_stats | 114s | 205s | +90s | +79% |
| 6 | picard_MarkDuplicates | 3s | 20s | +17s | +542% |
| 7 | lofreq_viterbi | 114s | 187s | +72s | +63% |
| 8 | multiqc | 28s | 12s | -16s | -56% |
| 9 | lofreq_indelqual | 94s | 187s | +93s | +99% |
| 10 | lofreq_call | 137s | 204s | +67s | +49% |
| 11 | lofreq_filter | 116s | 194s | +78s | +67% |
| 12 | snpEff | 148s | 216s | +68s | +46% |
| | **Total** | **19.2 min** | **30.5 min** | **+11.3 min** | **+59%** |

## Memory Usage

No memory metrics were reported for either runner. GCP Batch VMs do not expose container-level cgroup memory stats in the same way as Kubernetes pods.

## Analysis

### Per-Step Overhead

Pulsar adds a consistent **~57 seconds of overhead per step** (median across the 10 compute-bound steps). This overhead comes from the sidecar staging cycle on each GCP Batch job:

1. GCP Batch VM provisioning and container image pull
2. Sidecar startup and input staging via HTTP download from Galaxy
3. Tool execution (same as direct Batch)
4. Output collection and HTTP upload back to Galaxy
5. AMQP completion callback to Galaxy

For a 12-step sequential workflow, this per-step overhead accumulates to ~11 minutes of total overhead.

### Outliers

- **snpEff_build_gb** (-13s) and **multiqc** (-16s) were faster on Pulsar. These are short jobs where scheduling variance and VM provisioning luck dominate actual compute time.
- **picard_MarkDuplicates** (+542%) shows extreme relative overhead because the Batch step completed in just 3 seconds, making the fixed Pulsar overhead appear disproportionately large.

### Implications

- For **long-running, compute-heavy jobs** (hours), the ~1 minute per-step overhead is negligible.
- For **short multi-step workflows** like this variant analysis pipeline, Pulsar adds significant relative overhead (~59%).
- The overhead is primarily I/O-bound (HTTP file transfers), not compute-bound. Larger input/output files would increase the overhead further.
- Direct GCP Batch avoids sidecar overhead entirely but requires Galaxy to have direct GCP API access and is limited to simpler execution models.
