---
title: Pulsar vs Direct GCP Batch - Variant Analysis
---

# Pulsar vs Direct GCP Batch: Variant Analysis

**[Interactive Charts](charts.html)** | **[Cost Summary](costs.md)**

## Experiment Setup

- **Workflow:** Variant Analysis (12 unique tool types)
- **Galaxy version:** 26.1
- **Infrastructure:** GCE VM on RKE2 Kubernetes, jobs dispatched to GCP Batch VMs (us-east4)
- **Custom VM image:** `galaxy-k8s-minimal-debian12-v2026-03-05` (CVMFS pre-installed)
- **Batch server:** http://136.107.98.65
- **Pulsar server:** http://136.107.46.155
- **Date:** 2026-03-11 to 2026-03-12

### Runners Compared

| Runner | Type | Job Dispatch | File Transfer |
|--------|------|-------------|---------------|
| **GCP Batch** (direct) | `GoogleCloudBatchJobRunner` | Galaxy submits directly to GCP Batch API | Galaxy handles staging natively |
| **Pulsar** (AMQP sidecar) | `PulsarGcpBatchJobRunner` | Galaxy sends AMQP message; Pulsar sidecar stages inputs, runs tool, collects outputs, sends AMQP callback | HTTP upload/download via `remote_transfer` |

### Workflow Runs

8 workflow invocations, 98 total jobs (90 succeeded, 8 failed/errored).

### Failed/Errored Jobs

| Cloud | Tool | State | Count |
|-------|------|-------|-------|
| pulsar | lofreq_call | paused | 1 |
| pulsar | lofreq_filter | paused | 1 |
| pulsar | lofreq_indelqual | paused | 1 |
| pulsar | lofreq_viterbi | error | 1 |
| pulsar | multiqc | queued | 1 |
| pulsar | picard_MarkDuplicates | error | 2 |
| pulsar | snpEff | paused | 1 |

## Results Summary

### All Runs

| Runner | Run | Input Sizes | Wall Clock | Compute Time | Scheduling Overhead | Steps OK |
|--------|-----|-------------|-----------|-------------|-------------------|----------|
| batch | 1 | 10GB+2GB+5GB | 527.5 min | 504.3 min | 23.2 min (4%) | 12/12 |
| batch | 1 | 2GB | 205.7 min | 185.7 min | 20.1 min (10%) | 12/12 |
| batch | 1 | 2GB+5GB | 338.5 min | 320.4 min | 18.1 min (5%) | 12/12 |
| batch | 2 | 2GB | 207.6 min | 187.1 min | 20.4 min (10%) | 12/12 |
| batch | 2 | 2GB+5GB | 339.2 min | 320.3 min | 18.9 min (6%) | 12/12 |
| pulsar | 1 | 10GB+2GB+5GB | 622.6 min | 530.4 min | 92.2 min (15%) | 6/14 |
| pulsar | 1 | 2GB | 317.4 min | 238.5 min | 79.0 min (25%) | 12/12 |
| pulsar | 1 | 2GB+5GB | 587.4 min | 482.9 min | 104.5 min (18%) | 12/12 |

### Head-to-Head: 10GB+2GB+5GB

| Metric | GCP Batch | Pulsar | Difference |
|--------|-----------|--------|------------|
| **Wall clock** | **527.5 min** | **622.6 min** | **95.1 min (+18%)** |
| **Compute time** | **504.3 min** | **530.4 min** | **26.1 min (+5%)** |
| **Scheduling overhead** | **23.2 min** | **92.2 min** | **69.0 min (+298%)** |
| Steps completed | 12/12 | 6/14 | -- |

### Head-to-Head: 2GB

| Metric | GCP Batch (avg of 2 runs) | Pulsar | Difference |
|--------|---------------------------|--------|------------|
| **Wall clock** | **206.7 min** | **317.4 min** | **110.8 min (+54%)** |
| **Compute time** | **186.4 min** | **238.5 min** | **52.1 min (+28%)** |
| **Scheduling overhead** | **20.3 min** | **79.0 min** | **58.7 min (+289%)** |
| Steps completed | 12/12 | 12/12 | -- |

### Head-to-Head: 2GB+5GB

