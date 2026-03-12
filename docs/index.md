---
title: Pulsar vs Direct GCP Batch
---

# Pulsar vs Direct GCP Batch: Full Runtime Comparison

**[Interactive Charts](charts.html)**

## Experiment Setup

- **Workflow:** Variant analysis on WGS PE data (12 steps)
- **Input data:** ERR3485802 paired-end reads + genome.genbank reference, scaled across 2GB, 5GB, and 10GB input sizes
- **Galaxy version:** 26.1
- **Infrastructure:** GCE VM running Galaxy on RKE2 Kubernetes, jobs dispatched to GCP Batch VMs (us-east4)
- **Custom VM image:** `galaxy-k8s-minimal-debian12-v2026-03-05` (CVMFS pre-installed)
- **Batch server:** http://136.107.98.65
- **Pulsar server:** http://136.107.46.155
- **Date:** 2026-03-11 to 2026-03-12

### Runners Compared

| Runner | Type | Job Dispatch | File Transfer |
|--------|------|-------------|---------------|
| **GCP Batch** (direct) | `GoogleCloudBatchJobRunner` | Galaxy submits directly to GCP Batch API | Galaxy handles staging natively |
| **Pulsar** (AMQP sidecar) | `PulsarGcpBatchJobRunner` | Galaxy sends AMQP message; Pulsar sidecar on GCP Batch VM stages inputs, runs tool, collects outputs, sends AMQP callback | HTTP upload/download via `remote_transfer` |

### Workflow Runs

Six total invocations of the 12-step variant analysis workflow were executed. All 72 jobs (12 steps x 6 runs) completed successfully (state: ok).

## Results Summary

### All Runs

| Runner | Input Sizes | History | Wall Clock | Compute Time | Scheduling Overhead |
|--------|-------------|---------|-----------|-------------|-------------------|
| batch | 2GB | e3e0a8eb | 205.7 min | 185.7 min | 20.1 min (10%) |
| batch | 2GB | b1fb70a7 | 207.6 min | 187.1 min | 20.4 min (10%) |
| batch | 2GB+5GB | 312e47e2 | 338.5 min | 320.4 min | 18.1 min (5%) |
| batch | 2GB+5GB+10GB | 60739207 | 527.5 min | 504.3 min | 23.2 min (4%) |
| pulsar | 2GB | 958238f0 | 317.4 min | 238.5 min | 79.0 min (25%) |
| pulsar | 2GB+5GB | 39b19959 | 587.4 min | 482.9 min | 104.5 min (18%) |

### Head-to-Head: 2GB Runs

| Metric | GCP Batch (avg of 2 runs) | Pulsar | Difference |
|--------|--------------------------|--------|------------|
| **Wall clock** | **206.7 min** | **317.4 min** | **+110.7 min (+54%)** |
| **Compute time** | **186.4 min** | **238.5 min** | **+52.1 min (+28%)** |
| **Scheduling overhead** | **20.3 min** | **79.0 min** | **+58.7 min (+290%)** |
| Steps completed | 12/12 | 12/12 | -- |
| All jobs succeeded | Yes | Yes | -- |

### Head-to-Head: 2GB+5GB Runs

| Metric | GCP Batch | Pulsar | Difference |
|--------|----------|--------|------------|
| **Wall clock** | **338.5 min** | **587.4 min** | **+248.9 min (+74%)** |
| **Compute time** | **320.4 min** | **482.9 min** | **+162.5 min (+51%)** |
| **Scheduling overhead** | **18.1 min** | **104.5 min** | **+86.4 min (+477%)** |
| Steps completed | 12/12 | 12/12 | -- |
| All jobs succeeded | Yes | Yes | -- |

## Per-Step Compute Time (runtime_seconds)

### 2GB Runs

