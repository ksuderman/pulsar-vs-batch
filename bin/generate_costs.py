#!/usr/bin/env python3
"""Generate docs/costs.md and docs/cost-charts.html from metrics JSON files.

Usage:
    python3 bin/generate_costs.py [metrics_dir]

Supports any number of cloud runners. Queries the Rainstone API for
historical per-tool cost estimates from usegalaxy.org.
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
from datetime import datetime

# ---------------------------------------------------------------------------
# GCP pricing (us-east4)
# ---------------------------------------------------------------------------

VCPU_PER_HOUR = 0.031611
MEM_PER_GB_HOUR = 0.004237
SSD_PER_GB_HOUR = 0.000054
BOOT_DISK_PER_GB_MONTH = 0.10

PULSAR_SSD_GB = 375
BOOT_DISK_GB = 30

E2_VCPU_PER_HOUR = 0.02238
E2_MEM_PER_GB_HOUR = 0.003000
GALAXY_VM_VCPUS = 4
GALAXY_VM_MEM_GB = 16
GALAXY_VM_HOURLY = GALAXY_VM_VCPUS * E2_VCPU_PER_HOUR + GALAXY_VM_MEM_GB * E2_MEM_PER_GB_HOUR

LOCAL_VM_VCPUS = 20
LOCAL_VM_MEM_GB = 80
LOCAL_VM_HOURLY = LOCAL_VM_VCPUS * VCPU_PER_HOUR + LOCAL_VM_MEM_GB * MEM_PER_GB_HOUR

N2_STANDARD = {2: 8, 4: 16, 8: 32, 16: 64, 32: 128, 48: 192, 64: 256, 80: 320, 96: 384, 128: 512}

INPUT_SIZE_MAP = {
    "SRR24043307-80": "2GB", "SRR24043307-50": "5GB", "SRR24043307-full": "10GB",
    "chipseq-10g": "10GB", "chipseq-5g": "5GB", "chipseq-2g": "2GB",
}

CLOUD_COLORS = {
    "batch":  ("#3b82f6", "#93bbfd"),
    "pulsar": ("#f59e0b", "#fcd679"),
    "single": ("#22c55e", "#86efac"),
}
_EXTRA_COLORS = [("#8b5cf6", "#c4b5fd"), ("#ef4444", "#fca5a5")]


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
            elif m["name"] == "galaxy_slots":
                slots = float(m["raw_value"])
            elif m["name"] == "galaxy_memory_mb":
                mem = float(m["raw_value"])
        ct = datetime.fromisoformat(d["metrics"]["create_time"])
        ut = datetime.fromisoformat(d["metrics"]["update_time"])
        wallclock = max(0, (ut - ct).total_seconds())
        # Classify job runner from external_id
        ext_id = str(d["metrics"].get("external_id") or "")
        if ext_id.startswith("galaxy-job-") or ext_id.startswith("galaxy-single-"):
            job_runner = "gcp_batch"
        elif ext_id.startswith("galaxy-pulsar-") or ext_id.startswith("pulsar-"):
            job_runner = "gcp_batch"
        elif d["cloud"] == "pulsar" and ext_id.isdigit():
            # Pulsar uses numeric internal job IDs for GCP Batch jobs
            job_runner = "gcp_batch"
        elif ext_id.startswith("gxy-galaxy-"):
            job_runner = "k8s"
        elif ext_id.isdigit():
            job_runner = "local"
        else:
            job_runner = "local"

        jobs.append({
            "cloud": d["cloud"], "workflow_id": d.get("workflow_id", ""),
            "history_id": d.get("history_id", ""),
            "tool": tool, "state": d["metrics"]["state"],
            "runtime": runtime or 0, "wallclock": wallclock,
            "slots": slots or 0, "mem_mb": mem or 0,
            "inputs": d.get("inputs", ""),
            "create_time": d["metrics"]["create_time"],
            "update_time": d["metrics"]["update_time"],
            "job_runner": job_runner,
        })
    return jobs


def discover_clouds(jobs):
    return sorted(set(j["cloud"] for j in jobs))


def derive_experiment_title(name):
    title = name
    for prefix in ["Pulsar-vs-Batch-", "Pulsar-vs-Batch"]:
        if title.startswith(prefix):
            title = title[len(prefix):]
            break
    if not title:
        title = "Variant Analysis"
    return title.replace("-", " ")


# ---------------------------------------------------------------------------
# Cost computation
# ---------------------------------------------------------------------------

def compute_machine_type(slots, mem_mb):
    vcpus = max(2, int(slots)) if slots > 0 else 2
    for n2 in sorted(N2_STANDARD.keys()):
        if n2 >= vcpus:
            vcpus = n2
            break
    else:
        vcpus = max(N2_STANDARD.keys())
    mem_gb = N2_STANDARD[vcpus]
    if mem_mb > 0 and mem_mb / 1024 > mem_gb:
        mem_gb = vcpus * 8
    return vcpus, mem_gb


def _cost_for_duration(hours, vcpus, mem_gb, cloud):
    vcpu_cost = vcpus * VCPU_PER_HOUR * hours
    mem_cost = mem_gb * MEM_PER_GB_HOUR * hours
    ssd_cost = PULSAR_SSD_GB * SSD_PER_GB_HOUR * hours if cloud == "pulsar" else 0
    boot_cost = BOOT_DISK_GB * BOOT_DISK_PER_GB_MONTH / (30 * 24) * hours
    return {
        "vcpu_cost": vcpu_cost, "mem_cost": mem_cost,
        "ssd_cost": ssd_cost, "boot_cost": boot_cost,
        "total_cost": vcpu_cost + mem_cost + ssd_cost + boot_cost,
        "hours": hours,
    }


def _zero_cost(vcpus=0, mem_gb=0):
    return {"vcpu_cost": 0, "mem_cost": 0, "ssd_cost": 0, "boot_cost": 0,
            "total_cost": 0, "hours": 0, "vcpus": vcpus, "mem_gb": mem_gb}


def compute_job_cost(job):
    vcpus, mem_gb = compute_machine_type(job["slots"], job["mem_mb"])
    # Jobs on k8s or local runners cost $0 — covered by the cluster
    if job.get("job_runner") in ("k8s", "local"):
        return {"compute": _zero_cost(vcpus, mem_gb),
                "wallclock": _zero_cost(vcpus, mem_gb)}
    compute = _cost_for_duration(job["runtime"] / 3600, vcpus, mem_gb, job["cloud"])
    wallclock = _cost_for_duration(job["wallclock"] / 3600, vcpus, mem_gb, job["cloud"])
    compute["vcpus"] = vcpus; compute["mem_gb"] = mem_gb
    wallclock["vcpus"] = vcpus; wallclock["mem_gb"] = mem_gb
    return {"compute": compute, "wallclock": wallclock}


# ---------------------------------------------------------------------------
# Rainstone API
# ---------------------------------------------------------------------------

def fetch_rainstone(tool_id):
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
    results = {}
    for tid in tool_ids:
        data = fetch_rainstone(tid)
        if data:
            results[tid] = data
    return results


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def _empty_bucket():
    return {"jobs": 0, "total_cost": 0, "vcpus": 0, "hours": 0,
            "vcpu_cost": 0, "mem_cost": 0, "ssd_cost": 0, "boot_cost": 0}


def _aggregate_one(ok_jobs, cost_key):
    cloud_totals = {}
    for cloud in discover_clouds(ok_jobs):
        cj = [j for j in ok_jobs if j["cloud"] == cloud]
        cloud_totals[cloud] = {
            "jobs": len(cj),
            "vm_hours": sum(j["cost"][cost_key]["hours"] for j in cj),
            "vcpu_cost": sum(j["cost"][cost_key]["vcpu_cost"] for j in cj),
            "mem_cost": sum(j["cost"][cost_key]["mem_cost"] for j in cj),
            "ssd_cost": sum(j["cost"][cost_key]["ssd_cost"] for j in cj),
            "boot_cost": sum(j["cost"][cost_key]["boot_cost"] for j in cj),
            "total_cost": sum(j["cost"][cost_key]["total_cost"] for j in cj),
        }
    tool_data = defaultdict(lambda: defaultdict(_empty_bucket))
    for j in ok_jobs:
        td = tool_data[j["tool"]][j["cloud"]]
        c = j["cost"][cost_key]
        td["jobs"] += 1; td["total_cost"] += c["total_cost"]
        td["vcpus"] = max(td["vcpus"], c["vcpus"])
        td["hours"] += c["hours"]
        td["vcpu_cost"] += c["vcpu_cost"]; td["mem_cost"] += c["mem_cost"]
        td["ssd_cost"] += c["ssd_cost"]; td["boot_cost"] += c["boot_cost"]
    return cloud_totals, tool_data


def aggregate_costs(jobs):
    ok_jobs = [j for j in jobs if j["state"] == "ok"]
    for j in ok_jobs:
        j["cost"] = compute_job_cost(j)
    compute_cloud, compute_tool = _aggregate_one(ok_jobs, "compute")
    wall_cloud, wall_tool = _aggregate_one(ok_jobs, "wallclock")
    all_tools = set(compute_tool.keys()) | set(wall_tool.keys())
    tool_order = sorted(all_tools,
                        key=lambda t: sum(wall_tool[t][c]["total_cost"] for c in wall_tool[t]),
                        reverse=True)
    return ok_jobs, compute_cloud, compute_tool, wall_cloud, wall_tool, tool_order


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def _runner_table(w, cloud_totals, clouds):
    w("| Runner | Jobs | VM-Hours | vCPU Cost | Memory Cost | SSD Cost | Boot Disk | Total Cost |")
    w("|--------|------|----------|-----------|-------------|----------|-----------|------------|")
    grand = defaultdict(float)
    for cloud in clouds:
        if cloud not in cloud_totals:
            continue
        ct = cloud_totals[cloud]
        w(f"| **{cloud.title()}** | {ct['jobs']} | {ct['vm_hours']:.1f}h | "
          f"${ct['vcpu_cost']:.2f} | ${ct['mem_cost']:.2f} | "
          f"${ct['ssd_cost']:.2f} | ${ct['boot_cost']:.2f} | "
          f"**${ct['total_cost']:.2f}** |")
        for k in ["jobs", "vm_hours", "vcpu_cost", "mem_cost", "ssd_cost", "boot_cost", "total_cost"]:
            grand[k] += ct[k]
    w(f"| **Total** | {int(grand['jobs'])} | {grand['vm_hours']:.1f}h | "
      f"${grand['vcpu_cost']:.2f} | ${grand['mem_cost']:.2f} | "
      f"${grand['ssd_cost']:.2f} | ${grand['boot_cost']:.2f} | "
      f"**${grand['total_cost']:.2f}** |")
    return dict(grand)


def generate_markdown(compute_cloud, compute_tool, wall_cloud, wall_tool,
                      tool_order, rainstone, experiment_name, date_range,
                      galaxy_vm, local_vm, clouds):
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
    w(f"**[Home](../index.html)** | "
      f"**[Interactive Cost Charts](cost-charts.html)** | "
      f"**[Performance Report](index.html)** | "
      f"**[Performance Charts](charts.html)**")
    w("")
    w(f"**Period:** {date_range}  ")
    w(f"**Region:** us-east4  ")
    w(f"**Total Jobs:** {total_jobs} (ok)")
    w("")

    # Wallclock costs
    w("## Estimated Cost (Wallclock)")
    w("")
    w("Cost based on total VM lifetime per job (Galaxy create_time to update_time), "
      "including VM provisioning, image pull, file staging, compute, and shutdown.")
    w("")
    _runner_table(w, wall_cloud, clouds)
    w("")

    # Galaxy VM cost
    if galaxy_vm:
        w("### Galaxy Host VM Cost")
        w("")
        w("Each runner requires a Galaxy host VM (e2-standard-4, 4 vCPU, 16 GB). "
          "Duration is summed per-run (per workflow invocation), not the full experiment window.")
        w("")
        w("| Runner | Duration | Galaxy VM Cost |")
        w("|--------|----------|----------------|")
        for cloud in clouds:
            if cloud in galaxy_vm:
                gv = galaxy_vm[cloud]
                w(f"| **{cloud.title()}** | {gv['hours']:.1f}h | ${gv['cost']:.2f} |")
        w("")

    # Total cost
    if galaxy_vm:
        w("### Total Estimated Cost (Batch Jobs + Galaxy VM)")
        w("")
        w("| Runner | Job Cost | Galaxy VM Cost | **Total** |")
        w("|--------|----------|----------------|-----------|")
        for cloud in clouds:
            if cloud in wall_cloud and cloud in galaxy_vm:
                jc = wall_cloud[cloud]["total_cost"]
                gc = galaxy_vm[cloud]["cost"]
                w(f"| **{cloud.title()}** | ${jc:.2f} | ${gc:.2f} | **${jc + gc:.2f}** |")
        w("")

    # Compute-only costs
    w("## Compute-Only Cost (cgroups)")
    w("")
    w("Cost based on cgroups `runtime_seconds` — actual CPU time inside the container.")
    w("")
    _runner_table(w, compute_cloud, clouds)
    w("")

    # Overhead ratio
    w("### Wallclock vs Compute Overhead")
    w("")
    w("| Runner | Compute Cost | Wallclock Cost | Overhead Ratio |")
    w("|--------|-------------|----------------|----------------|")
    for cloud in clouds:
        if cloud in compute_cloud and cloud in wall_cloud:
            cc = compute_cloud[cloud]["total_cost"]
            wc = wall_cloud[cloud]["total_cost"]
            ratio = wc / cc if cc > 0 else 0
            w(f"| **{cloud.title()}** | ${cc:.2f} | ${wc:.2f} | {ratio:.1f}x |")
    w("")

    # Per-tool wallclock
    w("## Per-Tool Cost Comparison (Wallclock)")
    w("")
    header = "| Tool | vCPU |"
    sep = "|------|------|"
    for cloud in clouds:
        header += f" {cloud.title()} Jobs | {cloud.title()} Cost | {cloud.title()} $/Job |"
        sep += " ---- | ---- | ---- |"
    header += " Rainstone Est. |"
    sep += " ---- |"
    w(header)
    w(sep)
    for tool in tool_order:
        vcpus = max((wall_tool[tool].get(c, _empty_bucket()).get("vcpus", 0) for c in clouds), default=0)
        row = f"| {tool} | {vcpus} |"
        for cloud in clouds:
            td = wall_tool[tool].get(cloud, _empty_bucket())
            per = td["total_cost"] / td["jobs"] if td["jobs"] > 0 else 0
            row += f" {td['jobs']} | ${td['total_cost']:.2f} | ${per:.4f} |"
        r_est = f"${rainstone[tool]['avg']:.4f}" if tool in rainstone else "--"
        row += f" {r_est} |"
        w(row)
    w("")

    # Rainstone comparison (compute costs)
    if rainstone:
        w("## Rainstone Comparison")
        w("")
        w("Per-job compute cost comparison against "
          "[Rainstone](https://rainstone.anvilproject.org) "
          "historical averages from usegalaxy.org. Rainstone data reflects median costs "
          "across thousands of production runs.")
        w("")
        header = "| Tool |"
        sep = "|------|"
        for cloud in clouds:
            header += f" {cloud.title()} $/Job |"
            sep += " ---- |"
        header += " Rainstone Avg | Rainstone Median | Rainstone P95 | usegalaxy.org Jobs |"
        sep += " ---- | ---- | ---- | ---- |"
        w(header)
        w(sep)
        for tool in tool_order:
            row = f"| {tool} |"
            for cloud in clouds:
                td = compute_tool[tool].get(cloud, _empty_bucket())
                per = td["total_cost"] / td["jobs"] if td["jobs"] > 0 else 0
                row += f" ${per:.4f} |"
            if tool in rainstone:
                r = rainstone[tool]
                row += f" ${r['avg']:.4f} | ${r['median']:.4f} | ${r['p95']:.4f} | {r['num_jobs']:,} |"
            else:
                row += " -- | -- | -- | -- |"
            w(row)
        w("")

    # Deployment model comparison
    if local_vm and galaxy_vm:
        w("## Deployment Model Comparison")
        w("")
        w("GCP Batch approach (Galaxy + per-job VMs) vs traditional deployment "
          "(single n2-standard-20 VM running for the experiment duration).")
        w("")
        w("| Model | Runner | Duration | Job Cost | Galaxy VM | **Total** |")
        w("|-------|--------|----------|----------|-----------|-----------|")
        for cloud in clouds:
            if cloud not in wall_cloud or cloud not in galaxy_vm:
                continue
            jc = wall_cloud[cloud]["total_cost"]
            gc = galaxy_vm[cloud]["cost"]
            lc = local_vm[cloud]["cost"]
            dur = galaxy_vm[cloud]["hours"]
            w(f"| **GCP Batch** | {cloud.title()} | {dur:.1f}h | ${jc:.2f} | ${gc:.2f} | **${jc + gc:.2f}** |")
            w(f"| **Local VM** | {cloud.title()} | {dur:.1f}h | -- | ${lc:.2f} | **${lc:.2f}** |")
        w("")
        for cloud in clouds:
            if cloud not in wall_cloud or cloud not in galaxy_vm:
                continue
            batch_total = wall_cloud[cloud]["total_cost"] + galaxy_vm[cloud]["cost"]
            lv = local_vm[cloud]["cost"]
            if lv > 0:
                ratio = batch_total / lv
                cheaper = "cheaper" if ratio < 1 else "more expensive"
                pct = abs(1 - ratio) * 100
                w(f"**{cloud.title()}**: GCP Batch is **{pct:.0f}% {cheaper}** "
                  f"than a local n2-standard-20 (${batch_total:.2f} vs ${lv:.2f}).")
        w("")

    # Pricing assumptions
    w("## Pricing Assumptions")
    w("")
    w("All costs estimated using GCP on-demand pricing for `us-east4`.")
    w("")
    w("| Resource | Rate |")
    w("|----------|------|")
    w(f"| N2 vCPU | ${VCPU_PER_HOUR}/vCPU/hour |")
    w(f"| N2 Memory | ${MEM_PER_GB_HOUR}/GB/hour |")
    w(f"| Local SSD | ${SSD_PER_GB_HOUR}/GB/hour |")
    w(f"| Boot Disk (pd-balanced) | ${BOOT_DISK_PER_GB_MONTH}/GB/month |")
    w(f"| Galaxy VM (e2-standard-4) | ${GALAXY_VM_HOURLY:.4f}/hour |")
    w(f"| Local n2-standard-20 | ${LOCAL_VM_HOURLY:.4f}/hour |")
    w("")
    if rainstone:
        w("Rainstone estimates are sourced from the "
          "[Rainstone Cost API](https://rainstone.anvilproject.org/api/docs) "
          "and reflect historical averages across usegalaxy.org production workloads.")
        w("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML chart generation
# ---------------------------------------------------------------------------

def generate_html(compute_cloud, compute_tool, wall_cloud, wall_tool,
                  tool_order, rainstone, experiment_name, galaxy_vm, clouds):
    workflow_title = derive_experiment_title(experiment_name)
    total_jobs = sum(ct["jobs"] for ct in wall_cloud.values())

    tools_json = json.dumps(tool_order)
    tools_short = [t[:12] if len(t) > 12 else t for t in tool_order]
    tools_short_json = json.dumps(tools_short)

    # Assign colors
    cc = {}
    extra_idx = 0
    for c in clouds:
        if c in CLOUD_COLORS:
            cc[c] = CLOUD_COLORS[c]
        else:
            cc[c] = _EXTRA_COLORS[extra_idx % len(_EXTRA_COLORS)]
            extra_idx += 1

    # Per-tool arrays
    def _arrays(tool_data):
        result = {}
        for cloud in clouds:
            cost, per_job, hours = [], [], []
            for tool in tool_order:
                td = tool_data[tool].get(cloud, _empty_bucket())
                cost.append(round(td["total_cost"], 2))
                per_job.append(round(td["total_cost"] / td["jobs"], 4) if td["jobs"] > 0 else 0)
                hours.append(round(td["hours"], 2))
            result[cloud] = {"cost": cost, "per_job": per_job, "hours": hours}
        return result

    w_arr = _arrays(wall_tool)
    c_arr = _arrays(compute_tool)

    r_avg = [round(rainstone.get(t, {}).get("avg", 0), 4) for t in tool_order]
    r_median = [round(rainstone.get(t, {}).get("median", 0), 4) for t in tool_order]
    r_p95 = [round(rainstone.get(t, {}).get("p95", 0), 4) for t in tool_order]

    _empty_ct = {"vcpu_cost": 0, "mem_cost": 0, "ssd_cost": 0, "boot_cost": 0, "total_cost": 0, "jobs": 0, "vm_hours": 0}

    html = []
    h = html.append

    h('<!DOCTYPE html>')
    h('<html lang="en"><head>')
    h('<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">')
    h(f'<title>{workflow_title}: Cost Analysis</title>')
    h('<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>')
    h('<style>')
    h('* { box-sizing: border-box; margin: 0; padding: 0; }')
    h('body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f7fa; color: #1a1a2e; padding: 2rem; max-width: 1200px; margin: 0 auto; }')
    h('h1 { font-size: 1.8rem; margin-bottom: 0.3rem; }')
    h('.subtitle { color: #666; font-size: 0.95rem; margin-bottom: 1.5rem; }')
    h('.nav { display: flex; gap: 1.5rem; margin-bottom: 1.5rem; font-size: 0.9rem; }')
    h('.nav a { color: #3b82f6; text-decoration: none; }')
    h('.tabs { display: flex; gap: 0; margin-bottom: 2rem; border-bottom: 2px solid #e5e7eb; flex-wrap: wrap; }')
    h('.tab { padding: 0.7rem 1.4rem; cursor: pointer; font-size: 0.9rem; font-weight: 500; color: #666; border-bottom: 2px solid transparent; margin-bottom: -2px; user-select: none; }')
    h('.tab:hover { color: #1a1a2e; }')
    h('.tab.active { color: #3b82f6; border-bottom-color: #3b82f6; }')
    h('.tab-content { display: none; }')
    h('.tab-content.active { display: block; }')
    h('.summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }')
    h('.card { background: #fff; border-radius: 10px; padding: 1.2rem 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }')
    h('.card .label { font-size: 0.8rem; color: #888; text-transform: uppercase; }')
    h('.card .value { font-size: 1.8rem; font-weight: 700; margin-top: 0.2rem; }')
    h('.card .detail { font-size: 0.85rem; color: #666; margin-top: 0.2rem; }')
    h('.chart-container { background: #fff; border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }')
    h('.chart-container h2 { font-size: 1.1rem; margin-bottom: 0.3rem; }')
    h('.chart-container .chart-desc { font-size: 0.85rem; color: #888; margin-bottom: 1rem; }')
    h('.footer { text-align: center; color: #aaa; font-size: 0.8rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; }')
    h('</style></head><body>')
    h('')
    h(f'<h1>{workflow_title}: Cost Analysis</h1>')
    h(f'<p class="subtitle">{total_jobs} jobs &mdash; {len(tool_order)} tools &mdash; {", ".join(c.title() for c in clouds)}</p>')
    h('<div class="nav">')
    h('  <a href="../index.html">&larr; Home</a>')
    h('  <a href="index.html">Results Report</a>')
    h('  <a href="charts.html">Performance Charts</a>')
    h('  <a href="costs.html">Cost Tables</a>')
    h('</div>')
    h('')

    h('<div class="tabs">')
    h('  <div class="tab active" data-tab="overview">Overview</div>')
    h('  <div class="tab" data-tab="per-tool-wall">Per-Tool (Wallclock)</div>')
    h('  <div class="tab" data-tab="per-tool-compute">Per-Tool (Compute)</div>')
    if rainstone:
        h('  <div class="tab" data-tab="rainstone">Rainstone</div>')
    h('</div>')
    h('')

    # Overview tab
    h('<div class="tab-content active" id="overview">')
    h('  <div class="summary-cards">')
    for cloud in clouds:
        wc = wall_cloud.get(cloud, _empty_ct)
        coc = compute_cloud.get(cloud, _empty_ct)
        color = cc[cloud][0]
        h(f'    <div class="card"><div class="label" style="color:{color}">{cloud.title()}</div>'
          f'<div class="value" style="color:{color}">${wc["total_cost"]:.2f}</div>'
          f'<div class="detail">{wc["jobs"]} jobs &middot; compute: ${coc["total_cost"]:.2f}</div></div>')
    h('  </div>')
    h('  <div class="chart-container">')
    h('    <h2>Wallclock vs Compute Cost</h2>')
    h('    <p class="chart-desc">Grouped bars: what the CPU used vs what you pay.</p>')
    h('    <canvas id="wallVsCompute" height="60"></canvas>')
    h('  </div>')
    h('  <div class="chart-container">')
    h('    <h2>VM-Hours by Tool (Wallclock)</h2>')
    h('    <p class="chart-desc">Total billed VM-hours per tool.</p>')
    h('    <canvas id="vmHoursChart" height="100"></canvas>')
    h('  </div>')
    h('</div>')

    # Per-tool wallclock tab
    h('<div class="tab-content" id="per-tool-wall">')
    h('  <div class="chart-container"><h2>Per-Tool Wallclock Cost</h2>')
    h('    <p class="chart-desc">Total wallclock cost per tool.</p>')
    h('    <canvas id="perToolWall" height="100"></canvas></div>')
    h('  <div class="chart-container"><h2>Per-Job Wallclock Cost</h2>')
    h('    <p class="chart-desc">Average wallclock cost per job.</p>')
    h('    <canvas id="perJobWall" height="100"></canvas></div>')
    h('</div>')

    # Per-tool compute tab
    h('<div class="tab-content" id="per-tool-compute">')
    h('  <div class="chart-container"><h2>Per-Tool Compute Cost</h2>')
    h('    <p class="chart-desc">Cost based on cgroups runtime only.</p>')
    h('    <canvas id="perToolComp" height="100"></canvas></div>')
    h('  <div class="chart-container"><h2>Per-Job Compute Cost</h2>')
    h('    <p class="chart-desc">Average compute cost per job.</p>')
    h('    <canvas id="perJobComp" height="100"></canvas></div>')
    h('</div>')

    # Rainstone tab
    if rainstone:
        h('<div class="tab-content" id="rainstone">')
        h('  <div class="chart-container"><h2>Compute Cost vs Rainstone (usegalaxy.org)</h2>')
        h('    <p class="chart-desc">Per-job compute cost vs Rainstone historical averages. Log scale.</p>')
        h('    <canvas id="rainstoneChart" height="120"></canvas></div>')
        h('</div>')

    h(f'<div class="footer">Galaxy 26.1 &middot; us-east4 &middot; {total_jobs} jobs &middot; Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>')

    # JavaScript
    h('<script>')
    h('Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif";')
    h('Chart.defaults.font.size = 12;')
    h(f'const tools = {tools_json};')
    h(f'const toolsShort = {tools_short_json};')
    h('const dollarFmt = ctx => `$${ctx.raw.toFixed(4)}`;')
    h('')

    # Emit data arrays
    for cloud in clouds:
        csafe = re.sub(r'[^a-zA-Z0-9]', '_', cloud)
        h(f'const w_{csafe}_cost = {json.dumps(w_arr[cloud]["cost"])};')
        h(f'const w_{csafe}_pj = {json.dumps(w_arr[cloud]["per_job"])};')
        h(f'const w_{csafe}_hrs = {json.dumps(w_arr[cloud]["hours"])};')
        h(f'const c_{csafe}_cost = {json.dumps(c_arr[cloud]["cost"])};')
        h(f'const c_{csafe}_pj = {json.dumps(c_arr[cloud]["per_job"])};')
    if rainstone:
        h(f'const rainstoneAvg = {json.dumps(r_avg)};')
    h('')

    # Wallclock vs Compute overview
    cloud_labels = json.dumps([c.title() for c in clouds])
    comp_vals = json.dumps([round(compute_cloud.get(c, _empty_ct)["total_cost"], 2) for c in clouds])
    wall_vals = json.dumps([round(wall_cloud.get(c, _empty_ct)["total_cost"], 2) for c in clouds])
    comp_colors = json.dumps([cc[c][1] for c in clouds])
    wall_colors = json.dumps([cc[c][0] for c in clouds])
    h(f'new Chart(document.getElementById("wallVsCompute"), {{ type: "bar", data: {{ labels: {cloud_labels}, datasets: [')
    h(f'  {{ label: "Compute", data: {comp_vals}, backgroundColor: {comp_colors}, borderRadius: 4 }},')
    h(f'  {{ label: "Wallclock", data: {wall_vals}, backgroundColor: {wall_colors}, borderRadius: 4 }}')
    h(f'] }}, options: {{ responsive: true, plugins: {{ tooltip: {{ callbacks: {{ label: ctx => `${{ctx.dataset.label}}: $${{ctx.raw.toFixed(2)}}` }} }} }}, scales: {{ y: {{ title: {{ display: true, text: "USD" }}, beginAtZero: true }} }} }} }});')
    h('')

    # VM-Hours chart
    h(f'new Chart(document.getElementById("vmHoursChart"), {{ type: "bar", data: {{ labels: toolsShort, datasets: [')
    for cloud in clouds:
        csafe = re.sub(r'[^a-zA-Z0-9]', '_', cloud)
        color = cc[cloud][0]
        h(f'  {{ label: "{cloud.title()}", data: w_{csafe}_hrs, backgroundColor: "{color}", borderRadius: 4 }},')
    h(f'] }}, options: {{ responsive: true, plugins: {{ legend: {{ position: "top" }} }}, scales: {{ y: {{ title: {{ display: true, text: "Hours" }}, beginAtZero: true }}, x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }} }} }} }});')
    h('')

    # Per-tool wallclock charts
    for suffix, data_key in [("Wall", "w"), ("Comp", "c")]:
        for chart_type, arr_suffix, ylabel in [("perTool", "cost", "USD"), ("perJob", "pj", "USD per job")]:
            chart_id = f"{chart_type}{suffix}"
            tooltip = 'ctx => `${ctx.dataset.label}: $${ctx.raw.toFixed(4)}`' if "pj" in arr_suffix else 'ctx => `${ctx.dataset.label}: $${ctx.raw.toFixed(2)}`'
            h(f'new Chart(document.getElementById("{chart_id}"), {{ type: "bar", data: {{ labels: toolsShort, datasets: [')
            for cloud in clouds:
                csafe = re.sub(r'[^a-zA-Z0-9]', '_', cloud)
                color = cc[cloud][0]
                h(f'  {{ label: "{cloud.title()}", data: {data_key}_{csafe}_{arr_suffix}, backgroundColor: "{color}", borderRadius: 4 }},')
            h(f'] }}, options: {{ responsive: true, plugins: {{ legend: {{ position: "top" }}, tooltip: {{ callbacks: {{ label: {tooltip} }} }} }}, scales: {{ y: {{ title: {{ display: true, text: "{ylabel}" }}, beginAtZero: true }}, x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }} }} }} }});')
            h('')

    # Rainstone chart
    if rainstone:
        h(f'new Chart(document.getElementById("rainstoneChart"), {{ type: "bar", data: {{ labels: toolsShort, datasets: [')
        for cloud in clouds:
            csafe = re.sub(r'[^a-zA-Z0-9]', '_', cloud)
            color = cc[cloud][0]
            h(f'  {{ label: "{cloud.title()}", data: c_{csafe}_pj, backgroundColor: "{color}", borderRadius: 4 }},')
        h(f'  {{ label: "Rainstone Avg", data: rainstoneAvg, backgroundColor: "#8b5cf6", borderRadius: 4 }}')
        h(f'] }}, options: {{ responsive: true, plugins: {{ tooltip: {{ callbacks: {{ label: dollarFmt }} }} }}, scales: {{ y: {{ type: "logarithmic", title: {{ display: true, text: "USD per job (log)" }} }}, x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }} }} }} }});')
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
    h('</script></body></html>')

    return "\n".join(html)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_experiment(jobs, experiment_name, docs_dir, no_rainstone=False):
    os.makedirs(docs_dir, exist_ok=True)

    ok_jobs, compute_cloud, compute_tool, wall_cloud, wall_tool, tool_order = aggregate_costs(jobs)
    clouds = sorted(wall_cloud.keys())
    print(f"  {len(ok_jobs)} ok jobs, {len(tool_order)} tools")
    print(f"  Clouds: {', '.join(clouds)}")
    print(f"  Tools: {', '.join(tool_order)}")

    all_creates = [j["create_time"] for j in ok_jobs]
    all_updates = [j["update_time"] for j in ok_jobs]
    date_range = (f"{min(all_creates)[:19].replace('T', ' ')} to "
                  f"{max(all_updates)[:19].replace('T', ' ')} UTC")

    # Galaxy VM cost per cloud (summed per-run durations)
    galaxy_vm = {}
    for cloud in clouds:
        cloud_jobs = [j for j in ok_jobs if j["cloud"] == cloud]
        if not cloud_jobs:
            continue
        by_history = defaultdict(list)
        for j in cloud_jobs:
            by_history[j.get("history_id", "")].append(j)
        total_hours = 0
        for hist_jobs in by_history.values():
            creates = [datetime.fromisoformat(j["create_time"]) for j in hist_jobs]
            updates = [datetime.fromisoformat(j["update_time"]) for j in hist_jobs]
            total_hours += (max(updates) - min(creates)).total_seconds() / 3600
        galaxy_vm[cloud] = {"hours": total_hours, "cost": total_hours * GALAXY_VM_HOURLY}

    local_vm = {}
    for cloud in clouds:
        if cloud in galaxy_vm:
            local_vm[cloud] = {"hours": galaxy_vm[cloud]["hours"],
                               "cost": galaxy_vm[cloud]["hours"] * LOCAL_VM_HOURLY}

    # Rainstone
    rainstone = {}
    if not no_rainstone:
        print("  Querying Rainstone API...")
        rainstone = fetch_all_rainstone(tool_order)
        print(f"  Got Rainstone data for {len(rainstone)}/{len(tool_order)} tools")

    md = generate_markdown(compute_cloud, compute_tool, wall_cloud, wall_tool,
                           tool_order, rainstone, experiment_name, date_range,
                           galaxy_vm, local_vm, clouds)
    md_path = os.path.join(docs_dir, "costs.md")
    with open(md_path, "w") as f:
        f.write(md)
    print(f"  Wrote {md_path}")

    html = generate_html(compute_cloud, compute_tool, wall_cloud, wall_tool,
                         tool_order, rainstone, experiment_name, galaxy_vm, clouds)
    html_path = os.path.join(docs_dir, "cost-charts.html")
    with open(html_path, "w") as f:
        f.write(html)
    print(f"  Wrote {html_path}")

    for cloud in clouds:
        if cloud in wall_cloud:
            wc = wall_cloud[cloud]
            coc = compute_cloud.get(cloud, {"total_cost": 0})
            print(f"  {cloud.title()}: ${wc['total_cost']:.2f} wallclock, "
                  f"${coc['total_cost']:.2f} compute ({wc['jobs']} jobs)")


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description="Generate cost analysis from metrics.")
    parser.add_argument("metrics_dir", nargs="?",
                        default=os.path.join(base_dir, "metrics", "Pulsar-vs-Batch"),
                        help="Directory containing metrics JSON files")
    parser.add_argument("--no-rainstone", action="store_true")
    parser.add_argument("--exclude", action="append", default=[])
    args = parser.parse_args()

    metrics_dir = args.metrics_dir
    experiment_name = os.path.basename(metrics_dir)

    print(f"Loading metrics from {metrics_dir}...")
    jobs = load_metrics(metrics_dir)

    if args.exclude:
        before = len(jobs)
        jobs = [j for j in jobs if not any(pat in j.get("inputs", "") for pat in args.exclude)]
        excluded = before - len(jobs)
        if excluded:
            print(f"  Excluded {excluded} jobs matching: {', '.join(args.exclude)}")

    docs_dir = os.path.join(base_dir, "docs", experiment_name)
    print(f"\n[{experiment_name}]")
    generate_experiment(jobs, experiment_name, docs_dir, args.no_rainstone)


if __name__ == "__main__":
    main()