| Metric | GCP Batch (avg of 2 runs) | Pulsar | Difference |
|--------|---------------------------|--------|------------|
| **Wall clock** | **338.9 min** | **587.4 min** | **248.6 min (+73%)** |
| **Compute time** | **320.4 min** | **482.9 min** | **162.5 min (+51%)** |
| **Scheduling overhead** | **18.5 min** | **104.5 min** | **86.0 min (+465%)** |
| Steps completed | 12/12 | 12/12 | -- |

## Per-Step Compute Time (runtime_seconds)

### 10GB+2GB+5GB

| Tool | Batch | Pulsar | Diff | Diff% |
|------|-------|--------|------|-------|
| bwa_mem | 8761s | 28198s | +19437s | +222% |
| lofreq_call * | 14609s | 0s | -14609s | -100% |
| picard_MarkDuplicates | 2563s | 1392s | -1171s | -46% |
| snpEff_build_gb | 1146s | 171s | -975s | -85% |
| lofreq_viterbi * | 1183s | 0s | -1183s | -100% |
| fastp | 482s | 1396s | +914s | +190% |
| lofreq_indelqual * | 652s | 0s | -652s | -100% |
| samtools_view | 626s | 454s | -172s | -27% |
| samtools_stats | 219s | 213s | -6s | -3% |
| multiqc * | 9s | 0s | -9s | -100% |
| snpEff * | 7s | 0s | -7s | -100% |
| lofreq_filter * | 2s | 0s | -2s | -100% |
| **Total** | **30259s** | **31824s** | **+1565s** | **+5%** |

*Tools only on Batch: lofreq_call, lofreq_viterbi, lofreq_indelqual, multiqc, snpEff, lofreq_filter*

### 2GB

| Tool | Batch Avg | Pulsar Avg | Diff | Diff% |
|------|-----------|------------|------|-------|
| bwa_mem | 4597s | 8237s | +3640s | +79% |
| lofreq_call | 3954s | 4593s | +638s | +16% |
| picard_MarkDuplicates | 526s | 296s | -230s | -44% |
| snpEff_build_gb | 1126s | 177s | -949s | -84% |
| lofreq_viterbi | 364s | 365s | +2s | +0% |
| fastp | 165s | 332s | +167s | +101% |
| lofreq_indelqual | 242s | 157s | -86s | -35% |
| samtools_view | 140s | 98s | -42s | -30% |
| samtools_stats | 54s | 47s | -8s | -14% |
| multiqc | 9s | 2s | -7s | -78% |
| snpEff | 5s | 4s | -1s | -20% |
| lofreq_filter | 1s | 0s | -1s | -- |
| **Total** | **11184s** | **14308s** | **+3124s** | **+28%** |

### 2GB+5GB

| Tool | Batch Avg | Pulsar Avg | Diff | Diff% |
|------|-----------|------------|------|-------|
| bwa_mem | 6142s | 15661s | +9519s | +155% |
| lofreq_call | 8610s | 10158s | +1548s | +18% |
| picard_MarkDuplicates | 1290s | 709s | -582s | -45% |
| snpEff_build_gb | 1174s | 175s | -1000s | -85% |
| lofreq_viterbi | 724s | 788s | +64s | +9% |
| fastp | 401s | 829s | +428s | +107% |
| lofreq_indelqual | 421s | 303s | -118s | -28% |
| samtools_view | 332s | 235s | -97s | -29% |
| samtools_stats | 110s | 107s | -4s | -3% |
| multiqc | 9s | 3s | -6s | -67% |
| snpEff | 6s | 5s | -1s | -17% |
| lofreq_filter | 1s | 0s | -1s | -- |
| **Total** | **19221s** | **28973s** | **+9752s** | **+51%** |

## Resource Allocation: VM Sizing vs GALAXY_SLOTS

### VM Right-Sizing (Working)

Pulsar correctly right-sizes GCP Batch VMs based on per-tool resource requirements. The TPV destination passes `cores: "{cores}"` and `mem: "{mem}"` to Pulsar's `parse_gcp_job_params()`, which calls `compute_machine_type()` to select an appropriate N2 machine type.

### GALAXY_SLOTS Reporting Gap

