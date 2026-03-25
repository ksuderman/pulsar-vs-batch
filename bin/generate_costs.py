#!/usr/bin/env python3
"""Generate docs/costs.md and docs/cost-charts.html from metrics JSON files.

Usage:
    python3 bin/generate_costs.py [metrics_dir]

Reads all JSON files from metrics/<experiment>/ (default: metrics/Pulsar-vs-Batch/)
and produces:
    docs/costs.md          - Markdown cost report
    docs/cost-charts.html  - Interactive Chart.js cost dashboard

Queries the Rainstone API (https://rainstone.anvilproject.org/api/tools/{toolId})
for historical per-tool cost estimates from usegalaxy.org production workloads.
"""

import argparse
import json
import glob
import os
import re
import sys
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# GCP N2 on-demand pricing (us-east4)
# ---------------------------------------------------------------------------

VCPU_PER_HOUR = 0.031611       # $/vCPU/hour
MEM_PER_GB_HOUR = 0.004237     # $/GB/hour
SSD_PER_GB_HOUR = 0.000054     # $/GB/hour (local SSD)
BOOT_DISK_PER_GB_MONTH = 0.10  # $/GB/month (pd-balanced)

PULSAR_SSD_GB = 375   # Local SSD per Pulsar job
BOOT_DISK_GB = 30     # Boot disk per job

# Galaxy host VM: e2-standard-4 (4 vCPU, 16 GB)
E2_VCPU_PER_HOUR = 0.02238
E2_MEM_PER_GB_HOUR = 0.003000
GALAXY_VM_VCPUS = 4
GALAXY_VM_MEM_GB = 16
GALAXY_VM_HOURLY = GALAXY_VM_VCPUS * E2_VCPU_PER_HOUR + GALAXY_VM_MEM_GB * E2_MEM_PER_GB_HOUR

# Traditional single-VM model: n2-standard-20 (20 vCPU, 80 GB)
LOCAL_VM_VCPUS = 20
LOCAL_VM_MEM_GB = 80
LOCAL_VM_HOURLY = LOCAL_VM_VCPUS * VCPU_PER_HOUR + LOCAL_VM_MEM_GB * MEM_PER_GB_HOUR

# N2 standard machine types: vCPU -> memory GB
N2_STANDARD = {2: 8, 4: 16, 8: 32, 16: 64, 32: 128, 48: 192, 64: 256, 80: 320, 96: 384, 128: 512}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_metrics(metrics_dir):
    files = sorted(glob.glob(os.path.join(metrics_dir, "*.json")))
    if not files:
        print(f"No JSON files found in {metrics_dir}", file=sys.stderr)
        sys.exit(1)

    jobs = []
    for f in files:
        with open(f) as fh:
            d = json.load(fh)
        tool = d["metrics"]["tool_id"].split("/")[-2] if "/" in d["metrics"]["tool_id"] else d["metrics"]["tool_id"]
        runtime = slots = mem = None
        for m in d["metrics"].get("job_metrics", []):
            if m["name"] == "runtime_seconds":
                runtime = float(m["raw_value"])
            if m["name"] == "galaxy_slots":
                slots = float(m["raw_value"])
            if m["name"] == "galaxy_memory_mb":
                mem = float(m["raw_value"])
        # Wallclock = Galaxy job lifetime (create to update), which includes
        # VM provisioning, image pull, staging, compute, and result collection.
        # This is what users actually pay for on GCP Batch.
        ct = datetime.fromisoformat(d["metrics"]["create_time"])
        ut = datetime.fromisoformat(d["metrics"]["update_time"])
        wallclock = max(0, (ut - ct).total_seconds())

        jobs.append({
            "cloud": d["cloud"],
            "workflow_id": d.get("workflow_id", ""),
            "tool": tool,
            "state": d["metrics"]["state"],
            "runtime": runtime or 0,
            "wallclock": wallclock,
            "slots": slots or 0,
            "mem_mb": mem or 0,
            "inputs": d.get("inputs", ""),
            "create_time": d["metrics"]["create_time"],
            "update_time": d["metrics"]["update_time"],
        })
    return jobs


def split_by_experiment(jobs):
    """Split jobs into experiment groups based on tool set similarity.

    Jobs from different Galaxy servers (batch vs pulsar) will have different
    workflow_ids but the same set of tools.  We cluster workflow_ids whose
    tool sets overlap by >= 50% into a single experiment.

    Returns a list of (experiment_name, job_list) tuples.
    """
    wf_tools = defaultdict(set)
    for j in jobs:
        wf_tools[j["workflow_id"]].add(j["tool"])

    wf_ids = list(wf_tools.keys())
    if len(wf_ids) <= 1:
        return [(None, jobs)]

    # Cluster by Jaccard overlap >= 0.5
    clusters = []
    assigned = set()
    for wf in wf_ids:
        if wf in assigned:
            continue
        cluster = {wf}
        assigned.add(wf)
        for other in wf_ids:
            if other in assigned:
                continue
            a, b = wf_tools[wf], wf_tools[other]
            overlap = len(a & b) / len(a | b) if a | b else 0
            if overlap >= 0.5:
                cluster.add(other)
                assigned.add(other)
        clusters.append(cluster)

    if len(clusters) <= 1:
        return [(None, jobs)]

    TOOL_TO_WORKFLOW = {
        "bwa_mem": "Variant-Calling",
        "rna_star": "RNASeq",
        "cufflinks": "RNASeq",
        "cutadapt": "RNASeq",
        "macs2_callpeak": "ChIPSeq",
        "bamcompare": "ChIPSeq",
    }

    result = []
    used_names = set()
    for cluster in clusters:
        cluster_jobs = [j for j in jobs if j["workflow_id"] in cluster]
        all_tools = set()
        for j in cluster_jobs:
            all_tools.add(j["tool"])

        name = None
        for tool, wf_name in TOOL_TO_WORKFLOW.items():
            if tool in all_tools and wf_name not in used_names:
                name = wf_name
                break

        if name is None:
            tool_runtimes = defaultdict(list)
            for j in cluster_jobs:
                if j["state"] == "ok" and j["runtime"] > 0:
                    tool_runtimes[j["tool"]].append(j["runtime"])
            if tool_runtimes:
                dominant = max(tool_runtimes,
                               key=lambda t: sum(tool_runtimes[t]) / len(tool_runtimes[t]))
                name = dominant
            else:
                name = f"Experiment-{len(result) + 1}"

        used_names.add(name)
        result.append((name, cluster_jobs))

    return result


def compute_machine_type(slots, mem_mb):
    """Determine N2 machine type vCPU and memory from requested resources."""
    vcpus = max(2, int(slots)) if slots > 0 else 2
    # Round up to nearest N2 standard tier
    for n2_vcpu in sorted(N2_STANDARD.keys()):
        if n2_vcpu >= vcpus:
            vcpus = n2_vcpu
            break
    else:
        vcpus = max(N2_STANDARD.keys())
    mem_gb = N2_STANDARD[vcpus]
    # If requested memory exceeds standard, use highmem (2x memory)
    if mem_mb > 0 and mem_mb / 1024 > mem_gb:
        mem_gb = vcpus * 8  # highmem ratio
    return vcpus, mem_gb


def _cost_for_duration(hours, vcpus, mem_gb, cloud):
    """Compute cost components for a given duration."""
    vcpu_cost = vcpus * VCPU_PER_HOUR * hours
    mem_cost = mem_gb * MEM_PER_GB_HOUR * hours
    ssd_cost = PULSAR_SSD_GB * SSD_PER_GB_HOUR * hours if cloud == "pulsar" else 0
    boot_cost = BOOT_DISK_GB * BOOT_DISK_PER_GB_MONTH / (30 * 24) * hours
    return {
        "vcpu_cost": vcpu_cost,
        "mem_cost": mem_cost,
        "ssd_cost": ssd_cost,
        "boot_cost": boot_cost,
        "total_cost": vcpu_cost + mem_cost + ssd_cost + boot_cost,
        "hours": hours,
    }


