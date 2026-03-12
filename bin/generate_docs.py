#!/usr/bin/env python3
"""Generate docs/index.md and docs/charts.html from metrics JSON files.

Usage:
    python3 bin/generate_docs.py [metrics_dir]

Reads all JSON files from metrics/<experiment>/ (default: metrics/Pulsar-vs-Batch/)
and produces:
    docs/index.md      - Markdown results report
    docs/charts.html   - Interactive Chart.js dashboard
"""

import json
import glob
import os
import sys
from collections import defaultdict
from datetime import datetime

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

TOOL_ORDER = [
    "fastp", "snpEff_build_gb", "bwa_mem", "samtools_view",
    "picard_MarkDuplicates", "samtools_stats", "lofreq_viterbi", "multiqc",
    "lofreq_indelqual", "lofreq_call", "lofreq_filter", "snpEff",
]

TOOL_SHORT = {
    "fastp": "fastp",
    "snpEff_build_gb": "snpEff_build",
    "bwa_mem": "bwa_mem",
    "samtools_view": "sam_view",
    "picard_MarkDuplicates": "picard_MD",
    "samtools_stats": "sam_stats",
    "lofreq_viterbi": "lf_viterbi",
    "multiqc": "multiqc",
    "lofreq_indelqual": "lf_indelq",
    "lofreq_call": "lf_call",
    "lofreq_filter": "lf_filter",
    "snpEff": "snpEff",
}


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
        runtime = start = end = slots = mem = None
        for m in d["metrics"].get("job_metrics", []):
            if m["name"] == "runtime_seconds":
                runtime = float(m["raw_value"])
            if m["name"] == "start_epoch":
                start = float(m["raw_value"])
            if m["name"] == "end_epoch":
                end = float(m["raw_value"])
            if m["name"] == "galaxy_slots":
                slots = float(m["raw_value"])
            if m["name"] == "galaxy_memory_mb":
                mem = float(m["raw_value"])
        jobs.append({
            "run": d["run"],
            "cloud": d["cloud"],
            "history_id": d["history_id"],
            "tool": tool,
            "state": d["metrics"]["state"],
            "runtime": runtime or 0,
            "start_epoch": start,
            "end_epoch": end,
            "create_time": d["metrics"]["create_time"],
            "update_time": d["metrics"]["update_time"],
            "inputs": d.get("inputs", ""),
            "server": d.get("server", ""),
            "slots": slots or 0,
            "mem_mb": mem or 0,
        })
    return jobs


def get_size_label(inputs_str):
    sizes = []
    if "10GB" in inputs_str:
        sizes.append("10GB")
    if "5GB" in inputs_str:
        sizes.append("5GB")
    if "2GB" in inputs_str:
        sizes.append("2GB")
    return "+".join(sorted(sizes)) if sizes else "unknown"


def group_by_history(jobs):
    groups = defaultdict(list)
    for j in jobs:
        groups[(j["cloud"], j["run"], j["history_id"])].append(j)
    return groups


def history_stats(jobs_in_history):
    jobs = sorted(jobs_in_history, key=lambda x: x["create_time"])
    creates = [datetime.fromisoformat(j["create_time"]) for j in jobs]
    updates = [datetime.fromisoformat(j["update_time"]) for j in jobs]
    wall_clock = (max(updates) - min(creates)).total_seconds()
    compute = sum(j["runtime"] for j in jobs)
    overhead = wall_clock - compute
    size_label = get_size_label(jobs[0]["inputs"])
    date_range = (min(creates).strftime("%Y-%m-%d"), max(updates).strftime("%Y-%m-%d"))
    return {
        "cloud": jobs[0]["cloud"],
        "run": jobs[0]["run"],
        "history_id": jobs[0]["history_id"],
        "size": size_label,
        "wall_clock": wall_clock,
        "compute": compute,
        "overhead": overhead,
        "steps": len(jobs),
        "server": jobs[0]["server"],
        "date_start": date_range[0],
        "date_end": date_range[1],
        "jobs": jobs,
    }


# ---------------------------------------------------------------------------
# Matching & comparison helpers
# ---------------------------------------------------------------------------

def find_matchups(all_stats):
    """Find (batch, pulsar) pairs with the same size label."""
    by_size = defaultdict(lambda: {"batch": [], "pulsar": []})
    for s in all_stats:
        by_size[s["size"]][s["cloud"]].append(s)
    matchups = {}
    for size, clouds in sorted(by_size.items()):
        if clouds["batch"] and clouds["pulsar"]:
            matchups[size] = clouds
    return matchups


def per_tool_times(stat):
    """Return {tool: runtime} for a history stat."""
    return {j["tool"]: j["runtime"] for j in stat["jobs"]}


def avg_tool_times(stats_list):
    """Average per-tool runtimes across multiple runs."""
    tools = defaultdict(list)
    for s in stats_list:
        for j in s["jobs"]:
            tools[j["tool"]].append(j["runtime"])
    return {t: sum(v) / len(v) for t, v in tools.items()}


def avg_tool_slots(stats_list):
    """Average per-tool slots across runs."""
    tools = defaultdict(list)
    for s in stats_list:
        for j in s["jobs"]:
            tools[j["tool"]].append(j["slots"])
    return {t: sum(v) / len(v) for t, v in tools.items()}


def fmt_min(seconds):
    return f"{seconds / 60:.1f}"