Galaxy reports **slots=1** and **mem=0MB** for all Pulsar jobs because the Pulsar coexecution path doesn't feed these values back to Galaxy's metrics. The direct Batch runner explicitly sets `export GALAXY_SLOTS=${galaxy_slots}` in its `container_script.sh`. The Pulsar path relies on `CLUSTER_SLOTS_STATEMENT.sh`, which falls through to `GALAXY_SLOTS="1"` on GCP Batch VMs (no SLURM/PBS/SGE env vars). Actual thread usage depends on how each tool discovers available CPUs.

### Batch Resource Allocation (as reported by Galaxy)

| Tool | CPU Slots |
|------|-----------|
| bwa_mem | 8 |
| lofreq_call | 2 |
| picard_MarkDuplicates | 3 |
| snpEff_build_gb | 1 |
| lofreq_viterbi | 4 |
| fastp | 4 |
| lofreq_indelqual | 1 |
| samtools_view | 1 |
| samtools_stats | 2 |
| multiqc | 1 |
| snpEff | 1 |
| lofreq_filter | 1 |

### Runtime Ratio Analysis (10GB+2GB+5GB)

| Tool | Batch Slots | Pulsar/Batch Ratio | Expected if 1 Thread |
|------|------------|-------------------|---------------------|
| bwa_mem | 8 | 3.22x | ~8x |
| picard_MarkDuplicates | 3 | 0.54x | ~3x |
| snpEff_build_gb | 1 | 0.15x | ~1x |
| fastp | 4 | 2.90x | ~4x |
| samtools_view | 1 | 0.73x | ~1x |
| samtools_stats | 2 | 0.97x | ~2x |

## Wall Clock vs Compute Time Analysis

| Runner | Input | Wall Clock | Compute | Overhead | Overhead % |
|--------|-------|-----------|---------|----------|------------|
| batch R1 | 10GB+2GB+5GB | 527.5m | 504.3m | 23.2m | 4% |
| batch R1 | 2GB | 205.7m | 185.7m | 20.1m | 10% |
| batch R2 | 2GB | 207.6m | 187.1m | 20.4m | 10% |
| batch R1 | 2GB+5GB | 338.5m | 320.4m | 18.1m | 5% |
| batch R2 | 2GB+5GB | 339.2m | 320.3m | 18.9m | 6% |
| pulsar R1 | 10GB+2GB+5GB | 622.6m | 530.4m | 92.2m | 15% |
| pulsar R1 | 2GB | 317.4m | 238.5m | 79.0m | 25% |
| pulsar R1 | 2GB+5GB | 587.4m | 482.9m | 104.5m | 18% |

## Batch Scaling Analysis

| Input | Wall Clock | Compute |
|-------|-----------|---------|
| 10GB+2GB+5GB | 527.5m | 504.3m |
| 2GB (avg of 2) | 206.7m | 186.4m |
| 2GB+5GB (avg of 2) | 338.9m | 320.4m |

## Key Findings

### 1. 10GB+2GB+5GB: Pulsar is +18% slower (wall clock)

- Wall clock: 622.6m vs 527.5m
- Compute: 530.4m vs 504.3m (+5%)

### 2. 2GB: Pulsar is +54% slower (wall clock)

- Wall clock: 317.4m vs 206.7m
- Compute: 238.5m vs 186.4m (+28%)

### 3. 2GB+5GB: Pulsar is +73% slower (wall clock)

- Wall clock: 587.4m vs 338.9m
- Compute: 482.9m vs 320.4m (+51%)

### 4. Several tools are faster on Pulsar

- **picard_MarkDuplicates** (10GB+2GB+5GB): -46% (1392s vs 2563s)
- **snpEff_build_gb** (10GB+2GB+5GB): -85% (171s vs 1146s)
- **samtools_view** (10GB+2GB+5GB): -27% (454s vs 626s)

### 5. Scheduling overhead is Pulsar's major cost

- Batch: 1.7 min/step avg
- Pulsar: 7.3 min/step avg

### 6. Batch is highly reproducible

- 2GB: 2 runs, compute range 185.7m - 187.1m (0.8% spread)
- 2GB+5GB: 2 runs, compute range 320.3m - 320.4m (0.0% spread)

## Implications

- **Pulsar's staging overhead is inherent** to the AMQP sidecar architecture. Dominates for short multi-step workflows, negligible for long-running single-step jobs.
- **Pulsar's I/O model has advantages.** Local SSD staging benefits I/O-bound tools.