def compute_job_cost(job):
    """Compute cost components for a single job.

    Returns two cost dicts: one based on cgroups runtime (compute), and one
    based on Galaxy wallclock (create_time to update_time).  The wallclock
    cost reflects what users actually pay for on GCP Batch, including VM
    provisioning, image pull, staging, and shutdown overhead.
    """
    vcpus, mem_gb = compute_machine_type(job["slots"], job["mem_mb"])
    compute = _cost_for_duration(job["runtime"] / 3600, vcpus, mem_gb, job["cloud"])
    wallclock = _cost_for_duration(job["wallclock"] / 3600, vcpus, mem_gb, job["cloud"])
    compute["vcpus"] = vcpus
    compute["mem_gb"] = mem_gb
    wallclock["vcpus"] = vcpus
    wallclock["mem_gb"] = mem_gb
    return {"compute": compute, "wallclock": wallclock}


# ---------------------------------------------------------------------------
# Rainstone API
# ---------------------------------------------------------------------------

def fetch_rainstone(tool_id):
    """Query Rainstone API for a tool's cost statistics."""
    url = f"https://rainstone.anvilproject.org/api/tools/{tool_id}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return {
            "avg": data.get("averageCostPerJob", 0),
            "median": data.get("medianCostPerJob", 0),
            "p95": data.get("p95CostPerJob", 0),
            "num_jobs": data.get("numJobs", 0),
        }
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as e:
        print(f"  Warning: Rainstone lookup failed for {tool_id}: {e}", file=sys.stderr)
        return None


def fetch_all_rainstone(tool_ids):
    """Fetch Rainstone data for all tools, returning {tool_id: data}."""
    results = {}
    for tid in tool_ids:
        data = fetch_rainstone(tid)
        if data:
            results[tid] = data
    return results


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def _empty_cost_bucket():
    return {"jobs": 0, "total_cost": 0, "vcpus": 0, "hours": 0,
            "vcpu_cost": 0, "mem_cost": 0, "ssd_cost": 0, "boot_cost": 0}


def _aggregate_one(ok_jobs, cost_key):
    """Aggregate costs for a single cost_key ('compute' or 'wallclock')."""
    cloud_totals = {}
    for cloud in ["batch", "pulsar"]:
        cloud_jobs = [j for j in ok_jobs if j["cloud"] == cloud]
        if not cloud_jobs:
            continue
        cloud_totals[cloud] = {
            "jobs": len(cloud_jobs),
            "vm_hours": sum(j["cost"][cost_key]["hours"] for j in cloud_jobs),
            "vcpu_cost": sum(j["cost"][cost_key]["vcpu_cost"] for j in cloud_jobs),
            "mem_cost": sum(j["cost"][cost_key]["mem_cost"] for j in cloud_jobs),
            "ssd_cost": sum(j["cost"][cost_key]["ssd_cost"] for j in cloud_jobs),
            "boot_cost": sum(j["cost"][cost_key]["boot_cost"] for j in cloud_jobs),
            "total_cost": sum(j["cost"][cost_key]["total_cost"] for j in cloud_jobs),
        }

    tool_data = defaultdict(lambda: defaultdict(_empty_cost_bucket))
    for j in ok_jobs:
        td = tool_data[j["tool"]][j["cloud"]]
        c = j["cost"][cost_key]
        td["jobs"] += 1
        td["total_cost"] += c["total_cost"]
        td["vcpus"] = max(td["vcpus"], c["vcpus"])
        td["hours"] += c["hours"]
        td["vcpu_cost"] += c["vcpu_cost"]
        td["mem_cost"] += c["mem_cost"]
        td["ssd_cost"] += c["ssd_cost"]
        td["boot_cost"] += c["boot_cost"]

    return cloud_totals, tool_data


def aggregate_costs(jobs):
    """Aggregate cost data by cloud and tool for both compute and wallclock."""
    ok_jobs = [j for j in jobs if j["state"] == "ok"]

    for j in ok_jobs:
        j["cost"] = compute_job_cost(j)

    compute_cloud, compute_tool = _aggregate_one(ok_jobs, "compute")
    wall_cloud, wall_tool = _aggregate_one(ok_jobs, "wallclock")

    # Sort tools by wallclock total cost descending (what users actually pay)
    all_tools = set(compute_tool.keys()) | set(wall_tool.keys())
    tool_order = sorted(all_tools,
                        key=lambda t: sum(wall_tool[t][c]["total_cost"]
                                          for c in wall_tool[t]),
                        reverse=True)

    return ok_jobs, compute_cloud, compute_tool, wall_cloud, wall_tool, tool_order


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def _runner_summary_table(w, cloud_totals, label):
    """Write a runner summary table (used for both compute and wallclock)."""
    w(f"| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |")
    w("|--------|------|----------|-----------|-------------|----------|-----------|------------|")
    grand = {"jobs": 0, "vm_hours": 0, "vcpu_cost": 0, "mem_cost": 0,
             "ssd_cost": 0, "boot_cost": 0, "total_cost": 0}
    for cloud in ["batch", "pulsar"]:
        if cloud not in cloud_totals:
            continue
        ct = cloud_totals[cloud]
        w(f"| **{cloud.title()}** | {ct['jobs']} | {ct['vm_hours']:.1f}h | "
          f"${ct['vcpu_cost']:.2f} | ${ct['mem_cost']:.2f} | "
          f"${ct['ssd_cost']:.2f} | ${ct['boot_cost']:.2f} | "
          f"**${ct['total_cost']:.2f}** |")
        for k in grand:
            grand[k] += ct[k]
    w(f"| **Total** | {grand['jobs']} | {grand['vm_hours']:.1f}h | "
      f"${grand['vcpu_cost']:.2f} | ${grand['mem_cost']:.2f} | "
      f"${grand['ssd_cost']:.2f} | ${grand['boot_cost']:.2f} | "
      f"**${grand['total_cost']:.2f}** |")
    return grand


def _per_tool_table(w, tool_data, tool_order, rainstone, label):
    """Write a per-tool cost table (used for both compute and wallclock)."""
    w(f"| Tool | vCPU | Batch Jobs | Batch Cost | Batch $/Job | "
      f"Pulsar Jobs | Pulsar Cost | Pulsar $/Job | Rainstone Est. |")
    w("|------|------|-----------|------------|-------------|"
      "------------|-------------|--------------|----------------|")
    b_grand = p_grand = 0
    b_jobs_grand = p_jobs_grand = 0
    for tool in tool_order:
        bd = tool_data[tool].get("batch", _empty_cost_bucket())
        pd = tool_data[tool].get("pulsar", _empty_cost_bucket())
        vcpus = max(bd.get("vcpus", 0), pd.get("vcpus", 0))
        b_per = bd["total_cost"] / bd["jobs"] if bd["jobs"] > 0 else 0
        p_per = pd["total_cost"] / pd["jobs"] if pd["jobs"] > 0 else 0
        r_est = f"${rainstone[tool]['avg']:.4f}" if tool in rainstone else "--"
        w(f"| {tool} | {vcpus} | {bd['jobs']} | ${bd['total_cost']:.2f} | "
          f"${b_per:.4f} | {pd['jobs']} | ${pd['total_cost']:.2f} | "
          f"${p_per:.4f} | {r_est} |")
        b_grand += bd["total_cost"]
        p_grand += pd["total_cost"]
        b_jobs_grand += bd["jobs"]
        p_jobs_grand += pd["jobs"]
    w(f"| **Total** | | **{b_jobs_grand}** | **${b_grand:.2f}** | | "
      f"**{p_jobs_grand}** | **${p_grand:.2f}** | | |")