| Tool | Batch R1 | Batch R2 | Batch Avg | Pulsar | Diff | Diff% |
|------|----------|----------|-----------|--------|------|-------|
| fastp | 170s | 160s | 165s | 332s | +167s | +101% |
| snpEff_build_gb | 1141s | 1111s | 1126s | 177s | -949s | -84% |
| bwa_mem | 4515s | 4679s | 4597s | 8237s | +3640s | +79% |
| samtools_view | 139s | 140s | 140s | 98s | -42s | -30% |
| picard_MarkDuplicates | 526s | 526s | 526s | 296s | -230s | -44% |
| samtools_stats | 55s | 54s | 55s | 47s | -8s | -15% |
| lofreq_viterbi | 364s | 363s | 364s | 365s | +1s | +0% |
| multiqc | 8s | 10s | 9s | 2s | -7s | -78% |
| lofreq_indelqual | 250s | 235s | 243s | 157s | -86s | -35% |
| lofreq_call | 3965s | 3944s | 3955s | 4593s | +638s | +16% |
| lofreq_filter | 1s | 1s | 1s | 0s | -1s | -- |
| snpEff | 5s | 5s | 5s | 4s | -1s | -- |
| **Total** | **11139s** | **11228s** | **11184s** | **14308s** | **+3124s** | **+28%** |

### 2GB+5GB Runs

| Tool | Batch | Pulsar | Diff | Diff% |
|------|-------|--------|------|-------|
| fastp | 399s | 829s | +430s | +108% |
| snpEff_build_gb | 1263s | 175s | -1088s | -86% |
| bwa_mem | 6141s | 15661s | +9520s | +155% |
| samtools_view | 339s | 235s | -104s | -31% |
| picard_MarkDuplicates | 1274s | 709s | -565s | -44% |
| samtools_stats | 110s | 107s | -3s | -3% |
| lofreq_viterbi | 724s | 788s | +64s | +9% |
| multiqc | 9s | 3s | -6s | -67% |
| lofreq_indelqual | 415s | 303s | -112s | -27% |
| lofreq_call | 8541s | 10158s | +1617s | +19% |
| lofreq_filter | 1s | 0s | -1s | -- |
| snpEff | 6s | 5s | -1s | -- |
| **Total** | **19222s** | **28973s** | **+9751s** | **+51%** |

## Resource Allocation: VM Sizing vs GALAXY_SLOTS

### VM Right-Sizing (Working)

Pulsar correctly right-sizes GCP Batch VMs based on per-tool resource requirements. The TPV destination passes `cores: "{cores}"` and `mem: "{mem}"` to Pulsar's `parse_gcp_job_params()`, which calls `compute_machine_type()` to select an appropriate N2 machine type (highcpu, standard, or highmem) based on the CPU-to-memory ratio. This fix (commit `b194758` in pulsar@gcp-fixes) ensures the VM has the correct number of vCPUs and memory available.

### GALAXY_SLOTS Reporting Gap

Galaxy's job metrics report **slots=1** and **mem=0MB** for all Pulsar jobs because the Pulsar coexecution path doesn't feed these values back to Galaxy's metric collection. The direct Batch runner explicitly sets `export GALAXY_SLOTS=${galaxy_slots}` in its `container_script.sh` and records these in job metrics. The Pulsar path instead relies on the job script's `CLUSTER_SLOTS_STATEMENT.sh`, which auto-detects available CPUs through a fallback chain (SLURM &rarr; PBS &rarr; SGE &rarr; `$GALAXY_SLOTS` env &rarr; `nproc` &rarr; `1`).

On GCP Batch VMs, none of the HPC scheduler environment variables are present, so the detection reaches `nproc` or falls to the default of `1` depending on the tool wrapper. This explains why Galaxy reports slots=1, but the **actual thread usage depends on how each tool discovers available CPUs**.

### Batch Resource Allocation (as reported by Galaxy)