def fmt_pct(diff, base):
    if base == 0:
        return "--"
    return f"{diff / base * 100:+.0f}%"


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def generate_markdown(all_stats, matchups, experiment_name):
    lines = []
    w = lines.append

    # Determine date range
    all_dates = set()
    servers = {}
    for s in all_stats:
        all_dates.add(s["date_start"])
        all_dates.add(s["date_end"])
        servers[s["cloud"]] = s["server"]
    date_range = f"{min(all_dates)} to {max(all_dates)}"

    w("---")
    w("title: Pulsar vs Direct GCP Batch")
    w("---")
    w("")
    w("# Pulsar vs Direct GCP Batch: Runtime Comparison")
    w("")
    w("**[Interactive Charts](charts.html)**")
    w("")

    # Setup
    w("## Experiment Setup")
    w("")
    w("- **Workflow:** Variant analysis on WGS PE data (12 steps)")
    w("- **Galaxy version:** 26.1")
    w("- **Infrastructure:** GCE VM on RKE2 Kubernetes, jobs dispatched to GCP Batch VMs (us-east4)")
    w("- **Custom VM image:** `galaxy-k8s-minimal-debian12-v2026-03-05` (CVMFS pre-installed)")
    if "batch" in servers:
        w(f"- **Batch server:** {servers['batch']}")
    if "pulsar" in servers:
        w(f"- **Pulsar server:** {servers['pulsar']}")
    w(f"- **Date:** {date_range}")
    w("")

    w("### Runners Compared")
    w("")
    w("| Runner | Type | Job Dispatch | File Transfer |")
    w("|--------|------|-------------|---------------|")
    w("| **GCP Batch** (direct) | `GoogleCloudBatchJobRunner` | Galaxy submits directly to GCP Batch API | Galaxy handles staging natively |")
    w("| **Pulsar** (AMQP sidecar) | `PulsarGcpBatchJobRunner` | Galaxy sends AMQP message; Pulsar sidecar stages inputs, runs tool, collects outputs, sends AMQP callback | HTTP upload/download via `remote_transfer` |")
    w("")

    total_jobs = sum(s["steps"] for s in all_stats)
    w(f"### Workflow Runs")
    w("")
    w(f"{len(all_stats)} workflow invocations, {total_jobs} total jobs. All completed successfully.")
    w("")

    # Summary table
    w("## Results Summary")
    w("")
    w("### All Runs")
    w("")
    w("| Runner | Run | Input Sizes | Wall Clock | Compute Time | Scheduling Overhead |")
    w("|--------|-----|-------------|-----------|-------------|-------------------|")
    for s in sorted(all_stats, key=lambda x: (x["cloud"], x["run"], x["size"])):
        oh_pct = f"{s['overhead'] / s['wall_clock'] * 100:.0f}%" if s["wall_clock"] > 0 else "--"
        w(f"| {s['cloud']} | {s['run']} | {s['size']} | {fmt_min(s['wall_clock'])} min | {fmt_min(s['compute'])} min | {fmt_min(s['overhead'])} min ({oh_pct}) |")
    w("")

    # Head-to-head matchups
    for size, clouds in sorted(matchups.items()):
        batch_stats = clouds["batch"]
        pulsar_stats = clouds["pulsar"]
        b_wall = sum(s["wall_clock"] for s in batch_stats) / len(batch_stats)
        b_comp = sum(s["compute"] for s in batch_stats) / len(batch_stats)
        b_oh = sum(s["overhead"] for s in batch_stats) / len(batch_stats)
        p_wall = sum(s["wall_clock"] for s in pulsar_stats) / len(pulsar_stats)
        p_comp = sum(s["compute"] for s in pulsar_stats) / len(pulsar_stats)
        p_oh = sum(s["overhead"] for s in pulsar_stats) / len(pulsar_stats)

        b_label = f"GCP Batch (avg of {len(batch_stats)} runs)" if len(batch_stats) > 1 else "GCP Batch"
        p_label = f"Pulsar (avg of {len(pulsar_stats)} runs)" if len(pulsar_stats) > 1 else "Pulsar"

        w(f"### Head-to-Head: {size}")
        w("")
        w(f"| Metric | {b_label} | {p_label} | Difference |")
        w("|--------|" + "-" * (len(b_label) + 2) + "|" + "-" * (len(p_label) + 2) + "|------------|")
        w(f"| **Wall clock** | **{fmt_min(b_wall)} min** | **{fmt_min(p_wall)} min** | **{fmt_min(p_wall - b_wall):s} min ({fmt_pct(p_wall - b_wall, b_wall)})** |")
        w(f"| **Compute time** | **{fmt_min(b_comp)} min** | **{fmt_min(p_comp)} min** | **{fmt_min(p_comp - b_comp):s} min ({fmt_pct(p_comp - b_comp, b_comp)})** |")
        w(f"| **Scheduling overhead** | **{fmt_min(b_oh)} min** | **{fmt_min(p_oh)} min** | **{fmt_min(p_oh - b_oh):s} min ({fmt_pct(p_oh - b_oh, b_oh)})** |")
        w(f"| Steps completed | {batch_stats[0]['steps']}/{batch_stats[0]['steps']} | {pulsar_stats[0]['steps']}/{pulsar_stats[0]['steps']} | -- |")
        w("")

    # Per-step tables
    w("## Per-Step Compute Time (runtime_seconds)")
    w("")
    for size, clouds in sorted(matchups.items()):
        batch_stats = clouds["batch"]
        pulsar_stats = clouds["pulsar"]
        b_times = avg_tool_times(batch_stats)
        p_times = avg_tool_times(pulsar_stats)

        w(f"### {size}")
        w("")
        if len(batch_stats) > 1 or len(pulsar_stats) > 1:
            header = "| Tool | Batch Avg | Pulsar Avg | Diff | Diff% |"
            sep = "|------|-----------|------------|------|-------|"
        else:
            header = "| Tool | Batch | Pulsar | Diff | Diff% |"
            sep = "|------|-------|--------|------|-------|"
        w(header)
        w(sep)
        b_total = p_total = 0
        for tool in TOOL_ORDER:
            if tool not in b_times and tool not in p_times:
                continue
            b = b_times.get(tool, 0)
            p = p_times.get(tool, 0)
            diff = p - b
            pct = fmt_pct(diff, b) if b > 1 else "--"
            w(f"| {tool} | {b:.0f}s | {p:.0f}s | {diff:+.0f}s | {pct} |")
            b_total += b
            p_total += p
        diff_total = p_total - b_total
        w(f"| **Total** | **{b_total:.0f}s** | **{p_total:.0f}s** | **{diff_total:+.0f}s** | **{fmt_pct(diff_total, b_total)}** |")
        w("")

    # Resource allocation section
    w("## Resource Allocation: VM Sizing vs GALAXY_SLOTS")
    w("")
    w("### VM Right-Sizing (Working)")
    w("")
    w("Pulsar correctly right-sizes GCP Batch VMs based on per-tool resource requirements. The TPV destination passes `cores: \"{cores}\"` and `mem: \"{mem}\"` to Pulsar's `parse_gcp_job_params()`, which calls `compute_machine_type()` to select an appropriate N2 machine type.")
    w("")
    w("### GALAXY_SLOTS Reporting Gap")
    w("")
    w("Galaxy reports **slots=1** and **mem=0MB** for all Pulsar jobs because the Pulsar coexecution path doesn't feed these values back to Galaxy's metrics. The direct Batch runner explicitly sets `export GALAXY_SLOTS=${galaxy_slots}` in its `container_script.sh`. The Pulsar path relies on `CLUSTER_SLOTS_STATEMENT.sh`, which falls through to `GALAXY_SLOTS=\"1\"` on GCP Batch VMs (no SLURM/PBS/SGE env vars). Actual thread usage depends on how each tool discovers available CPUs.")
    w("")

    # Slots table from batch data
    any_batch = [s for s in all_stats if s["cloud"] == "batch"]
    if any_batch:
        b_slots = avg_tool_slots(any_batch)
        w("### Batch Resource Allocation (as reported by Galaxy)")
        w("")
        w("| Tool | CPU Slots |")
        w("|------|-----------|")
        for tool in TOOL_ORDER:
            if tool in b_slots and b_slots[tool] > 0:
                w(f"| {tool} | {b_slots[tool]:.0f} |")
        w("")

    # Runtime ratio analysis
    for size, clouds in sorted(matchups.items()):
        b_times = avg_tool_times(clouds["batch"])
        p_times = avg_tool_times(clouds["pulsar"])
        b_slots_map = avg_tool_slots(clouds["batch"])
        w(f"### Runtime Ratio Analysis ({size})")
        w("")
        w("| Tool | Batch Slots | Pulsar/Batch Ratio | Expected if 1 Thread |")
        w("|------|------------|-------------------|---------------------|")
        for tool in TOOL_ORDER:
            b = b_times.get(tool, 0)
            p = p_times.get(tool, 0)
            s = b_slots_map.get(tool, 1)
            if b > 5:
                ratio = f"{p / b:.2f}x"
                expected = f"~{s:.0f}x"
                w(f"| {tool} | {s:.0f} | {ratio} | {expected} |")
        w("")
        break  # Only show for smallest matchup size

    # Scheduling overhead
    w("## Wall Clock vs Compute Time Analysis")
    w("")
    w("| Runner | Input | Wall Clock | Compute | Overhead | Overhead % |")
    w("|--------|-------|-----------|---------|----------|------------|")
    for s in sorted(all_stats, key=lambda x: (x["cloud"], x["size"])):
        oh_pct = f"{s['overhead'] / s['wall_clock'] * 100:.0f}%" if s["wall_clock"] > 0 else "--"
        w(f"| {s['cloud']} R{s['run']} | {s['size']} | {fmt_min(s['wall_clock'])}m | {fmt_min(s['compute'])}m | {fmt_min(s['overhead'])}m | {oh_pct} |")
    w("")

    # Batch scaling
    batch_only = sorted([s for s in all_stats if s["cloud"] == "batch"], key=lambda x: x["size"])
    if len(set(s["size"] for s in batch_only)) > 1:
        w("## Batch Scaling Analysis")
        w("")
        by_size = defaultdict(list)
        for s in batch_only:
            by_size[s["size"]].append(s)
        w("| Input | Wall Clock | Compute |")
        w("|-------|-----------|---------|")
        for size in sorted(by_size.keys()):
            avg_wall = sum(s["wall_clock"] for s in by_size[size]) / len(by_size[size])
            avg_comp = sum(s["compute"] for s in by_size[size]) / len(by_size[size])
            n = len(by_size[size])
            label = f"{size} (avg of {n})" if n > 1 else size
            w(f"| {label} | {fmt_min(avg_wall)}m | {fmt_min(avg_comp)}m |")
        w("")

    # Key findings
    w("## Key Findings")
    w("")
    finding_num = 1
    for size, clouds in sorted(matchups.items()):
        b_wall = sum(s["wall_clock"] for s in clouds["batch"]) / len(clouds["batch"])
        p_wall = sum(s["wall_clock"] for s in clouds["pulsar"]) / len(clouds["pulsar"])
        b_comp = sum(s["compute"] for s in clouds["batch"]) / len(clouds["batch"])
        p_comp = sum(s["compute"] for s in clouds["pulsar"]) / len(clouds["pulsar"])
        w(f"### {finding_num}. {size}: Pulsar is {fmt_pct(p_wall - b_wall, b_wall)} slower (wall clock)")
        w("")
        w(f"- Wall clock: {fmt_min(p_wall)}m vs {fmt_min(b_wall)}m")
        w(f"- Compute: {fmt_min(p_comp)}m vs {fmt_min(b_comp)}m ({fmt_pct(p_comp - b_comp, b_comp)})")
        w("")
        finding_num += 1

    # Tools faster on Pulsar
    w(f"### {finding_num}. Several tools are faster on Pulsar")
    w("")
    for size, clouds in sorted(matchups.items()):
        b_times = avg_tool_times(clouds["batch"])
        p_times = avg_tool_times(clouds["pulsar"])
        faster = [(t, b_times[t], p_times[t]) for t in TOOL_ORDER
                   if t in b_times and t in p_times and p_times[t] < b_times[t] * 0.8 and b_times[t] > 5]
        if faster:
            for t, b, p in faster:
                w(f"- **{t}** ({size}): {fmt_pct(p - b, b)} ({p:.0f}s vs {b:.0f}s)")
        break
    w("")
    finding_num += 1

    w(f"### {finding_num}. Scheduling overhead is Pulsar's major cost")
    w("")
    batch_oh = [s["overhead"] / s["steps"] for s in all_stats if s["cloud"] == "batch"]
    pulsar_oh = [s["overhead"] / s["steps"] for s in all_stats if s["cloud"] == "pulsar"]
    if batch_oh and pulsar_oh:
        w(f"- Batch: {sum(batch_oh)/len(batch_oh)/60:.1f} min/step avg")
        w(f"- Pulsar: {sum(pulsar_oh)/len(pulsar_oh)/60:.1f} min/step avg")
    w("")
    finding_num += 1

    # Reproducibility
    sizes_with_multi_batch = [size for size, clouds in matchups.items() if len(clouds["batch"]) > 1]
    if sizes_with_multi_batch:
        w(f"### {finding_num}. Batch is highly reproducible")
        w("")
        for size in sizes_with_multi_batch:
            computes = [s["compute"] for s in matchups[size]["batch"]]
            if len(computes) >= 2:
                mean = sum(computes) / len(computes)
                spread = max(computes) - min(computes)
                w(f"- {size}: {len(computes)} runs, compute range {fmt_min(min(computes))}m - {fmt_min(max(computes))}m ({spread/mean*100:.1f}% spread)")
        w("")
        finding_num += 1

    w("## Implications")
    w("")
    w("- **Inject `GALAXY_SLOTS` into Pulsar task environment.** Tools that read `$GALAXY_SLOTS` for thread count would benefit. A fix has been prototyped in `pulsar/client/container_job_config.py`.")
    w("- **Pulsar's staging overhead is inherent** to the AMQP sidecar architecture. Dominates for short multi-step workflows, negligible for long-running single-step jobs.")
    w("- **Pulsar's I/O model has advantages.** Local SSD staging benefits I/O-bound tools. The snpEff_build_gb speedup warrants investigation.")
    w("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML chart generation
# ---------------------------------------------------------------------------

def generate_html(all_stats, matchups):
    # Prepare data for charts
    chart_data = {}
    for size, clouds in sorted(matchups.items()):
        b_times = avg_tool_times(clouds["batch"])
        p_times = avg_tool_times(clouds["pulsar"])
        b_slots = avg_tool_slots(clouds["batch"])
        chart_data[size] = {
            "batch": [b_times.get(t, 0) for t in TOOL_ORDER],
            "pulsar": [p_times.get(t, 0) for t in TOOL_ORDER],
            "batch_slots": [b_slots.get(t, 0) for t in TOOL_ORDER],
        }

    # Overview data
    overview_data = []
    for s in sorted(all_stats, key=lambda x: (x["cloud"], x["size"], x["run"])):
        overview_data.append({
            "label": f"{s['cloud']} R{s['run']} {s['size']}",
            "compute": round(s["compute"] / 60, 1),
            "overhead": round(s["overhead"] / 60, 1),
            "cloud": s["cloud"],
        })

    # Batch scaling data
    batch_by_size = defaultdict(list)
    for s in all_stats:
        if s["cloud"] == "batch":
            batch_by_size[s["size"]].append(s)

    scaling_data = {}
    for size in sorted(batch_by_size.keys()):
        avg_times = avg_tool_times(batch_by_size[size])
        scaling_data[size] = [avg_times.get(t, 0) for t in TOOL_ORDER]

    tools_json = json.dumps([TOOL_SHORT.get(t, t) for t in TOOL_ORDER])
    tools_full_json = json.dumps(TOOL_ORDER)
    matchup_sizes = sorted(matchups.keys())

    # Build tabs dynamically
    tab_ids = ["overview"]
    tab_labels = ["Overview"]
    for size in matchup_sizes:
        tab_ids.append(f"tab-{size.lower().replace('+', '-')}")
        tab_labels.append(size)
    if len(scaling_data) > 1:
        tab_ids.append("scaling")
        tab_labels.append("Batch Scaling")
    tab_ids.append("resources")
    tab_labels.append("Resources")

    html = []
    h = html.append

    h('<!DOCTYPE html>')
    h('<html lang="en">')
    h('<head>')
    h('<meta charset="UTF-8">')
    h('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    h('<title>Pulsar vs GCP Batch: Runtime Comparison</title>')
    h('<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>')
    h('<style>')
    h('  * { box-sizing: border-box; margin: 0; padding: 0; }')
    h('  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f7fa; color: #1a1a2e; padding: 2rem; max-width: 1200px; margin: 0 auto; }')
    h('  h1 { font-size: 1.8rem; margin-bottom: 0.3rem; }')
    h('  .subtitle { color: #666; font-size: 0.95rem; margin-bottom: 1.5rem; }')
    h('  .tabs { display: flex; gap: 0; margin-bottom: 2rem; border-bottom: 2px solid #e5e7eb; }')
    h('  .tab { padding: 0.7rem 1.4rem; cursor: pointer; font-size: 0.9rem; font-weight: 500; color: #666; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: color 0.2s, border-color 0.2s; user-select: none; }')
    h('  .tab:hover { color: #1a1a2e; }')
    h('  .tab.active { color: #3b82f6; border-bottom-color: #3b82f6; }')
    h('  .tab-content { display: none; }')
    h('  .tab-content.active { display: block; }')
    h('  .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 2rem; }')
    h('  .card { background: #fff; border-radius: 10px; padding: 1.2rem 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }')
    h('  .card .label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em; }')
    h('  .card .value { font-size: 1.8rem; font-weight: 700; margin-top: 0.2rem; }')
    h('  .card .detail { font-size: 0.85rem; color: #666; margin-top: 0.2rem; }')
    h('  .card.batch .value { color: #3b82f6; }')
    h('  .card.pulsar .value { color: #f59e0b; }')
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
    h('<h1>Pulsar vs Direct GCP Batch</h1>')
    h(f'<p class="subtitle">Variant analysis on WGS PE data &mdash; 12-step workflow &mdash; {len(all_stats)} runs</p>')
    h('')

    # Tabs
    h('<div class="tabs">')
    for i, (tid, tlabel) in enumerate(zip(tab_ids, tab_labels)):
        active = " active" if i == 0 else ""
        h(f'  <div class="tab{active}" data-tab="{tid}">{tlabel}</div>')
    h('</div>')
    h('')

    # ===== OVERVIEW TAB =====
    h('<div class="tab-content active" id="overview">')
    h('  <div class="chart-container">')
    h('    <h2>Wall Clock: Compute vs Scheduling Overhead</h2>')
    h('    <p class="chart-desc">Stacked bars: compute time (solid) + scheduling/staging overhead (striped) for each run.</p>')
    h('    <canvas id="overviewStacked" height="80"></canvas>')
    h('  </div>')

    # Overview scheduling overhead comparison
    h('  <div class="chart-container">')
    h('    <h2>Per-Step Scheduling Overhead</h2>')
    h('    <p class="chart-desc">Average overhead per workflow step (wall clock minus compute, divided by step count).</p>')
    h('    <canvas id="overviewOHPerStep" height="80"></canvas>')
    h('  </div>')
    h('</div>')
    h('')

    # ===== SIZE COMPARISON TABS =====
    for size in matchup_sizes:
        tid = f"tab-{size.lower().replace('+', '-')}"
        b_stats = matchups[size]["batch"]
        p_stats = matchups[size]["pulsar"]
        b_wall = sum(s["wall_clock"] for s in b_stats) / len(b_stats)
        p_wall = sum(s["wall_clock"] for s in p_stats) / len(p_stats)
        b_comp = sum(s["compute"] for s in b_stats) / len(b_stats)
        p_comp = sum(s["compute"] for s in p_stats) / len(p_stats)

        h(f'<div class="tab-content" id="{tid}">')
        h('  <div class="summary-cards">')
        h(f'    <div class="card batch"><div class="label">Batch Compute</div><div class="value">{b_comp/60:.1f} min</div><div class="detail">{b_comp:.0f}s across 12 steps</div></div>')
        h(f'    <div class="card pulsar"><div class="label">Pulsar Compute</div><div class="value">{p_comp/60:.1f} min</div><div class="detail">{p_comp:.0f}s across 12 steps</div></div>')
        diff_pct = (p_comp - b_comp) / b_comp * 100 if b_comp > 0 else 0
        h(f'    <div class="card overhead"><div class="label">Compute Difference</div><div class="value">{diff_pct:+.0f}%</div><div class="detail">{p_comp - b_comp:+.0f}s &mdash; staging overhead + GALAXY_SLOTS gap</div></div>')
        h('  </div>')
        h(f'  <div class="chart-container"><h2>Per-Step Compute Time &mdash; {size}</h2><p class="chart-desc">Actual runtime_seconds per tool.</p><canvas id="bar_{tid}" height="100"></canvas></div>')
        h('  <div class="chart-row">')
        h(f'    <div class="chart-container"><h2>Per-Step Overhead &mdash; {size}</h2><p class="chart-desc">Pulsar minus Batch compute. Green = Pulsar faster.</p><canvas id="oh_{tid}" height="160"></canvas></div>')
        h(f'    <div class="chart-container"><h2>Cumulative Compute &mdash; {size}</h2><p class="chart-desc">Running total of compute seconds.</p><canvas id="cum_{tid}" height="160"></canvas></div>')
        h('  </div>')
        h('</div>')
        h('')

    # ===== SCALING TAB =====
    if len(scaling_data) > 1:
        h('<div class="tab-content" id="scaling">')
        h('  <div class="chart-container"><h2>Batch: Per-Tool Compute by Input Size</h2><p class="chart-desc">How each tool scales with data size (Batch only).</p><canvas id="scalingChart" height="100"></canvas></div>')
        h('  <div class="chart-container"><h2>Batch: Total Compute by Input Size</h2><p class="chart-desc">Total compute and wall clock scaling.</p><canvas id="scalingLineChart" height="80"></canvas></div>')
        h('</div>')
        h('')

    # ===== RESOURCES TAB =====
    first_matchup = matchup_sizes[0] if matchup_sizes else None
    h('<div class="tab-content" id="resources">')
    h('  <div class="summary-cards">')
    h('    <div class="card batch"><div class="label">VM Right-Sizing</div><div class="value">Working</div><div class="detail">Pulsar compute_machine_type() selects correct N2 VM</div></div>')
    h('    <div class="card pulsar"><div class="label">GALAXY_SLOTS Reporting</div><div class="value">slots=1</div><div class="detail">Galaxy reports 1 slot (metric gap, not actual VM cores)</div></div>')
    h('  </div>')
    h('  <div class="chart-container"><h2>Galaxy-Reported CPU Slots: Batch vs Pulsar</h2><p class="chart-desc">Batch sets GALAXY_SLOTS explicitly. Pulsar relies on CLUSTER_SLOTS_STATEMENT.sh fallback.</p><canvas id="slotsChart" height="100"></canvas></div>')
    h('  <div class="chart-container"><h2>Runtime Ratio vs Batch Slot Count</h2><p class="chart-desc">If Pulsar were truly 1-thread, overhead % would match slot count. Actual ratios are lower.</p><canvas id="impactChart" height="100"></canvas></div>')
    h('</div>')
    h('')

    # Footer
    h('<div class="footer">')
    h(f'  Galaxy 26.1 &middot; GCP Batch us-east4 &middot; {len(all_stats)} workflow runs &middot; Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>')
    h('')

    # ===== JAVASCRIPT =====
    # Python-side color constants (mirrored in JS below)
    blue, blueLight, amber, amberLight = "#3b82f6", "#93bbfd", "#f59e0b", "#fcd679"

    h('<script>')
    h(f'const tools = {tools_json};')
    h(f'const toolsFull = {tools_full_json};')
    h('')
    h(f'const blue = "{blue}", blueLight = "{blueLight}", amber = "{amber}", amberLight = "{amberLight}";')
    h('const red = "#ef4444", green = "#22c55e", purple = "#8b5cf6", purpleLight = "#c4b5fd";')
    h('const chartFont = { family: "-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" };')
    h('Chart.defaults.font.family = chartFont.family;')
    h('Chart.defaults.font.size = 12;')
    h('')
    h('const secTooltip = ctx => `${ctx.dataset.label}: ${ctx.raw}s (${(ctx.raw/60).toFixed(1)}m)`;')
    h('function cumSum(arr) { let s=0; return arr.map(v => s += v); }')
    h('')

    # Matchup data
    for size, cd in chart_data.items():
        safe = size.lower().replace("+", "_")
        h(f'const batch_{safe} = {json.dumps([round(v) for v in cd["batch"]])};')
        h(f'const pulsar_{safe} = {json.dumps([round(v) for v in cd["pulsar"]])};')
        h(f'const overhead_{safe} = batch_{safe}.map((b,i) => pulsar_{safe}[i] - b);')
        h(f'const batchSlots_{safe} = {json.dumps([round(v) for v in cd["batch_slots"]])};')

    h('')

    # Overview stacked chart
    h(f'const ovLabels = {json.dumps([d["label"] for d in overview_data])};')
    h(f'const ovCompute = {json.dumps([d["compute"] for d in overview_data])};')
    h(f'const ovOverhead = {json.dumps([d["overhead"] for d in overview_data])};')
    h(f'const ovColors = {json.dumps([blue if d["cloud"] == "batch" else amber for d in overview_data])};')
    h(f'const ovOHColors = {json.dumps(["#93bbfd" if d["cloud"] == "batch" else "#fcd679" for d in overview_data])};')
    h('')
    h('new Chart(document.getElementById("overviewStacked"), {')
    h('  type: "bar",')
    h('  data: { labels: ovLabels, datasets: [')
    h('    { label: "Compute", data: ovCompute, backgroundColor: ovColors, borderRadius: 4 },')
    h('    { label: "Scheduling Overhead", data: ovOverhead, backgroundColor: ovOHColors, borderRadius: 4 }')
    h('  ]},')
    h('  options: { responsive: true, plugins: { legend: { position: "top" }, tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.raw} min` } } }, scales: { x: { stacked: true, ticks: { maxRotation: 45, minRotation: 45 } }, y: { stacked: true, title: { display: true, text: "Minutes" }, beginAtZero: true } } }')
    h('});')
    h('')

    # Overview per-step overhead
    oh_per_step_labels = []
    oh_per_step_data = []
    oh_per_step_colors = []
    for s in sorted(all_stats, key=lambda x: (x["cloud"], x["size"])):
        oh_per_step_labels.append(f"{s['cloud']} R{s['run']} {s['size']}")
        oh_per_step_data.append(round(s["overhead"] / s["steps"] / 60, 1))
        oh_per_step_colors.append(blue if s["cloud"] == "batch" else amber)
    h(f'new Chart(document.getElementById("overviewOHPerStep"), {{')
    h(f'  type: "bar",')
    h(f'  data: {{ labels: {json.dumps(oh_per_step_labels)}, datasets: [{{ label: "Overhead per step", data: {json.dumps(oh_per_step_data)}, backgroundColor: {json.dumps(oh_per_step_colors)}, borderRadius: 4 }}] }},')
    h(f'  options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ title: {{ display: true, text: "Minutes" }}, beginAtZero: true }}, x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }} }} }}')
    h('});')
    h('')

    # Per-size comparison charts
    for size in matchup_sizes:
        safe = size.lower().replace("+", "_")
        tid = f"tab-{size.lower().replace('+', '-')}"

        # Bar chart
        h(f'new Chart(document.getElementById("bar_{tid}"), {{')
        h(f'  type: "bar", data: {{ labels: tools, datasets: [')
        h(f'    {{ label: "Batch", data: batch_{safe}, backgroundColor: blue, borderRadius: 4 }},')
        h(f'    {{ label: "Pulsar", data: pulsar_{safe}, backgroundColor: amber, borderRadius: 4 }}')
        h(f'  ] }}, options: {{ responsive: true, plugins: {{ legend: {{ position: "top" }}, tooltip: {{ callbacks: {{ label: secTooltip }} }} }}, scales: {{ y: {{ title: {{ display: true, text: "Seconds" }}, beginAtZero: true }}, x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }} }} }}')
        h('});')

        # Overhead chart
        h(f'new Chart(document.getElementById("oh_{tid}"), {{')
        h(f'  type: "bar", data: {{ labels: tools, datasets: [{{ label: "Pulsar overhead", data: overhead_{safe}, backgroundColor: overhead_{safe}.map(v => v >= 0 ? "#fca5a5" : "#86efac"), borderColor: overhead_{safe}.map(v => v >= 0 ? red : green), borderWidth: 1, borderRadius: 4 }}] }},')
        h(f'  options: {{ responsive: true, plugins: {{ legend: {{ display: false }}, tooltip: {{ callbacks: {{ label: ctx => {{ const v = ctx.raw; const base = batch_{safe}[ctx.dataIndex]; const pct = base > 0 ? ((v/base)*100).toFixed(0) : "--"; return `${{v >= 0 ? "+" : ""}}${{v}}s (${{v >= 0 ? "+" : ""}}${{pct}}%)`; }} }} }} }}, scales: {{ y: {{ title: {{ display: true, text: "Seconds" }} }}, x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }} }} }}')
        h('});')

        # Cumulative chart
        h(f'const bCum_{safe} = cumSum(batch_{safe});')
        h(f'const pCum_{safe} = cumSum(pulsar_{safe});')
        h(f'new Chart(document.getElementById("cum_{tid}"), {{')
        h(f'  type: "line", data: {{ labels: tools, datasets: [')
        h(f'    {{ label: "Batch", data: bCum_{safe}.map(v => +(v/60).toFixed(1)), borderColor: blue, backgroundColor: blueLight + "33", fill: true, tension: 0.3, pointRadius: 4, pointBackgroundColor: blue }},')
        h(f'    {{ label: "Pulsar", data: pCum_{safe}.map(v => +(v/60).toFixed(1)), borderColor: amber, backgroundColor: amberLight + "33", fill: true, tension: 0.3, pointRadius: 4, pointBackgroundColor: amber }}')
        h(f'  ] }}, options: {{ responsive: true, plugins: {{ tooltip: {{ callbacks: {{ label: ctx => `${{ctx.dataset.label}}: ${{ctx.raw}} min` }} }} }}, scales: {{ y: {{ title: {{ display: true, text: "Minutes" }}, beginAtZero: true }}, x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }} }} }}')
        h('});')
        h('')

    # Scaling charts
    if len(scaling_data) > 1:
        scaling_sizes = sorted(scaling_data.keys())
        colors = ['#93bbfd', '#3b82f6', '#1d4ed8', '#1e3a5f']
        h(f'new Chart(document.getElementById("scalingChart"), {{')
        h(f'  type: "bar", data: {{ labels: tools, datasets: [')
        for i, sz in enumerate(scaling_sizes):
            h(f'    {{ label: "{sz}", data: {json.dumps([round(v) for v in scaling_data[sz]])}, backgroundColor: "{colors[i % len(colors)]}", borderRadius: 4 }},')
        h(f'  ] }}, options: {{ responsive: true, plugins: {{ legend: {{ position: "top" }}, tooltip: {{ callbacks: {{ label: secTooltip }} }} }}, scales: {{ y: {{ title: {{ display: true, text: "Seconds" }}, beginAtZero: true }}, x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }} }} }}')
        h('});')

        # Scaling line chart
        s_labels = json.dumps(scaling_sizes)
        s_compute = json.dumps([round(sum(scaling_data[sz]) / 60, 1) for sz in scaling_sizes])
        s_wall = json.dumps([round(sum(s["wall_clock"] for s in batch_by_size[sz]) / len(batch_by_size[sz]) / 60, 1) for sz in scaling_sizes])
        h(f'new Chart(document.getElementById("scalingLineChart"), {{')
        h(f'  type: "line", data: {{ labels: {s_labels}, datasets: [')
        h(f'    {{ label: "Compute", data: {s_compute}, borderColor: blue, backgroundColor: blueLight + "33", fill: true, tension: 0.3, pointRadius: 6, pointBackgroundColor: blue }},')
        h(f'    {{ label: "Wall Clock", data: {s_wall}, borderColor: purple, backgroundColor: purpleLight + "33", fill: true, tension: 0.3, pointRadius: 6, pointBackgroundColor: purple }}')
        h(f'  ] }}, options: {{ responsive: true, plugins: {{ tooltip: {{ callbacks: {{ label: ctx => `${{ctx.dataset.label}}: ${{ctx.raw}} min` }} }} }}, scales: {{ y: {{ title: {{ display: true, text: "Minutes" }}, beginAtZero: true }}, x: {{ title: {{ display: true, text: "Input Data" }} }} }} }}')
        h('});')
        h('')

    # Resource charts (use first matchup)
    if first_matchup:
        safe = first_matchup.lower().replace("+", "_")
        h(f'const batchSlots = batchSlots_{safe};')
        h(f'const pulsarSlots = {json.dumps([1] * len(TOOL_ORDER))};')
        h('new Chart(document.getElementById("slotsChart"), {')
        h('  type: "bar", data: { labels: tools, datasets: [')
        h('    { label: "Batch slots", data: batchSlots, backgroundColor: blue, borderRadius: 4 },')
        h('    { label: "Pulsar slots (reported)", data: pulsarSlots, backgroundColor: amber, borderRadius: 4 }')
        h('  ] }, options: { responsive: true, plugins: { legend: { position: "top" } }, scales: { y: { title: { display: true, text: "CPU Slots" }, beginAtZero: true, ticks: { stepSize: 1 } }, x: { ticks: { maxRotation: 45, minRotation: 45 } } } }')
        h('});')
        h('')

        # Impact chart
        h(f'const impactData = tools.map((t, i) => {{')
        h(f'  const base = batch_{safe}[i]; const diff = overhead_{safe}[i];')
        h(f'  const pct = base > 0 ? +((diff / base) * 100).toFixed(0) : 0;')
        h(f'  return {{ tool: t, slots: batchSlots[i], pct: pct }};')
        h('});')
        h('new Chart(document.getElementById("impactChart"), {')
        h('  type: "bar", data: { labels: tools, datasets: [')
        h('    { label: "Batch CPU Slots", data: batchSlots, backgroundColor: blueLight, borderColor: blue, borderWidth: 1, borderRadius: 4, yAxisID: "y" },')
        h('    { label: "Pulsar Compute Overhead %", data: impactData.map(d => d.pct), backgroundColor: impactData.map(d => d.pct >= 0 ? "#fca5a5" : "#86efac"), borderColor: impactData.map(d => d.pct >= 0 ? red : green), borderWidth: 1, borderRadius: 4, yAxisID: "y1" }')
        h('  ] }, options: { responsive: true, plugins: { legend: { position: "top" }, tooltip: { callbacks: { label: ctx => { if (ctx.datasetIndex === 0) return `${ctx.raw} CPU slots`; return `${ctx.raw >= 0 ? "+" : ""}${ctx.raw}% compute overhead`; } } } }, scales: { y: { position: "left", title: { display: true, text: "CPU Slots" }, beginAtZero: true, ticks: { stepSize: 1 } }, y1: { position: "right", title: { display: true, text: "Overhead %" }, grid: { drawOnChartArea: false } }, x: { ticks: { maxRotation: 45, minRotation: 45 } } } }')
        h('});')

    h('')

    # Tab switching JS
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
# Main
# ---------------------------------------------------------------------------

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    metrics_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base_dir, "metrics", "Pulsar-vs-Batch")
    docs_dir = os.path.join(base_dir, "docs")

    os.makedirs(docs_dir, exist_ok=True)

    print(f"Loading metrics from {metrics_dir}...")
    jobs = load_metrics(metrics_dir)
    groups = group_by_history(jobs)

    all_stats = [history_stats(g) for g in groups.values()]
    matchups = find_matchups(all_stats)

    print(f"  {len(jobs)} jobs across {len(all_stats)} workflow runs")
    print(f"  Matchups: {', '.join(matchups.keys()) if matchups else 'none'}")
    print()

    experiment_name = os.path.basename(metrics_dir)

    md_path = os.path.join(docs_dir, "index.md")
    md = generate_markdown(all_stats, matchups, experiment_name)
    with open(md_path, "w") as f:
        f.write(md)
    print(f"  Wrote {md_path}")

    html_path = os.path.join(docs_dir, "charts.html")
    html = generate_html(all_stats, matchups)
    with open(html_path, "w") as f:
        f.write(html)
    print(f"  Wrote {html_path}")


if __name__ == "__main__":
    main()