def generate_markdown(compute_cloud, compute_tool, wall_cloud, wall_tool,
                      tool_order, rainstone, experiment_name, date_range,
                      galaxy_vm=None, local_vm=None):
    workflow_title = derive_experiment_title(experiment_name)
    total_jobs = sum(ct["jobs"] for ct in wall_cloud.values())

    lines = []
    w = lines.append

    w("---")
    w(f"title: {workflow_title} Cost Summary")
    w("---")
    w("")
    w(f"# {workflow_title} Cost Summary")
    w("")
    w(f"**[Interactive Cost Charts](cost-charts.html)** | "
      f"**[Performance Report](index.html)** | "
      f"**[Performance Charts](charts.html)**")
    w("")
    w(f"**Period:** {date_range}  ")
    w(f"**Region:** us-east4  ")
    w(f"**Total Jobs:** {total_jobs} (ok)")
    w("")

    # ---- Wallclock-based costs (what users pay) ----
    w("## Estimated Cost (Wallclock)")
    w("")
    w("Cost based on total VM lifetime per job (Galaxy create_time to "
      "update_time). This is what users pay for on GCP Batch — it includes "
      "VM provisioning, image pull, file staging, compute, and shutdown.")
    w("")
    wall_grand = _runner_summary_table(w, wall_cloud, "Wallclock")
    w("")

    # Galaxy VM cost (e2-standard-4 host, not included in per-tool costs)
    if galaxy_vm:
        w("### Galaxy Host VM Cost")
        w("")
        w("Each runner requires a Galaxy host VM (e2-standard-4, 4 vCPU, 16 GB) "
          "running for the duration of the experiment. This cost is not included "
          "in the per-tool or compute-time calculations above.")
        w("")
        w("| Runner | Duration | Galaxy VM Cost |")
        w("|--------|----------|----------------|")
        for cloud in ["batch", "pulsar"]:
            if cloud in galaxy_vm:
                gv = galaxy_vm[cloud]
                w(f"| **{cloud.title()}** | {gv['hours']:.1f}h | ${gv['cost']:.2f} |")
        w("")

    # Total wallclock + Galaxy VM
    if galaxy_vm:
        w("### Total Estimated Cost (Batch Jobs + Galaxy VM)")
        w("")
        w("| Runner | Batch Job Cost | Galaxy VM Cost | **Total** |")
        w("|--------|---------------|----------------|-----------|")
        for cloud in ["batch", "pulsar"]:
            if cloud in wall_cloud and cloud in galaxy_vm:
                jc = wall_cloud[cloud]["total_cost"]
                gc = galaxy_vm[cloud]["cost"]
                w(f"| **{cloud.title()}** | ${jc:.2f} | ${gc:.2f} | **${jc + gc:.2f}** |")
        w("")
        if "batch" in wall_cloud and "pulsar" in wall_cloud:
            b = wall_cloud["batch"]["total_cost"] + galaxy_vm.get("batch", {}).get("cost", 0)
            p = wall_cloud["pulsar"]["total_cost"] + galaxy_vm.get("pulsar", {}).get("cost", 0)
            ratio = p / b if b > 0 else 0
            w(f"Pulsar costs **${p:.2f}** vs Batch **${b:.2f}** ({ratio:.1f}x) including Galaxy VM.")
        w("")
    elif "batch" in wall_cloud and "pulsar" in wall_cloud:
        b = wall_cloud["batch"]["total_cost"]
        p = wall_cloud["pulsar"]["total_cost"]
        ratio = p / b if b > 0 else 0
        w(f"Pulsar costs **${p:.2f}** vs Batch **${b:.2f}** ({ratio:.1f}x).")
        w("")

    # ---- Compute-only costs (cgroups runtime) ----
    w("## Compute-Only Cost (cgroups)")
    w("")
    w("Cost based on cgroups `runtime_seconds` only — the actual CPU time "
      "reported by the container. Excludes VM boot, scheduling, and staging "
      "overhead.")
    w("")
    compute_grand = _runner_summary_table(w, compute_cloud, "Compute")
    w("")
    if "batch" in compute_cloud and "pulsar" in compute_cloud:
        b = compute_cloud["batch"]["total_cost"]
        p = compute_cloud["pulsar"]["total_cost"]
        ratio = p / b if b > 0 else 0
        w(f"Pulsar costs **${p:.2f}** vs Batch **${b:.2f}** ({ratio:.1f}x).")
    w("")

    # ---- Overhead ratio ----
    w("### Wallclock vs Compute Overhead")
    w("")
    w("| Runner | Compute Cost | Wallclock Cost | Overhead Ratio |")
    w("|--------|-------------|----------------|----------------|")
    for cloud in ["batch", "pulsar"]:
        if cloud in compute_cloud and cloud in wall_cloud:
            cc = compute_cloud[cloud]["total_cost"]
            wc = wall_cloud[cloud]["total_cost"]
            ratio = wc / cc if cc > 0 else 0
            w(f"| **{cloud.title()}** | ${cc:.2f} | ${wc:.2f} | {ratio:.1f}x |")
    w("")
    w("The overhead ratio shows how much more users pay compared to pure "
      "compute. This includes VM provisioning (~2-5 min per job), container "
      "image pull, file staging (Pulsar: HTTP upload/download; Batch: NFS), "
      "and Galaxy scheduling delays.")
    w("")

    # Cost component breakdown (wallclock)
    w("### Cost Component Breakdown (Wallclock)")
    w("")
    w("| Component | Batch | Pulsar | Total | % |")
    w("|-----------|-------|--------|-------|---|")
    for comp, label in [("vcpu_cost", "vCPU"), ("mem_cost", "Memory"),
                        ("ssd_cost", "Local SSD"), ("boot_cost", "Boot Disk")]:
        b = wall_cloud.get("batch", {}).get(comp, 0)
        p = wall_cloud.get("pulsar", {}).get(comp, 0)
        total = b + p
        pct = f"{total / wall_grand['total_cost'] * 100:.0f}%" if wall_grand["total_cost"] > 0 else "--"
        w(f"| {label} | ${b:.2f} | ${p:.2f} | ${total:.2f} | {pct} |")
    b_total = wall_cloud.get("batch", {}).get("total_cost", 0)
    p_total = wall_cloud.get("pulsar", {}).get("total_cost", 0)
    w(f"| **Total** | **${b_total:.2f}** | **${p_total:.2f}** | "
      f"**${wall_grand['total_cost']:.2f}** | |")
    w("")

    if "pulsar" in wall_cloud:
        w("Note: Batch jobs use NFS for file staging (no local SSD cost). "
          "Pulsar jobs each provision a 375 GB local SSD.")
        w("")

    # Per-Tool Cost Comparison (wallclock)
    w("## Per-Tool Cost Comparison (Wallclock)")
    w("")
    if rainstone:
        w("The Rainstone Est. column shows the average cost per job from the "
          "[Rainstone cost API](https://rainstone.anvilproject.org/api/docs), "
          "based on historical usegalaxy.org usage.")
    w("")
    _per_tool_table(w, wall_tool, tool_order, rainstone, "Wallclock")
    w("")

    # Per-Tool Cost Comparison (compute)
    w("## Per-Tool Cost Comparison (Compute-Only)")
    w("")
    _per_tool_table(w, compute_tool, tool_order, rainstone, "Compute")
    w("")

    # Rainstone Comparison (use compute costs — Rainstone reflects cgroups-like runtimes)
    if rainstone:
        w("## Rainstone Comparison")
        w("")
        w("Per-job compute cost comparison against "
          "[Rainstone](https://rainstone.anvilproject.org) "
          "historical averages from usegalaxy.org. Rainstone data reflects median costs "
          "across thousands of production runs.")
        w("")
        w("| Tool | Batch $/Job | Pulsar $/Job | Rainstone Avg | "
          "Rainstone Median | Rainstone P95 | usegalaxy.org Jobs |")
        w("|------|-------------|--------------|---------------|"
          "-----------------|---------------|------------|")
        for tool in tool_order:
            bd = compute_tool[tool].get("batch", _empty_cost_bucket())
            pd = compute_tool[tool].get("pulsar", _empty_cost_bucket())
            b_per = bd["total_cost"] / bd["jobs"] if bd["jobs"] > 0 else 0
            p_per = pd["total_cost"] / pd["jobs"] if pd["jobs"] > 0 else 0
            if tool in rainstone:
                r = rainstone[tool]
                w(f"| {tool} | ${b_per:.4f} | ${p_per:.4f} | "
                  f"${r['avg']:.4f} | ${r['median']:.4f} | "
                  f"${r['p95']:.4f} | {r['num_jobs']:,} |")
            else:
                w(f"| {tool} | ${b_per:.4f} | ${p_per:.4f} | -- | -- | -- | -- |")
        w("")

    # Pricing Assumptions
    w("## Pricing Assumptions")
    w("")
    w("All costs are estimated using GCP N2 on-demand pricing for `us-east4`:")
    w("")
    w("| Resource | Rate |")
    w("|----------|------|")
    w(f"| N2 vCPU | ${VCPU_PER_HOUR}/vCPU/hour |")
    w(f"| N2 Memory | ${MEM_PER_GB_HOUR}/GB/hour |")
    w(f"| Local SSD | ${SSD_PER_GB_HOUR}/GB/hour |")
    w(f"| Boot Disk (pd-balanced) | ${BOOT_DISK_PER_GB_MONTH}/GB/month |")
    w("")
    w("**Wallclock cost** uses the full Galaxy job lifetime (create_time to "
      "update_time) as the billing duration. This includes VM provisioning, "
      "container image pull, file staging, and scheduling overhead — all of "
      "which the user pays for on GCP Batch.")
    w("")
    w("**Compute-only cost** uses cgroups `runtime_seconds` — the actual CPU "
      "time inside the container. This is a lower bound that excludes all "
      "infrastructure overhead.")
    w("")
    w("Pulsar jobs each provision a 375 GB local SSD and a 30 GB boot disk. "
      "Batch jobs use NFS for staging (no local SSD). VM machine types are "
      "selected automatically based on tool CPU and memory requirements "
      "via `compute_machine_type()`.")
    w("")
    if rainstone:
        w("Rainstone estimates are sourced from the "
          "[Rainstone Cost API](https://rainstone.anvilproject.org/api/docs) "
          "and reflect historical averages across usegalaxy.org production workloads.")
    w("")

    # Deployment Model Comparison
    if local_vm and galaxy_vm:
        w("## Deployment Model Comparison")
        w("")
        w("Comparison of our GCP Batch approach (Galaxy + Batch VMs) against the "
          "traditional deployment model where Galaxy runs jobs locally on a single "
          "large VM (n2-standard-20, 20 vCPU, 80 GB).")
        w("")
        w("In the local model, the single VM must run for the entire experiment "
          "duration. In the Batch model, per-job VMs are provisioned on demand "
          "and the Galaxy host is a smaller e2-standard-4.")
        w("")
        w("| Model | Runner | Duration | Job Cost | Galaxy VM | **Total** |")
        w("|-------|--------|----------|----------|-----------|-----------|")
        for cloud in ["batch", "pulsar"]:
            if cloud not in wall_cloud or cloud not in galaxy_vm:
                continue
            jc = wall_cloud[cloud]["total_cost"]
            gc = galaxy_vm[cloud]["cost"]
            batch_total = jc + gc
            lc = local_vm[cloud]["cost"]
            dur = galaxy_vm[cloud]["hours"]
            w(f"| **GCP Batch** | {cloud.title()} | {dur:.1f}h | ${jc:.2f} | "
              f"${gc:.2f} | **${batch_total:.2f}** |")
            w(f"| **Local VM** | {cloud.title()} | {dur:.1f}h | -- | "
              f"${lc:.2f} | **${lc:.2f}** |")
        w("")

        # Summary comparison
        for cloud in ["batch", "pulsar"]:
            if cloud not in wall_cloud or cloud not in galaxy_vm:
                continue
            batch_total = wall_cloud[cloud]["total_cost"] + galaxy_vm[cloud]["cost"]
            lv = local_vm[cloud]["cost"]
            if lv > 0:
                ratio = batch_total / lv
                if ratio < 1:
                    w(f"**{cloud.title()}**: GCP Batch is **{(1 - ratio) * 100:.0f}% cheaper** "
                      f"than a local n2-standard-20 (${batch_total:.2f} vs ${lv:.2f}).")
                else:
                    w(f"**{cloud.title()}**: GCP Batch is **{(ratio - 1) * 100:.0f}% more expensive** "
                      f"than a local n2-standard-20 (${batch_total:.2f} vs ${lv:.2f}).")
        w("")
        w(f"Local VM pricing: n2-standard-20 at ${LOCAL_VM_HOURLY:.4f}/hour "
          f"({LOCAL_VM_VCPUS} vCPU × ${VCPU_PER_HOUR}/h + "
          f"{LOCAL_VM_MEM_GB} GB × ${MEM_PER_GB_HOUR}/h).")
        w("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML chart generation
# ---------------------------------------------------------------------------

def _tool_arrays(tool_data, tool_order):
    """Extract per-tool arrays from tool_data for chart generation."""
    batch_cost, pulsar_cost = [], []
    batch_per_job, pulsar_per_job = [], []
    batch_hours, pulsar_hours = [], []
    empty = _empty_cost_bucket()
    for tool in tool_order:
        bd = tool_data[tool].get("batch", empty)
        pd = tool_data[tool].get("pulsar", empty)
        batch_cost.append(round(bd["total_cost"], 2))
        pulsar_cost.append(round(pd["total_cost"], 2))
        batch_per_job.append(round(bd["total_cost"] / bd["jobs"], 4) if bd["jobs"] > 0 else 0)
        pulsar_per_job.append(round(pd["total_cost"] / pd["jobs"], 4) if pd["jobs"] > 0 else 0)
        batch_hours.append(round(bd["hours"], 2))
        pulsar_hours.append(round(pd["hours"], 2))
    return batch_cost, pulsar_cost, batch_per_job, pulsar_per_job, batch_hours, pulsar_hours


def _ratio_label(b_total, p_total):
    if b_total > 0 and p_total > 0:
        ratio = p_total / b_total
        label = f"{ratio:.1f}x"
        if 0.95 < ratio < 1.05:
            detail = "Essentially identical cost"
        elif ratio >= 1.05:
            detail = f"Pulsar is {(ratio - 1) * 100:.0f}% more expensive"
        else:
            detail = f"Pulsar is {(1 - ratio) * 100:.0f}% cheaper"
        return label, detail
    return "--", "Single runner"


def generate_html(compute_cloud, compute_tool, wall_cloud, wall_tool,
                  tool_order, rainstone, experiment_name,
                  galaxy_vm=None, local_vm=None):
    workflow_title = derive_experiment_title(experiment_name)
    total_jobs = sum(ct["jobs"] for ct in wall_cloud.values())
    num_tools = len(tool_order)

    tools_json = json.dumps(tool_order)
    tools_short = [t[:12] if len(t) > 12 else t for t in tool_order]
    tools_short_json = json.dumps(tools_short)

    # Wallclock arrays (primary — what users pay)
    w_bc, w_pc, w_bpj, w_ppj, w_bh, w_ph = _tool_arrays(wall_tool, tool_order)
    # Compute arrays
    c_bc, c_pc, c_bpj, c_ppj, c_bh, c_ph = _tool_arrays(compute_tool, tool_order)

    r_avg = [round(rainstone.get(t, {}).get("avg", 0), 4) for t in tool_order]
    r_median = [round(rainstone.get(t, {}).get("median", 0), 4) for t in tool_order]
    r_p95 = [round(rainstone.get(t, {}).get("p95", 0), 4) for t in tool_order]

    _empty_ct = {"vcpu_cost": 0, "mem_cost": 0, "ssd_cost": 0, "boot_cost": 0,
                 "total_cost": 0, "jobs": 0, "vm_hours": 0}
    w_b_ct = wall_cloud.get("batch", _empty_ct)
    w_p_ct = wall_cloud.get("pulsar", _empty_ct)
    w_grand = w_b_ct["total_cost"] + w_p_ct["total_cost"]
    c_b_ct = compute_cloud.get("batch", _empty_ct)
    c_p_ct = compute_cloud.get("pulsar", _empty_ct)
    c_grand = c_b_ct["total_cost"] + c_p_ct["total_cost"]

    w_ratio_label, w_ratio_detail = _ratio_label(w_b_ct["total_cost"], w_p_ct["total_cost"])
    c_ratio_label, c_ratio_detail = _ratio_label(c_b_ct["total_cost"], c_p_ct["total_cost"])

    std_vcpu_frac = VCPU_PER_HOUR / (VCPU_PER_HOUR + MEM_PER_GB_HOUR * 4)

    html = []
    h = html.append

    h('<!DOCTYPE html>')
    h('<html lang="en">')
    h('<head>')
    h('<meta charset="UTF-8">')
    h('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    h(f'<title>Pulsar vs GCP Batch: Cost Analysis</title>')
    h('<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>')
    h('<style>')
    h('  * { box-sizing: border-box; margin: 0; padding: 0; }')
    h('  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f7fa; color: #1a1a2e; padding: 2rem; max-width: 1200px; margin: 0 auto; }')
    h('  h1 { font-size: 1.8rem; margin-bottom: 0.3rem; }')
    h('  .subtitle { color: #666; font-size: 0.95rem; margin-bottom: 1.5rem; }')
    h('  .nav { display: flex; gap: 1.5rem; margin-bottom: 1.5rem; font-size: 0.9rem; }')
    h('  .nav a { color: #3b82f6; text-decoration: none; }')
    h('  .nav a:hover { text-decoration: underline; }')
    h('  .tabs { display: flex; gap: 0; margin-bottom: 2rem; border-bottom: 2px solid #e5e7eb; flex-wrap: wrap; }')
    h('  .tab { padding: 0.7rem 1.4rem; cursor: pointer; font-size: 0.9rem; font-weight: 500; color: #666; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: color 0.2s, border-color 0.2s; user-select: none; }')
    h('  .tab:hover { color: #1a1a2e; }')
    h('  .tab.active { color: #3b82f6; border-bottom-color: #3b82f6; }')
    h('  .tab-content { display: none; }')
    h('  .tab-content.active { display: block; }')
    h('  .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }')
    h('  .card { background: #fff; border-radius: 10px; padding: 1.2rem 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }')
    h('  .card .label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em; }')
    h('  .card .value { font-size: 1.8rem; font-weight: 700; margin-top: 0.2rem; }')
    h('  .card .detail { font-size: 0.85rem; color: #666; margin-top: 0.2rem; }')
    h('  .card.batch .value { color: #3b82f6; }')
    h('  .card.pulsar .value { color: #f59e0b; }')
    h('  .card.total .value { color: #8b5cf6; }')
    h('  .card.neutral .value { color: #22c55e; }')
    h('  .card.overhead .value { color: #ef4444; }')
    h('  .chart-container { background: #fff; border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }')
    h('  .chart-container h2 { font-size: 1.1rem; margin-bottom: 0.3rem; }')
    h('  .chart-container .chart-desc { font-size: 0.85rem; color: #888; margin-bottom: 1rem; }')
    h('  .chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }')
    h('  @media (max-width: 800px) { .chart-row { grid-template-columns: 1fr; } }')
    h('  .footer { text-align: center; color: #aaa; font-size: 0.8rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; }')
    h('</style>')
    h('</head>')
    h('<body>')
    h('')
    h(f'<h1>Pulsar vs Direct GCP Batch: Cost Analysis</h1>')
    h(f'<p class="subtitle">{workflow_title} &mdash; {total_jobs} jobs &mdash; {num_tools} tool types &mdash; us-east4</p>')
    h('')
    h('<div class="nav">')
    h('  <a href="index.html">&larr; Results Report</a>')
    h('  <a href="charts.html">Performance Charts</a>')
    h('  <a href="costs.html">Cost Tables (Markdown)</a>')
    h('</div>')
    h('')
    h('<div class="tabs">')
    h('  <div class="tab active" data-tab="overview">Overview</div>')
    h('  <div class="tab" data-tab="per-tool-wall">Per-Tool (Wallclock)</div>')
    h('  <div class="tab" data-tab="per-tool-compute">Per-Tool (Compute)</div>')
    if rainstone:
        h('  <div class="tab" data-tab="rainstone">Rainstone Comparison</div>')
    h('  <div class="tab" data-tab="breakdown">Cost Breakdown</div>')
    h('</div>')
    h('')

    # ===== OVERVIEW TAB =====
    # Compute overhead ratio
    b_overhead = (w_b_ct["total_cost"] / c_b_ct["total_cost"]) if c_b_ct["total_cost"] > 0 else 0
    p_overhead = (w_p_ct["total_cost"] / c_p_ct["total_cost"]) if c_p_ct["total_cost"] > 0 else 0

    h('<div class="tab-content active" id="overview">')
    h('  <div class="summary-cards">')
    if "batch" in wall_cloud:
        h(f'    <div class="card batch"><div class="label">Batch (Wallclock)</div>'
          f'<div class="value">${w_b_ct["total_cost"]:.2f}</div>'
          f'<div class="detail">{w_b_ct["jobs"]} jobs &middot; {w_b_ct["vm_hours"]:.1f} VM-hours '
          f'&middot; compute: ${c_b_ct["total_cost"]:.2f}</div></div>')
    if "pulsar" in wall_cloud:
        h(f'    <div class="card pulsar"><div class="label">Pulsar (Wallclock)</div>'
          f'<div class="value">${w_p_ct["total_cost"]:.2f}</div>'
          f'<div class="detail">{w_p_ct["jobs"]} jobs &middot; {w_p_ct["vm_hours"]:.1f} VM-hours '
          f'&middot; compute: ${c_p_ct["total_cost"]:.2f}</div></div>')
    h(f'    <div class="card neutral"><div class="label">Pulsar vs Batch</div>'
      f'<div class="value">{w_ratio_label}</div>'
      f'<div class="detail">{w_ratio_detail}</div></div>')
    h(f'    <div class="card overhead"><div class="label">Overhead Ratio</div>'
      f'<div class="value">{b_overhead:.1f}x / {p_overhead:.1f}x</div>'
      f'<div class="detail">Wallclock / Compute (Batch / Pulsar)</div></div>')

    # Galaxy VM + total cost cards
    if galaxy_vm:
        b_gv = galaxy_vm.get("batch", {"cost": 0})
        p_gv = galaxy_vm.get("pulsar", {"cost": 0})
        b_total_all = w_b_ct["total_cost"] + b_gv["cost"]
        p_total_all = w_p_ct["total_cost"] + p_gv["cost"]
        h(f'    <div class="card total"><div class="label">Total (Jobs + Galaxy VM)</div>'
          f'<div class="value">${b_total_all:.2f} / ${p_total_all:.2f}</div>'
          f'<div class="detail">Batch / Pulsar (incl. e2-standard-4 host)</div></div>')
    h('  </div>')

    h('  <div class="chart-container">')
    h('    <h2>Wallclock vs Compute Cost by Runner</h2>')
    h('    <p class="chart-desc">Grouped bars: compute cost (what the CPU used) vs wallclock cost (what you pay). The gap is infrastructure overhead.</p>')
    h('    <canvas id="wallVsComputeChart" height="60"></canvas>')
    h('  </div>')
    h('  <div class="chart-container">')
    h('    <h2>Cost Component Breakdown (Wallclock)</h2>')
    h('    <p class="chart-desc">Stacked by cost component: vCPU, memory, local SSD, and boot disk.</p>')
    h('    <canvas id="runnerStackedChart" height="60"></canvas>')
    h('  </div>')
    h('  <div class="chart-container">')
    h('    <h2>Component Distribution</h2>')
    w_vcpu_total = w_b_ct.get("vcpu_cost", 0) + w_p_ct.get("vcpu_cost", 0)
    h(f'    <p class="chart-desc">Where the money goes: vCPU dominates at '
      f'{w_vcpu_total / w_grand * 100:.0f}%.</p>')
    h('    <canvas id="componentDonutChart" height="60"></canvas>')
    h('  </div>')
    h('</div>')
    h('')

    # ===== PER-TOOL WALLCLOCK TAB =====
    h('<div class="tab-content" id="per-tool-wall">')
    h('  <div class="chart-container">')
    h('    <h2>Per-Tool Wallclock Cost: Batch vs Pulsar</h2>')
    h('    <p class="chart-desc">Total wallclock cost for each tool. This is what users pay including VM boot, staging, and scheduling.</p>')
    h('    <canvas id="perToolWallChart" height="100"></canvas>')
    h('  </div>')
    h('  <div class="chart-container">')
    h('    <h2>Per-Job Wallclock Cost: Batch vs Pulsar</h2>')
    h('    <p class="chart-desc">Average wallclock cost per job invocation.</p>')
    h('    <canvas id="perJobWallChart" height="100"></canvas>')
    h('  </div>')
    h('  <div class="chart-container">')
    h('    <h2>Wallclock Cost Difference (Pulsar &minus; Batch)</h2>')
    h('    <p class="chart-desc">Green = Pulsar cheaper, red = Pulsar more expensive. Per-job average.</p>')
    h('    <canvas id="costDiffWallChart" height="100"></canvas>')
    h('  </div>')
    h('</div>')
    h('')

    # ===== PER-TOOL COMPUTE TAB =====
    h('<div class="tab-content" id="per-tool-compute">')
    h('  <div class="chart-container">')
    h('    <h2>Per-Tool Compute Cost: Batch vs Pulsar</h2>')
    h('    <p class="chart-desc">Total cost based on cgroups runtime only (excludes VM overhead).</p>')
    h('    <canvas id="perToolCompChart" height="100"></canvas>')
    h('  </div>')
    h('  <div class="chart-container">')
    h('    <h2>Per-Job Compute Cost: Batch vs Pulsar</h2>')
    h('    <p class="chart-desc">Average compute-only cost per job invocation.</p>')
    h('    <canvas id="perJobCompChart" height="100"></canvas>')
    h('  </div>')
    h('  <div class="chart-container">')
    h('    <h2>Overhead Ratio by Tool (Wallclock / Compute)</h2>')
    h('    <p class="chart-desc">How much more each tool costs due to infrastructure overhead. Higher = more overhead relative to actual computation.</p>')
    h('    <canvas id="overheadRatioChart" height="100"></canvas>')
    h('  </div>')
    h('</div>')
    h('')

    # ===== RAINSTONE TAB =====
    if rainstone:
        h('<div class="tab-content" id="rainstone">')
        h('  <div class="chart-container">')
        h('    <h2>Batch vs Pulsar vs Rainstone (usegalaxy.org Historical Average)</h2>')
        h('    <p class="chart-desc">Per-job compute cost compared to Rainstone historical averages from usegalaxy.org production workloads. Log scale.</p>')
        h('    <canvas id="rainstoneChart" height="120"></canvas>')
        h('  </div>')
        h('  <div class="chart-container">')
        h('    <h2>Rainstone Cost Range: Median to P95</h2>')
        h('    <p class="chart-desc">Floating bars show usegalaxy.org historical cost range (median to P95). Dots show our compute per-job costs.</p>')
        h('    <canvas id="rainstoneRangeChart" height="120"></canvas>')
        h('  </div>')
        h('</div>')
        h('')

    # ===== BREAKDOWN TAB =====
    h('<div class="tab-content" id="breakdown">')
    h('  <div class="chart-container">')
    h('    <h2>VM-Hours by Tool (Wallclock)</h2>')
    h('    <p class="chart-desc">Total VM-hours billed per tool (wallclock), both runners.</p>')
    h('    <canvas id="vmHoursChart" height="100"></canvas>')
    h('  </div>')
    h('  <div class="chart-row">')
    if "batch" in wall_cloud:
        h('    <div class="chart-container">')
        h('      <h2>Batch: Cost Components by Tool</h2>')
        h('      <p class="chart-desc">vCPU vs memory cost per tool (wallclock).</p>')
        h('      <canvas id="batchBreakdownChart" height="180"></canvas>')
        h('    </div>')
    if "pulsar" in wall_cloud:
        h('    <div class="chart-container">')
        h('      <h2>Pulsar: Cost Components by Tool</h2>')
        h('      <p class="chart-desc">vCPU vs memory vs SSD cost per tool (wallclock).</p>')
        h('      <canvas id="pulsarBreakdownChart" height="180"></canvas>')
        h('    </div>')
    h('  </div>')
    h('</div>')
    h('')

    # Footer
    h('<div class="footer">')
    h(f'  Galaxy 26.1 &middot; GCP Batch us-east4 &middot; N2 on-demand pricing &middot; '
      f'{total_jobs} jobs &middot; Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>')
    h('')

    # ===== JAVASCRIPT =====
    h('<script>')
    h('const blue = "#3b82f6", blueLight = "#93bbfd", amber = "#f59e0b", amberLight = "#fcd679";')
    h('const red = "#ef4444", green = "#22c55e", purple = "#8b5cf6", purpleLight = "#c4b5fd";')
    h('Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif";')
    h('Chart.defaults.font.size = 12;')
    h('')
    h(f'const tools = {tools_json};')
    h(f'const toolsShort = {tools_short_json};')
    h('')
    # Wallclock data (primary)
    h(f'const wBatchCost = {json.dumps(w_bc)};')
    h(f'const wPulsarCost = {json.dumps(w_pc)};')
    h(f'const wBatchPerJob = {json.dumps(w_bpj)};')
    h(f'const wPulsarPerJob = {json.dumps(w_ppj)};')
    h(f'const wBatchHours = {json.dumps(w_bh)};')
    h(f'const wPulsarHours = {json.dumps(w_ph)};')
    # Compute data
    h(f'const cBatchCost = {json.dumps(c_bc)};')
    h(f'const cPulsarCost = {json.dumps(c_pc)};')
    h(f'const cBatchPerJob = {json.dumps(c_bpj)};')
    h(f'const cPulsarPerJob = {json.dumps(c_ppj)};')
    h('')
    if rainstone:
        h(f'const rainstoneAvg = {json.dumps(r_avg)};')
        h(f'const rainstoneMedian = {json.dumps(r_median)};')
        h(f'const rainstoneP95 = {json.dumps(r_p95)};')
    h('')

    # Component totals (wallclock)
    h(f'const wBatchVcpu = {w_b_ct.get("vcpu_cost", 0):.2f}, wBatchMem = {w_b_ct.get("mem_cost", 0):.2f}, wBatchSsd = {w_b_ct.get("ssd_cost", 0):.2f}, wBatchDisk = {w_b_ct.get("boot_cost", 0):.2f};')
    h(f'const wPulsarVcpu = {w_p_ct.get("vcpu_cost", 0):.2f}, wPulsarMem = {w_p_ct.get("mem_cost", 0):.2f}, wPulsarSsd = {w_p_ct.get("ssd_cost", 0):.2f}, wPulsarDisk = {w_p_ct.get("boot_cost", 0):.2f};')
    h('')
    h('const dollarFmt = ctx => `$${ctx.raw.toFixed(4)}`;')
    h('const dollarFmt2 = ctx => `$${ctx.raw.toFixed(2)}`;')
    h('')

    # Wallclock vs Compute overview chart
    h('new Chart(document.getElementById("wallVsComputeChart"), {')
    h('  type: "bar",')
    h('  data: {')
    h('    labels: ["Batch", "Pulsar"],')
    h('    datasets: [')
    h(f'      {{ label: "Compute Cost", data: [{c_b_ct["total_cost"]:.2f}, {c_p_ct["total_cost"]:.2f}], backgroundColor: [blueLight, amberLight], borderRadius: 4 }},')
    h(f'      {{ label: "Wallclock Cost", data: [{w_b_ct["total_cost"]:.2f}, {w_p_ct["total_cost"]:.2f}], backgroundColor: [blue, amber], borderRadius: 4 }}')
    h('    ]')
    h('  },')
    h('  options: {')
    h('    responsive: true,')
    h('    plugins: { legend: { position: "top" }, tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: $${ctx.raw.toFixed(2)}` } } },')
    h('    scales: { y: { title: { display: true, text: "USD" }, beginAtZero: true } }')
    h('  }')
    h('});')
    h('')

    # Runner Stacked Chart (wallclock)
    h('new Chart(document.getElementById("runnerStackedChart"), {')
    h('  type: "bar",')
    h('  data: {')
    h('    labels: ["Batch", "Pulsar"],')
    h('    datasets: [')
    h('      { label: "vCPU", data: [wBatchVcpu, wPulsarVcpu], backgroundColor: blue, borderRadius: 4 },')
    h('      { label: "Memory", data: [wBatchMem, wPulsarMem], backgroundColor: blueLight, borderRadius: 4 },')
    h('      { label: "Local SSD", data: [wBatchSsd, wPulsarSsd], backgroundColor: amber, borderRadius: 4 },')
    h('      { label: "Boot Disk", data: [wBatchDisk, wPulsarDisk], backgroundColor: amberLight, borderRadius: 4 }')
    h('    ]')
    h('  },')
    h('  options: {')
    h('    indexAxis: "y", responsive: true,')
    h('    plugins: { legend: { position: "top" }, tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: $${ctx.raw.toFixed(2)}` } } },')
    h('    scales: { x: { stacked: true, title: { display: true, text: "USD" }, beginAtZero: true }, y: { stacked: true } }')
    h('  }')
    h('});')
    h('')

    # Component Donut (wallclock)
    w_mem_total = w_b_ct.get("mem_cost", 0) + w_p_ct.get("mem_cost", 0)
    w_ssd_total = w_b_ct.get("ssd_cost", 0) + w_p_ct.get("ssd_cost", 0)
    w_disk_total = w_b_ct.get("boot_cost", 0) + w_p_ct.get("boot_cost", 0)
    h('new Chart(document.getElementById("componentDonutChart"), {')
    h('  type: "doughnut",')
    h('  data: {')
    h(f'    labels: ["vCPU (${w_vcpu_total:.2f})", "Memory (${w_mem_total:.2f})", "Local SSD (${w_ssd_total:.2f})", "Boot Disk (${w_disk_total:.2f})"],')
    h(f'    datasets: [{{ data: [{w_vcpu_total:.2f}, {w_mem_total:.2f}, {w_ssd_total:.2f}, {w_disk_total:.2f}], backgroundColor: [blue, blueLight, amber, amberLight], borderWidth: 2, borderColor: "#fff" }}]')
    h('  },')
    h('  options: {')
    h('    responsive: true, cutout: "55%",')
    h(f'    plugins: {{ legend: {{ position: "right" }}, tooltip: {{ callbacks: {{ label: ctx => {{ const pct = ((ctx.raw / {w_grand:.2f}) * 100).toFixed(0); return `${{ctx.label}}: ${{pct}}%`; }} }} }} }}')
    h('  }')
    h('});')
    h('')

    # Per-Tool Wallclock charts
    h('new Chart(document.getElementById("perToolWallChart"), { type: "bar",')
    h('  data: { labels: toolsShort, datasets: [')
    h('    { label: "Batch", data: wBatchCost, backgroundColor: blue, borderRadius: 4 },')
    h('    { label: "Pulsar", data: wPulsarCost, backgroundColor: amber, borderRadius: 4 }')
    h('  ]}, options: { responsive: true, plugins: { legend: { position: "top" }, tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: $${ctx.raw.toFixed(2)}` } } }, scales: { y: { title: { display: true, text: "USD" }, beginAtZero: true }, x: { ticks: { maxRotation: 45, minRotation: 45 } } } } });')
    h('')
    h('new Chart(document.getElementById("perJobWallChart"), { type: "bar",')
    h('  data: { labels: toolsShort, datasets: [')
    h('    { label: "Batch $/job", data: wBatchPerJob, backgroundColor: blue, borderRadius: 4 },')
    h('    { label: "Pulsar $/job", data: wPulsarPerJob, backgroundColor: amber, borderRadius: 4 }')
    h('  ]}, options: { responsive: true, plugins: { legend: { position: "top" }, tooltip: { callbacks: { label: dollarFmt } } }, scales: { y: { title: { display: true, text: "USD per job" }, beginAtZero: true }, x: { ticks: { maxRotation: 45, minRotation: 45 } } } } });')
    h('')
    h('const wCostDiff = wBatchPerJob.map((b, i) => +(wPulsarPerJob[i] - b).toFixed(4));')
    h('new Chart(document.getElementById("costDiffWallChart"), { type: "bar",')
    h('  data: { labels: toolsShort, datasets: [{ label: "Pulsar - Batch", data: wCostDiff, backgroundColor: wCostDiff.map(v => v <= 0 ? "#86efac" : "#fca5a5"), borderColor: wCostDiff.map(v => v <= 0 ? green : red), borderWidth: 1, borderRadius: 4 }]},')
    h('  options: { responsive: true, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => { const v = ctx.raw; const base = wBatchPerJob[ctx.dataIndex]; const pct = base > 0 ? ((v/base)*100).toFixed(0) : "--"; return `${v >= 0 ? "+" : ""}$${v.toFixed(4)} (${v >= 0 ? "+" : ""}${pct}%)`; } } } }, scales: { y: { title: { display: true, text: "USD per job" } }, x: { ticks: { maxRotation: 45, minRotation: 45 } } } } });')
    h('')

    # Per-Tool Compute charts
    h('new Chart(document.getElementById("perToolCompChart"), { type: "bar",')
    h('  data: { labels: toolsShort, datasets: [')
    h('    { label: "Batch", data: cBatchCost, backgroundColor: blue, borderRadius: 4 },')
    h('    { label: "Pulsar", data: cPulsarCost, backgroundColor: amber, borderRadius: 4 }')
    h('  ]}, options: { responsive: true, plugins: { legend: { position: "top" }, tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: $${ctx.raw.toFixed(2)}` } } }, scales: { y: { title: { display: true, text: "USD" }, beginAtZero: true }, x: { ticks: { maxRotation: 45, minRotation: 45 } } } } });')
    h('')
    h('new Chart(document.getElementById("perJobCompChart"), { type: "bar",')
    h('  data: { labels: toolsShort, datasets: [')
    h('    { label: "Batch $/job", data: cBatchPerJob, backgroundColor: blue, borderRadius: 4 },')
    h('    { label: "Pulsar $/job", data: cPulsarPerJob, backgroundColor: amber, borderRadius: 4 }')
    h('  ]}, options: { responsive: true, plugins: { legend: { position: "top" }, tooltip: { callbacks: { label: dollarFmt } } }, scales: { y: { title: { display: true, text: "USD per job" }, beginAtZero: true }, x: { ticks: { maxRotation: 45, minRotation: 45 } } } } });')
    h('')

    # Overhead ratio chart (wallclock / compute per tool)
    h('const batchOH = wBatchPerJob.map((w, i) => cBatchPerJob[i] > 0 ? +(w / cBatchPerJob[i]).toFixed(1) : 0);')
    h('const pulsarOH = wPulsarPerJob.map((w, i) => cPulsarPerJob[i] > 0 ? +(w / cPulsarPerJob[i]).toFixed(1) : 0);')
    h('new Chart(document.getElementById("overheadRatioChart"), { type: "bar",')
    h('  data: { labels: toolsShort, datasets: [')
    h('    { label: "Batch overhead", data: batchOH, backgroundColor: blue, borderRadius: 4 },')
    h('    { label: "Pulsar overhead", data: pulsarOH, backgroundColor: amber, borderRadius: 4 }')
    h('  ]}, options: { responsive: true, plugins: { legend: { position: "top" }, tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.raw}x` } } }, scales: { y: { title: { display: true, text: "Wallclock / Compute ratio" }, beginAtZero: true }, x: { ticks: { maxRotation: 45, minRotation: 45 } } } } });')
    h('')

    # Rainstone Charts (use compute per-job costs for apples-to-apples comparison)
    if rainstone:
        h('new Chart(document.getElementById("rainstoneChart"), { type: "bar",')
        h('  data: { labels: toolsShort, datasets: [')
        h('    { label: "Batch $/job", data: cBatchPerJob, backgroundColor: blue, borderRadius: 4 },')
        h('    { label: "Pulsar $/job", data: cPulsarPerJob, backgroundColor: amber, borderRadius: 4 },')
        h('    { label: "Rainstone Avg", data: rainstoneAvg, backgroundColor: purple, borderRadius: 4 }')
        h('  ]}, options: { responsive: true, plugins: { legend: { position: "top" }, tooltip: { callbacks: { label: dollarFmt } } }, scales: { y: { type: "logarithmic", title: { display: true, text: "USD per job (log)" }, ticks: { callback: v => "$" + v } }, x: { ticks: { maxRotation: 45, minRotation: 45 } } } } });')
        h('')
        h('new Chart(document.getElementById("rainstoneRangeChart"), { type: "bar",')
        h('  data: { labels: toolsShort, datasets: [')
        h('    { label: "Rainstone Median-P95 range", data: rainstoneMedian.map((m, i) => [m, rainstoneP95[i]]), backgroundColor: purpleLight + "66", borderColor: purple, borderWidth: 1, borderSkipped: false, borderRadius: 4 },')
        h('    { type: "scatter", label: "Batch $/job", data: cBatchPerJob.map((v, i) => ({x: i, y: v})), backgroundColor: blue, pointRadius: 6, pointStyle: "circle" },')
        h('    { type: "scatter", label: "Pulsar $/job", data: cPulsarPerJob.map((v, i) => ({x: i, y: v})), backgroundColor: amber, pointRadius: 6, pointStyle: "triangle" }')
        h('  ]}, options: { responsive: true, plugins: { legend: { position: "top" }, tooltip: { callbacks: { label: ctx => { if (ctx.datasetIndex === 0) { const [lo, hi] = ctx.raw; return `Rainstone range: $${lo.toFixed(4)} - $${hi.toFixed(4)}`; } return `${ctx.dataset.label}: $${ctx.raw.y.toFixed(4)}`; } } } }, scales: { y: { type: "logarithmic", title: { display: true, text: "USD per job (log)" }, ticks: { callback: v => "$" + v } }, x: { ticks: { maxRotation: 45, minRotation: 45 } } } } });')
        h('')

    # Breakdown Charts (wallclock)
    h(f'const stdVcpuFrac = {std_vcpu_frac:.3f};')
    h('')

    if "batch" in wall_cloud:
        h('const batchVcpuPerTool = wBatchCost.map(c => +(c * stdVcpuFrac).toFixed(3));')
        h('const batchMemPerTool = wBatchCost.map((c, i) => +(c - batchVcpuPerTool[i]).toFixed(3));')
        h('new Chart(document.getElementById("batchBreakdownChart"), { type: "bar",')
        h('  data: { labels: toolsShort, datasets: [')
        h('    { label: "vCPU", data: batchVcpuPerTool, backgroundColor: blue, borderRadius: 4 },')
        h('    { label: "Memory", data: batchMemPerTool, backgroundColor: blueLight, borderRadius: 4 }')
        h('  ]}, options: { indexAxis: "y", responsive: true, plugins: { legend: { position: "top" }, tooltip: { callbacks: { label: dollarFmt2 } } }, scales: { x: { stacked: true, title: { display: true, text: "USD" }, beginAtZero: true }, y: { stacked: true } } } });')
        h('')

    if "pulsar" in wall_cloud:
        h('const pulsarVcpuPerTool = wPulsarCost.map(c => +(c * stdVcpuFrac * 0.93).toFixed(3));')
        h('const pulsarSsdPerTool = wPulsarCost.map(c => +(c * 0.07).toFixed(3));')
        h('const pulsarMemPerTool = wPulsarCost.map((c, i) => +(c - pulsarVcpuPerTool[i] - pulsarSsdPerTool[i]).toFixed(3));')
        h('new Chart(document.getElementById("pulsarBreakdownChart"), { type: "bar",')
        h('  data: { labels: toolsShort, datasets: [')
        h('    { label: "vCPU", data: pulsarVcpuPerTool, backgroundColor: amber, borderRadius: 4 },')
        h('    { label: "Memory", data: pulsarMemPerTool, backgroundColor: amberLight, borderRadius: 4 },')
        h('    { label: "Local SSD", data: pulsarSsdPerTool, backgroundColor: "#a78bfa", borderRadius: 4 }')
        h('  ]}, options: { indexAxis: "y", responsive: true, plugins: { legend: { position: "top" }, tooltip: { callbacks: { label: dollarFmt2 } } }, scales: { x: { stacked: true, title: { display: true, text: "USD" }, beginAtZero: true }, y: { stacked: true } } } });')
        h('')

    # VM-Hours Chart (wallclock)
    h('new Chart(document.getElementById("vmHoursChart"), { type: "bar",')
    h('  data: { labels: toolsShort, datasets: [')
    h('    { label: "Batch VM-hours", data: wBatchHours, backgroundColor: blue, borderRadius: 4 },')
    h('    { label: "Pulsar VM-hours", data: wPulsarHours, backgroundColor: amber, borderRadius: 4 }')
    h('  ]}, options: { responsive: true, plugins: { legend: { position: "top" }, tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.raw.toFixed(2)}h` } } }, scales: { y: { title: { display: true, text: "Hours" }, beginAtZero: true }, x: { ticks: { maxRotation: 45, minRotation: 45 } } } } });')
    h('')

    # Tab switching
    h('document.querySelectorAll(".tab").forEach(tab => {')
    h('  tab.addEventListener("click", () => {')
    h('    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));')
    h('    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));')
    h('    tab.classList.add("active");')
    h('    document.getElementById(tab.dataset.tab).classList.add("active");')
    h('  });')
    h('});')
    h('</script>')
    h('</body>')
    h('</html>')

    return "\n".join(html)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def derive_experiment_title(experiment_name):
    title = experiment_name
    for prefix in ["Pulsar-vs-Batch-", "Pulsar-vs-Batch"]:
        if title.startswith(prefix):
            title = title[len(prefix):]
            break
    if not title:
        title = "Variant Analysis"
    title = title.replace("-", " ")
    return title


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_experiment(jobs, experiment_name, docs_dir, no_rainstone=False):
    """Generate cost docs for a single experiment's jobs."""
    os.makedirs(docs_dir, exist_ok=True)

    ok_jobs, compute_cloud, compute_tool, wall_cloud, wall_tool, tool_order = aggregate_costs(jobs)
    print(f"  {len(ok_jobs)} ok jobs, {len(tool_order)} tools")
    print(f"  Tools: {', '.join(tool_order)}")

    # Date range from job timestamps
    all_creates = [j["create_time"] for j in ok_jobs]
    all_updates = [j["update_time"] for j in ok_jobs]
    date_range = (f"{min(all_creates)[:19].replace('T', ' ')} to "
                  f"{max(all_updates)[:19].replace('T', ' ')} UTC")

    # Galaxy VM cost: each cloud has its own Galaxy host VM running for the
    # duration of that cloud's experiment (first create to last update).
    galaxy_vm = {}
    for cloud in ["batch", "pulsar"]:
        cloud_jobs = [j for j in ok_jobs if j["cloud"] == cloud]
        if not cloud_jobs:
            continue
        creates = [datetime.fromisoformat(j["create_time"]) for j in cloud_jobs]
        updates = [datetime.fromisoformat(j["update_time"]) for j in cloud_jobs]
        duration_hours = (max(updates) - min(creates)).total_seconds() / 3600
        galaxy_vm[cloud] = {
            "hours": duration_hours,
            "cost": duration_hours * GALAXY_VM_HOURLY,
        }

    # Local single-VM model cost (n2-standard-20 for experiment duration)
    local_vm = {}
    for cloud in ["batch", "pulsar"]:
        if cloud in galaxy_vm:
            local_vm[cloud] = {
                "hours": galaxy_vm[cloud]["hours"],
                "cost": galaxy_vm[cloud]["hours"] * LOCAL_VM_HOURLY,
            }

    # Rainstone
    rainstone = {}
    if not no_rainstone:
        print("  Querying Rainstone API...")
        rainstone = fetch_all_rainstone(tool_order)
        print(f"  Got Rainstone data for {len(rainstone)}/{len(tool_order)} tools")

    # Generate Markdown
    md = generate_markdown(compute_cloud, compute_tool, wall_cloud, wall_tool,
                           tool_order, rainstone, experiment_name, date_range,
                           galaxy_vm, local_vm)
    md_path = os.path.join(docs_dir, "costs.md")
    with open(md_path, "w") as f:
        f.write(md)
    print(f"  Wrote {md_path}")

    # Generate HTML
    html = generate_html(compute_cloud, compute_tool, wall_cloud, wall_tool,
                         tool_order, rainstone, experiment_name,
                         galaxy_vm, local_vm)
    html_path = os.path.join(docs_dir, "cost-charts.html")
    with open(html_path, "w") as f:
        f.write(html)
    print(f"  Wrote {html_path}")

    # Summary
    for cloud in ["batch", "pulsar"]:
        if cloud in wall_cloud:
            wc = wall_cloud[cloud]
            cc = compute_cloud.get(cloud, {"total_cost": 0})
            print(f"  {cloud.title()}: ${wc['total_cost']:.2f} wallclock, "
                  f"${cc['total_cost']:.2f} compute "
                  f"({wc['jobs']} jobs, {wc['vm_hours']:.1f} VM-hours)")


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    parser = argparse.ArgumentParser(
        description="Generate cost analysis docs from metrics JSON files.")
    parser.add_argument("metrics_dir", nargs="?",
                        default=os.path.join(base_dir, "metrics", "Pulsar-vs-Batch"),
                        help="Directory containing metrics JSON files")
    parser.add_argument("--no-rainstone", action="store_true",
                        help="Skip Rainstone API queries")
    parser.add_argument("--exclude", action="append", default=[],
                        help="Exclude jobs whose inputs contain this string (repeatable)")
    args = parser.parse_args()

    metrics_dir = args.metrics_dir
    experiment_name = os.path.basename(metrics_dir)

    print(f"Loading metrics from {metrics_dir}...")
    jobs = load_metrics(metrics_dir)

    if args.exclude:
        before = len(jobs)
        jobs = [j for j in jobs
                if not any(pat in j.get("inputs", "") for pat in args.exclude)]
        excluded = before - len(jobs)
        if excluded:
            print(f"  Excluded {excluded} jobs matching: {', '.join(args.exclude)}")

    # Split into per-workflow experiments
    experiments = split_by_experiment(jobs)

    if len(experiments) == 1 and experiments[0][0] is None:
        # Single experiment
        docs_dir = os.path.join(base_dir, "docs", experiment_name)
        print(f"\n[{experiment_name}]")
        generate_experiment(jobs, experiment_name, docs_dir, args.no_rainstone)
    else:
        print(f"  Found {len(experiments)} experiments: "
              f"{', '.join(name for name, _ in experiments)}")
        for name, exp_jobs in experiments:
            docs_dir = os.path.join(base_dir, "docs", name)
            print(f"\n[{name}]")
            generate_experiment(exp_jobs, name, docs_dir, args.no_rainstone)


if __name__ == "__main__":
    main()