| Tool | CPU Slots | Memory |
|------|-----------|--------|
| fastp | 4 | ~7.6 GB |
| bwa_mem | 8 | ~58 GB |
| picard_MarkDuplicates | 3 | ~15 GB |
| samtools_stats | 2 | ~7.6 GB |
| lofreq_viterbi | 4 | ~16 GB |
| lofreq_call | 2 | ~8 GB |
| Other tools | 1 | ~3.8-12 GB |

### Runtime Ratio Analysis

If Pulsar tools were truly limited to 1 thread, we'd expect the Pulsar/Batch runtime ratio to roughly match the Batch slot count. The actual ratios tell a more nuanced story:

| Tool | Batch Slots | Pulsar/Batch Ratio | Expected if 1 Thread |
|------|------------|-------------------|---------------------|
| fastp | 4 | 2.01x | ~4x |
| bwa_mem | 8 | 1.79x | ~8x |
| lofreq_viterbi | 4 | 1.00x | ~4x |
| lofreq_call | 2 | 1.16x | ~2x |
| samtools_stats | 2 | 0.86x | ~2x |
| picard_MarkDuplicates | 3 | 0.56x | ~3x |
| snpEff_build_gb | 1 | 0.16x | ~1x |

The ratios are consistently lower than the "1 thread" prediction. Tools like lofreq_viterbi (4 batch slots, 1.00x ratio) and picard_MarkDuplicates (3 batch slots, 0.56x ratio &mdash; Pulsar is *faster*) confirm that the VM is properly sized and tools are discovering available cores, at least partially. The slowdowns on bwa_mem and fastp likely come from a combination of `GALAXY_SLOTS` fallback behavior in the Galaxy tool wrappers and the additional I/O overhead of HTTP-based staging.

## Wall Clock vs Compute Time Analysis

### Scheduling Overhead by Runner

The difference between wall clock time and compute time represents scheduling overhead: VM provisioning, container startup, input staging, output collection, and AMQP messaging.

| Runner | Input | Wall Clock | Compute | Overhead | Overhead % |
|--------|-------|-----------|---------|----------|------------|
| batch R1 | 2GB | 205.7m | 185.7m | 20.1m | 10% |
| batch R2 | 2GB | 207.6m | 187.1m | 20.4m | 10% |
| batch | 2GB+5GB | 338.5m | 320.4m | 18.1m | 5% |
| batch | 2GB+5GB+10GB | 527.5m | 504.3m | 23.2m | 4% |
| pulsar | 2GB | 317.4m | 238.5m | 79.0m | 25% |
| pulsar | 2GB+5GB | 587.4m | 482.9m | 104.5m | 18% |

**Key observations:**

- Batch scheduling overhead is remarkably consistent at 18-23 minutes regardless of data size (~1.5-1.9 min per step)
- Pulsar scheduling overhead is 4-5x higher: 79-105 minutes (~6.6-8.7 min per step)
- As data size grows, scheduling overhead becomes a smaller percentage of total time for both runners
- Pulsar's per-step overhead increases with data size (from ~6.6 min to ~8.7 min per step), consistent with larger file transfers

## Batch Scaling Analysis

Batch-only runs across three input sizes show how the workflow scales with data:

| Input | Wall Clock | Compute | Per-2GB Compute |
|-------|-----------|---------|-----------------|
| 2GB (avg) | 206.7m | 186.4m | 186.4m |
| 2GB+5GB | 338.5m | 320.4m | -- |
| 2GB+5GB+10GB | 527.5m | 504.3m | -- |

The scaling is roughly linear:

- 2GB to 2GB+5GB: compute grows from 186m to 320m (1.72x for ~3.5x data)
- 2GB to 2GB+5GB+10GB: compute grows from 186m to 504m (2.70x for ~8.5x data)

This sub-linear scaling suggests that some steps (e.g., snpEff_build_gb, multiqc, snpEff) have fixed costs that don't scale with input size.

## Key Findings

### 1. Pulsar is significantly slower overall

- **2GB:** 54% slower wall clock (317m vs 207m), 28% slower compute (239m vs 186m)
- **2GB+5GB:** 74% slower wall clock (587m vs 339m), 51% slower compute (483m vs 320m)

