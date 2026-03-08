# Pulsar vs Direct GCP Batch: Galaxy Job Runner Comparison

Benchmarking framework for comparing two Galaxy job runner strategies on Google Cloud Platform:

- **Direct GCP Batch** (`GoogleCloudBatchJobRunner`) -- Galaxy submits jobs directly to the GCP Batch API and handles file staging natively.
- **Pulsar GCP Batch** (`PulsarGcpBatchJobRunner`) -- Galaxy sends AMQP messages to a Pulsar sidecar container running on the GCP Batch VM, which stages inputs via HTTP, runs the tool, collects outputs, and sends a completion callback.

## Prerequisites

- [gxabm](https://pypi.org/project/gxabm/) (`abm` CLI)
- [Google Cloud SDK](https://cloud.google.com/sdk) (`gcloud`)
- `kubectl` configured for your Galaxy Kubernetes clusters
- Two Galaxy instances deployed on GCE VMs with RKE2 Kubernetes (one per runner type)

## Quick Start

### 1. Launch Galaxy instances

```bash
bin/batch.sh start    # Direct GCP Batch runner
bin/pulsar.sh start   # Pulsar GCP Batch runner
```

### 2. Download kubeconfig files

```bash
bin/batch.sh kube
bin/pulsar.sh kube
```

### 3. Bootstrap instances

Detects instance IPs, configures API endpoints, and retrieves user API keys:

```bash
bin/bootstrap.sh batch pulsar
```

### 4. Upload data and workflows

```bash
bin/upload.sh batch pulsar
```

### 5. Run an experiment

Validate that all inputs and workflows are available, then run:

```bash
# Quick test (1 run, small variant-calling workflow)
abm experiment validate experiments/test.yml
abm experiment run experiments/test.yml

# Full benchmark (3 runs, three workflows at multiple data sizes)
abm experiment validate experiments/benchmark.yml
abm experiment run experiments/benchmark.yml
```

Metrics are saved to `metrics/<experiment-name>/`.

### 6. Tear down

```bash
bin/batch.sh stop
bin/pulsar.sh stop
```

## Repository Structure

```
.abm/                   # abm CLI configuration
  profile.yml           #   Galaxy server profiles (url, api key, kubeconfig)
  datasets.yml          #   Named dataset download URLs
  histories.yml         #   Named history import URLs
  workflows.yml         #   Named workflow import URLs
benchmarks/             # Benchmark configurations (workflow + inputs)
  variant-test.yml      #   Small variant-calling test (~2GB)
  variant.yml           #   Variant-calling at 2GB, 5GB, 10GB
  rnaseq.yml            #   RNA-seq PE at 2GB, 5GB, 10GB
  chipseq-pe.yml        #   ChIP-seq PE (mm10)
experiments/            # Experiment definitions
  test.yml              #   Quick test: 1 run of variant-test on both runners
  benchmark.yml         #   Full: 3 runs of all benchmarks on both runners
results/                # Analysis output
  results.md            #   Markdown summary of test experiment results
  charts.html           #   Interactive Chart.js visualizations
bin/                    # Scripts
  batch.sh              #   Launch/stop the direct Batch Galaxy instance
  pulsar.sh             #   Launch/stop the Pulsar Galaxy instance
  bootstrap.sh          #   Configure API keys for both instances
  upload.sh             #   Upload datasets, histories, and workflows
  launch_vm.sh          #   GCE VM provisioning (used by batch.sh/pulsar.sh)
  kube.sh               #   Download and configure kubeconfig from a VM
  test.sh               #   Run or validate the variant-test benchmark
  tail.sh               #   Tail cloud-init logs on a running VM
```

## Benchmark Workflows

| Workflow | Steps | Input Sizes | Reference |
|----------|------:|-------------|-----------|
| Variant analysis on WGS PE data | 12 | 2GB, 5GB, 10GB | GRCh38 (GenBank) |
| RNA-seq PE | 15 | 2GB, 5GB, 10GB | hg38 (UCSC) |
| ChIP-seq PE | 12 | ~1GB | mm10 |

## Initial Results (variant-test, 1 run)

| Metric | GCP Batch (direct) | Pulsar (AMQP) | Difference |
|--------|-------------------:|---------------:|-----------:|
| Workflow wall clock | 19.2 min | 30.5 min | +11.3 min (+59%) |
| Median per-step overhead | -- | -- | ~57s |
| Steps completed | 12/12 | 12/12 | -- |

The Pulsar sidecar adds roughly 1 minute of overhead per workflow step due to HTTP file staging and AMQP messaging. This overhead is fixed per step, so it is proportionally more significant for short-running tools and negligible for compute-heavy jobs.

See [results/results.md](results/results.md) for the full breakdown and [results/charts.html](results/charts.html) for interactive visualizations.

## Configuration

Galaxy server profiles are defined in `.abm/profile.yml`:

```yaml
batch:
  url: http://<batch-instance-ip>
  key: <api-key>
  kube: ~/.kube/configs/batch
pulsar:
  url: http://<pulsar-instance-ip>
  key: <api-key>
  kube: ~/.kube/configs/pulsar
```

These are auto-configured by `bin/bootstrap.sh`.

## Infrastructure

Both Galaxy instances run on GCE VMs in `us-east4-c` with RKE2 Kubernetes. Jobs are dispatched to separate GCP Batch VMs using a custom boot image (`galaxy-k8s-minimal-debian12-v2026-03-05`) with CVMFS pre-installed for access to Galaxy reference data.

The Pulsar runner uses a custom sidecar image (`ksuderman/pulsar-pod-staging:0.15.15.dev0`) built from the [ksuderman/pulsar@gcp-fixes](https://github.com/ksuderman/pulsar/tree/gcp-fixes) branch, which contains fixes for container ordering, output collection, and AMQP messaging on GCP Batch.