### 2. Compute differences are mixed &mdash; not a simple threading story

Pulsar VMs are correctly right-sized via `compute_machine_type()`. Galaxy reports `slots=1` for Pulsar jobs because the Pulsar coexecution path doesn't propagate `GALAXY_SLOTS` back to Galaxy's metric system, but the actual CPU availability on the VM is correct. Multi-threaded tools show slowdowns that are smaller than a pure "1 thread vs N" model would predict, suggesting tools partially discover available cores via `nproc`:

- **bwa_mem**: +79% (2GB), +155% (2GB+5GB) &mdash; slower, but far less than the 8x expected from 1 vs 8 threads. Likely affected by the `GALAXY_SLOTS` fallback in the bwa Galaxy wrapper plus HTTP staging overhead.
- **fastp**: +101% (2GB), +108% (2GB+5GB) &mdash; ~2x slower vs the 4x expected.

Tools that check `$GALAXY_SLOTS` for their `-t`/`--threads` parameter would default to 1 thread even on a right-sized VM. The fix would be to inject `GALAXY_SLOTS` into the Pulsar task environment (similar to what the direct Batch runner does in `container_script.sh`).

### 3. Several tools are significantly faster on Pulsar

- **snpEff_build_gb:** 84-86% faster on Pulsar (177s vs 1126s for 2GB). This is the most dramatic difference and likely reflects the different VM image (`galaxy-k8s-minimal-debian12-v2026-03-05` for Pulsar vs `galaxy-k8s-boot-debian12-v2026-02-24` for Batch), different disk I/O characteristics (local SSD staging vs NFS), or different CVMFS cache warmth.
- **picard_MarkDuplicates:** 44% faster on Pulsar (0.56x ratio vs 3 batch slots). The Pulsar VM likely has favorable memory characteristics for this Java-based tool.
- **samtools_view:** 30-31% faster on Pulsar. Local SSD I/O may outperform NFS for BAM filtering.
- **lofreq_indelqual:** 35% faster on Pulsar.

### 4. Scheduling overhead is Pulsar's other major cost

Beyond compute, Pulsar adds 60-85 minutes of scheduling/staging overhead compared to Batch. This overhead comes from the AMQP sidecar architecture: input download, output upload, and message passing for each step.

### 5. Batch is highly reproducible

The two Batch 2GB runs produced nearly identical results: 185.7m vs 187.1m compute time (<1% variance). This validates the benchmark methodology.

### 6. Batch scales sub-linearly

The 2GB+5GB+10GB run (504m compute for ~8.5x the data of the 2GB run) shows 2.7x scaling, indicating efficient handling of larger datasets with fixed per-step costs amortized.

## Implications

- **Inject `GALAXY_SLOTS` into Pulsar task environment.** The Pulsar coexecution path should set `GALAXY_SLOTS` based on the `cores` parameter (similar to how `container_script.sh` does `export GALAXY_SLOTS=${galaxy_slots}` for direct Batch). This would ensure Galaxy tool wrappers that read `$GALAXY_SLOTS` for thread count use the full available cores on the right-sized VM.
- **Pulsar's staging overhead is inherent** to the AMQP sidecar architecture. At ~6.6-8.7 min per step, this HTTP staging + AMQP callback cost dominates for short multi-step workflows but becomes negligible for long-running single-step jobs.
- **Batch is faster overall** for this workflow type, but the gap is narrower than the raw numbers suggest: several tools are genuinely faster on Pulsar, and the `GALAXY_SLOTS` fix would likely close the remaining compute gap.
- **Pulsar's I/O model has advantages.** The local SSD staging on Pulsar appears to benefit I/O-bound tools (samtools_view, picard, lofreq_indelqual). The snpEff_build_gb speedup (6x) warrants investigation &mdash; it may reflect CVMFS cache locality, faster local disk I/O, or differences between the two custom VM images.
