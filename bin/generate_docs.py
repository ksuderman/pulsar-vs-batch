#!/usr/bin/env python3
"""Generate docs/index.md and docs/charts.html from metrics JSON files.

Usage:
    python3 bin/generate_docs.py [metrics_dir]

Reads all JSON files from metrics/<experiment>/ (default: metrics/Pulsar-vs-Batch/)
and produces:
    docs/index.md      - Markdown results report
    docs/charts.html   - Interactive Chart.js dashboard

Supports any workflow -- tools are discovered dynamically from the data,
sorted by average runtime (descending), and short names are auto-generated.
"""

import argparse
import json
import glob
import hashlib
import os
import re
import sys
from collections import defaultdict
from datetime import datetime

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
    """Derive a size label from the inputs string.

    For variant analysis data with explicit size markers (2GB, 5GB, 10GB),
    returns a cumulative label showing total data processed. When multiple
    sizes appear in one workflow invocation, all datasets are processed
    together (e.g. "7GB (2+5)" means the 2GB and 5GB datasets were
    processed in a single workflow run).

    For other workflows (e.g. RNASeq with SRR identifiers), extracts
    meaningful tokens from the input string to produce a short label.
    """
    # Check for explicit size markers first.
    # The inputs field may contain datasets from prior runs in the same
    # history (an ABM reporting artifact).  Use the largest size marker
    # as the actual input size for this invocation.
    size_values = {"2GB": 2, "5GB": 5, "10GB": 10}
    sizes = [s for s in size_values if s in inputs_str]
    if sizes:
        largest = max(sizes, key=lambda s: size_values[s])
        return largest

    # For other workflows, extract distinguishing tokens.
    # Split on whitespace, find unique non-reference tokens.
    # Reference files (e.g. .gtf, .gbff) are shared across runs;
    # the varying parts (e.g. SRR IDs with size suffixes) identify the run.
    tokens = inputs_str.strip().split()
    if not tokens:
        return "unknown"

    # Filter out common reference file names (keep only data identifiers)
    ref_extensions = {".gtf", ".gbff", ".gbff.gz", ".fa", ".fa.gz", ".fasta",
                      ".fasta.gz", ".bed", ".gff", ".gff3", ".len"}
    data_tokens = []
    for t in tokens:
        is_ref = any(t.lower().endswith(ext) for ext in ref_extensions)
        if not is_ref:
            data_tokens.append(t)

    if data_tokens:
        return " ".join(sorted(set(data_tokens)))

    # Fallback: short hash
    h = hashlib.sha256(inputs_str.encode()).hexdigest()[:8]
    return f"input-{h}"


def discover_tool_order(jobs):
    """Discover tools from data and sort by average runtime (descending).

    Returns (tool_order, tool_short) where tool_order is a list of tool names
    and tool_short maps full names to abbreviated display names.
    """
    # Only consider successfully completed jobs for runtime ordering
    tool_runtimes = defaultdict(list)
    all_tools = set()
    for j in jobs:
        all_tools.add(j["tool"])
        if j["state"] == "ok" and j["runtime"] > 0:
            tool_runtimes[j["tool"]].append(j["runtime"])

    # Include tools with no successful runs too (they'll have avg=0)
    for t in all_tools:
        if t not in tool_runtimes:
            tool_runtimes[t] = [0]

    # Sort by average runtime descending
    tool_order = sorted(tool_runtimes.keys(),
                        key=lambda t: sum(tool_runtimes[t]) / len(tool_runtimes[t]),
                        reverse=True)

    # Generate short names: truncate at 12 chars
    tool_short = {}
    for t in tool_order:
        if len(t) <= 12:
            tool_short[t] = t
        else:
            tool_short[t] = t[:12]

    # Resolve collisions in short names
    seen = {}
    for t in tool_order:
        short = tool_short[t]
        if short in seen:
            # Append a distinguishing suffix
            idx = 2
            while f"{short[:10]}_{idx}" in seen.values():
                idx += 1
            tool_short[t] = f"{short[:10]}_{idx}"
        seen[tool_short[t]] = t

    return tool_order, tool_short


def derive_experiment_title(experiment_name):
    """Derive a human-readable workflow title from the experiment directory name.

    e.g. 'Pulsar-vs-Batch-RNASeq' -> 'RNASeq'
         'Pulsar-vs-Batch' -> 'Variant Analysis'
    """
    # Strip the common prefix
    title = experiment_name
    for prefix in ["Pulsar-vs-Batch-", "Pulsar-vs-Batch"]:
        if title.startswith(prefix):
            title = title[len(prefix):]
            break
    # If nothing left after stripping, use a default
    if not title:
        title = "Variant Analysis"
    return title


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
    # Only count runtime from ok jobs
    ok_jobs = [j for j in jobs if j["state"] == "ok"]
    compute = sum(j["runtime"] for j in ok_jobs)
    overhead = wall_clock - compute
    size_label = get_size_label(jobs[0]["inputs"])
    date_range = (min(creates).strftime("%Y-%m-%d"), max(updates).strftime("%Y-%m-%d"))

    total_steps = len(jobs)
    ok_steps = len(ok_jobs)
    failed_steps = total_steps - ok_steps
    failed_tools = [j["tool"] for j in jobs if j["state"] != "ok"]

    return {
        "cloud": jobs[0]["cloud"],
        "run": jobs[0]["run"],
        "history_id": jobs[0]["history_id"],
        "size": size_label,
        "wall_clock": wall_clock,
        "compute": compute,
        "overhead": overhead,
        "steps": total_steps,
        "ok_steps": ok_steps,
        "failed_steps": failed_steps,
        "failed_tools": failed_tools,
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
    """Return {tool: total_runtime} for a history stat, summing duplicate tools."""
    tools = defaultdict(float)
    for j in stat["jobs"]:
        if j["state"] == "ok":
            tools[j["tool"]] += j["runtime"]
    return dict(tools)


def avg_tool_times(stats_list):
    """Average per-tool runtimes across multiple runs.

    For tools that appear multiple times in a single workflow run,
    their runtimes are summed first, then averaged across runs.
    """
    tool_totals = defaultdict(list)
    for s in stats_list:
        per_history = defaultdict(float)
        for j in s["jobs"]:
            if j["state"] == "ok":
                per_history[j["tool"]] += j["runtime"]
        for t, v in per_history.items():
            tool_totals[t].append(v)
    return {t: sum(v) / len(v) for t, v in tool_totals.items()}


def avg_tool_slots(stats_list):
    """Average per-tool slots across runs (take max slots per tool per history)."""
    tool_slots = defaultdict(list)
    for s in stats_list:
        per_history = defaultdict(float)
        for j in s["jobs"]:
            if j["state"] == "ok" and j["slots"] > 0:
                # Use max slots for a tool (in case of multiple invocations)
                per_history[j["tool"]] = max(per_history[j["tool"]], j["slots"])
        for t, v in per_history.items():
            tool_slots[t].append(v)
    return {t: sum(v) / len(v) for t, v in tool_slots.items()}


def fmt_min(seconds):
    return f"{seconds / 60:.1f}"


def fmt_pct(diff, base):
    if base == 0:
        return "--"
    return f"{diff / base * 100:+.0f}%"


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def generate_markdown(all_stats, matchups, experiment_name, tool_order, tool_short):
    workflow_title = derive_experiment_title(experiment_name)
    # Count unique tools across all runs
    all_tools = set()
    for s in all_stats:
        for j in s["jobs"]:
            all_tools.add(j["tool"])
    step_count = len(all_tools)

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
    w(f"title: Pulsar vs Direct GCP Batch - {workflow_title}")
    w("---")
    w("")
    w(f"# Pulsar vs Direct GCP Batch: {workflow_title}")
    w("")
    w("**[Interactive Charts](charts.html)**")
    w("")

    # Setup
    w("## Experiment Setup")
    w("")
    w(f"- **Workflow:** {workflow_title} ({step_count} unique tool types)")
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
    total_ok = sum(s["ok_steps"] for s in all_stats)
    total_failed = sum(s["failed_steps"] for s in all_stats)
    w(f"### Workflow Runs")
    w("")
    if total_failed == 0:
        w(f"{len(all_stats)} workflow invocations, {total_jobs} total jobs. All completed successfully.")
    else:
        w(f"{len(all_stats)} workflow invocations, {total_jobs} total jobs ({total_ok} succeeded, {total_failed} failed/errored).")
    w("")

    # Report failed jobs if any
    if total_failed > 0:
        w("### Failed/Errored Jobs")
        w("")
        failed_by_cloud = defaultdict(lambda: defaultdict(list))
        for s in all_stats:
            for j in s["jobs"]:
                if j["state"] != "ok":
                    failed_by_cloud[s["cloud"]][j["tool"]].append(j["state"])
        w("| Cloud | Tool | State | Count |")
        w("|-------|------|-------|-------|")
        for cloud in sorted(failed_by_cloud.keys()):
            for tool in sorted(failed_by_cloud[cloud].keys()):
                states = failed_by_cloud[cloud][tool]
                from collections import Counter
                for state, count in sorted(Counter(states).items()):
                    w(f"| {cloud} | {tool} | {state} | {count} |")
        w("")

    # Summary table
    w("## Results Summary")
    w("")
    w("### All Runs")
    w("")
    w("| Runner | Run | Input Sizes | Wall Clock | Compute Time | Scheduling Overhead | Steps OK |")
    w("|--------|-----|-------------|-----------|-------------|-------------------|----------|")
    for s in sorted(all_stats, key=lambda x: (x["cloud"], x["run"], x["size"])):
        oh_pct = f"{s['overhead'] / s['wall_clock'] * 100:.0f}%" if s["wall_clock"] > 0 else "--"
        steps_str = f"{s['ok_steps']}/{s['steps']}"
        w(f"| {s['cloud']} | {s['run']} | {s['size']} | {fmt_min(s['wall_clock'])} min | {fmt_min(s['compute'])} min | {fmt_min(s['overhead'])} min ({oh_pct}) | {steps_str} |")
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

        b_ok = sum(s["ok_steps"] for s in batch_stats) // len(batch_stats)
        p_ok = sum(s["ok_steps"] for s in pulsar_stats) // len(pulsar_stats)
        b_total = batch_stats[0]["steps"]
        p_total = pulsar_stats[0]["steps"]

        w(f"### Head-to-Head: {size}")
        w("")
        w(f"| Metric | {b_label} | {p_label} | Difference |")
        w("|--------|" + "-" * (len(b_label) + 2) + "|" + "-" * (len(p_label) + 2) + "|------------|")
        w(f"| **Wall clock** | **{fmt_min(b_wall)} min** | **{fmt_min(p_wall)} min** | **{fmt_min(p_wall - b_wall):s} min ({fmt_pct(p_wall - b_wall, b_wall)})** |")
        w(f"| **Compute time** | **{fmt_min(b_comp)} min** | **{fmt_min(p_comp)} min** | **{fmt_min(p_comp - b_comp):s} min ({fmt_pct(p_comp - b_comp, b_comp)})** |")
        w(f"| **Scheduling overhead** | **{fmt_min(b_oh)} min** | **{fmt_min(p_oh)} min** | **{fmt_min(p_oh - b_oh):s} min ({fmt_pct(p_oh - b_oh, b_oh)})** |")
        w(f"| Steps completed | {b_ok}/{b_total} | {p_ok}/{p_total} | -- |")
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
        for tool in tool_order:
            if tool not in b_times and tool not in p_times:
                continue
            b = b_times.get(tool, 0)
            p = p_times.get(tool, 0)
            diff = p - b
            pct = fmt_pct(diff, b) if b > 1 else "--"
            note = ""
            if tool not in b_times:
                note = " *"
            elif tool not in p_times:
                note = " *"
            w(f"| {tool}{note} | {b:.0f}s | {p:.0f}s | {diff:+.0f}s | {pct} |")
            b_total += b
            p_total += p
        diff_total = p_total - b_total
        w(f"| **Total** | **{b_total:.0f}s** | **{p_total:.0f}s** | **{diff_total:+.0f}s** | **{fmt_pct(diff_total, b_total)}** |")
        w("")
        # Note tools only present on one cloud
        batch_only = [t for t in tool_order if t in b_times and t not in p_times]
        pulsar_only = [t for t in tool_order if t not in b_times and t in p_times]
        if batch_only:
            w(f"*Tools only on Batch: {', '.join(batch_only)}*")
            w("")
        if pulsar_only:
            w(f"*Tools only on Pulsar: {', '.join(pulsar_only)}*")
            w("")

    # Resource allocation section
    w("## Resource Allocation: VM Sizing vs GALAXY_SLOTS")
    w("")
    w("### VM Right-Sizing (Working)")
    w("")
    w("Pulsar correctly right-sizes GCP Batch VMs based on per-tool resource requirements. The TPV destination passes `cores: \"{cores}\"` and `mem: \"{mem}\"` to Pulsar's `parse_gcp_job_params()`, which calls `compute_machine_type()` to select an appropriate N2 machine type.")
    w("")

    # Check if Pulsar still reports slots=1 or if the fix is deployed
    pulsar_stats = [s for s in all_stats if s["cloud"] == "pulsar"]
    pulsar_slots_values = set()
    for s in pulsar_stats:
        for j in s["jobs"]:
            if j["state"] == "ok" and j["slots"] > 0:
                pulsar_slots_values.add(j["slots"])

    if pulsar_slots_values and pulsar_slots_values != {1.0}:
        w("### GALAXY_SLOTS Reporting (Fixed)")
        w("")
        w("Pulsar now correctly reports GALAXY_SLOTS. The fix injects the proper slot count into the Pulsar task environment, so Galaxy metrics accurately reflect the VM cores allocated to each job.")
        w("")
    else:
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
        for tool in tool_order:
            if tool in b_slots and b_slots[tool] > 0:
                w(f"| {tool} | {b_slots[tool]:.0f} |")
        w("")

    # Runtime ratio analysis
    for size, clouds in sorted(matchups.items()):
        b_times = avg_tool_times(clouds["batch"])
        p_times = avg_tool_times(clouds["pulsar"])
        b_slots_map = avg_tool_slots(clouds["batch"])
        # Only show if there are tools with data on both sides
        tools_both = [t for t in tool_order if t in b_times and t in p_times and b_times[t] > 5]
        if not tools_both:
            continue
        w(f"### Runtime Ratio Analysis ({size})")
        w("")
        w("| Tool | Batch Slots | Pulsar/Batch Ratio | Expected if 1 Thread |")
        w("|------|------------|-------------------|---------------------|")
        for tool in tools_both:
            b = b_times[tool]
            p = p_times[tool]
            s = b_slots_map.get(tool, 1)
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
    for size, clouds in sorted(matchups.items()):
        b_times = avg_tool_times(clouds["batch"])
        p_times = avg_tool_times(clouds["pulsar"])
        faster = [(t, b_times[t], p_times[t]) for t in tool_order
                   if t in b_times and t in p_times and p_times[t] < b_times[t] * 0.8 and b_times[t] > 5]
        if faster:
            w(f"### {finding_num}. Several tools are faster on Pulsar")
            w("")
            for t, b, p in faster:
                w(f"- **{t}** ({size}): {fmt_pct(p - b, b)} ({p:.0f}s vs {b:.0f}s)")
            w("")
            finding_num += 1
        break

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
    w("- **Pulsar's staging overhead is inherent** to the AMQP sidecar architecture. Dominates for short multi-step workflows, negligible for long-running single-step jobs.")
    w("- **Pulsar's I/O model has advantages.** Local SSD staging benefits I/O-bound tools.")
    w("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML chart generation
# ---------------------------------------------------------------------------

def generate_html(all_stats, matchups, experiment_name, tool_order, tool_short):
    workflow_title = derive_experiment_title(experiment_name)

    # Count unique tools
    all_tools = set()
    for s in all_stats:
        for j in s["jobs"]:
            all_tools.add(j["tool"])
    step_count = len(all_tools)

    # Prepare data for charts
    chart_data = {}
    for size, clouds in sorted(matchups.items()):
        b_times = avg_tool_times(clouds["batch"])
        p_times = avg_tool_times(clouds["pulsar"])
        b_slots = avg_tool_slots(clouds["batch"])
        chart_data[size] = {
            "batch": [b_times.get(t, 0) for t in tool_order],
            "pulsar": [p_times.get(t, 0) for t in tool_order],
            "batch_slots": [b_slots.get(t, 0) for t in tool_order],
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
        scaling_data[size] = [avg_times.get(t, 0) for t in tool_order]

    tools_json = json.dumps([tool_short.get(t, t) for t in tool_order])
    tools_full_json = json.dumps(tool_order)
    matchup_sizes = sorted(matchups.keys())

    # Check Pulsar slots status
    pulsar_stats = [s for s in all_stats if s["cloud"] == "pulsar"]
    pulsar_slots_values = set()
    for s in pulsar_stats:
        for j in s["jobs"]:
            if j["state"] == "ok" and j["slots"] > 0:
                pulsar_slots_values.add(j["slots"])
    pulsar_slots_fixed = pulsar_slots_values and pulsar_slots_values != {1.0}

    # Build tabs dynamically
    tab_ids = ["overview"]
    tab_labels = ["Overview"]
    for size in matchup_sizes:
        safe_id = re.sub(r'[^a-zA-Z0-9]', '-', size.lower())
        tab_ids.append(f"tab-{safe_id}")
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
    h(f'<title>Pulsar vs GCP Batch: {workflow_title}</title>')
    h('<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>')
    h('<style>')
    h('  * { box-sizing: border-box; margin: 0; padding: 0; }')
    h('  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f7fa; color: #1a1a2e; padding: 2rem; max-width: 1200px; margin: 0 auto; }')
    h('  h1 { font-size: 1.8rem; margin-bottom: 0.3rem; }')
    h('  .subtitle { color: #666; font-size: 0.95rem; margin-bottom: 1.5rem; }')
    h('  .tabs { display: flex; gap: 0; margin-bottom: 2rem; border-bottom: 2px solid #e5e7eb; flex-wrap: wrap; }')
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
    h(f'<h1>Pulsar vs Direct GCP Batch: {workflow_title}</h1>')
    h(f'<p class="subtitle">{workflow_title} &mdash; {step_count} tool types &mdash; {len(all_stats)} runs</p>')
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
        safe_id = re.sub(r'[^a-zA-Z0-9]', '-', size.lower())
        tid = f"tab-{safe_id}"
        b_stats = matchups[size]["batch"]
        p_stats = matchups[size]["pulsar"]
        b_wall = sum(s["wall_clock"] for s in b_stats) / len(b_stats)
        p_wall = sum(s["wall_clock"] for s in p_stats) / len(p_stats)
        b_comp = sum(s["compute"] for s in b_stats) / len(b_stats)
        p_comp = sum(s["compute"] for s in p_stats) / len(p_stats)

        b_ok = sum(s["ok_steps"] for s in b_stats) // len(b_stats)
        p_ok = sum(s["ok_steps"] for s in p_stats) // len(p_stats)

        h(f'<div class="tab-content" id="{tid}">')
        h('  <div class="summary-cards">')
        h(f'    <div class="card batch"><div class="label">Batch Compute</div><div class="value">{b_comp/60:.1f} min</div><div class="detail">{b_comp:.0f}s across {b_ok} steps</div></div>')
        h(f'    <div class="card pulsar"><div class="label">Pulsar Compute</div><div class="value">{p_comp/60:.1f} min</div><div class="detail">{p_comp:.0f}s across {p_ok} steps</div></div>')
        diff_pct = (p_comp - b_comp) / b_comp * 100 if b_comp > 0 else 0
        h(f'    <div class="card overhead"><div class="label">Compute Difference</div><div class="value">{diff_pct:+.0f}%</div><div class="detail">{p_comp - b_comp:+.0f}s</div></div>')
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
    if pulsar_slots_fixed:
        h('    <div class="card pulsar"><div class="label">GALAXY_SLOTS Reporting</div><div class="value">Fixed</div><div class="detail">Pulsar now correctly reports slot count</div></div>')
    else:
        h('    <div class="card pulsar"><div class="label">GALAXY_SLOTS Reporting</div><div class="value">slots=1</div><div class="detail">Galaxy reports 1 slot (metric gap, not actual VM cores)</div></div>')
    h('  </div>')
    if first_matchup:
        h('  <div class="chart-container"><h2>Galaxy-Reported CPU Slots: Batch vs Pulsar</h2><p class="chart-desc">Batch sets GALAXY_SLOTS explicitly. Pulsar relies on CLUSTER_SLOTS_STATEMENT.sh fallback.</p><canvas id="slotsChart" height="100"></canvas></div>')
        h('  <div class="chart-container"><h2>Runtime Ratio vs Batch Slot Count</h2><p class="chart-desc">If Pulsar were truly 1-thread, overhead % would match slot count. Actual ratios are lower.</p><canvas id="impactChart" height="100"></canvas></div>')
    h('</div>')
    h('')

    # Footer
    h('<div class="footer">')
    h(f'  Galaxy 26.1 &middot; GCP Batch us-east4 &middot; {len(all_stats)} workflow runs &middot; Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>')
    h('')

    # ===== JAVASCRIPT =====
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
        safe = re.sub(r'[^a-zA-Z0-9]', '_', size.lower())
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
        safe = re.sub(r'[^a-zA-Z0-9]', '_', size.lower())
        safe_id = re.sub(r'[^a-zA-Z0-9]', '-', size.lower())
        tid = f"tab-{safe_id}"

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
        safe = re.sub(r'[^a-zA-Z0-9]', '_', first_matchup.lower())

        # Determine Pulsar slots for the chart
        if pulsar_slots_fixed:
            # Use actual Pulsar slot data
            p_slots_data = avg_tool_slots([s for s in all_stats if s["cloud"] == "pulsar"])
            pulsar_slots_arr = [p_slots_data.get(t, 0) for t in tool_order]
        else:
            pulsar_slots_arr = [1] * len(tool_order)

        h(f'const batchSlots = batchSlots_{safe};')
        h(f'const pulsarSlots = {json.dumps([round(v) for v in pulsar_slots_arr])};')
        h('new Chart(document.getElementById("slotsChart"), {')
        h('  type: "bar", data: { labels: tools, datasets: [')
        h('    { label: "Batch slots", data: batchSlots, backgroundColor: blue, borderRadius: 4 },')
        pulsar_slots_label = "Pulsar slots" if pulsar_slots_fixed else "Pulsar slots (reported)"
        h(f'    {{ label: "{pulsar_slots_label}", data: pulsarSlots, backgroundColor: amber, borderRadius: 4 }}')
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

    parser = argparse.ArgumentParser(description="Generate docs from metrics JSON files.")
    parser.add_argument("metrics_dir", nargs="?",
                        default=os.path.join(base_dir, "metrics", "Pulsar-vs-Batch"),
                        help="Directory containing metrics JSON files")
    parser.add_argument("--exclude", action="append", default=[],
                        help="Exclude workflow runs whose inputs contain this string (repeatable)")
    args = parser.parse_args()

    metrics_dir = args.metrics_dir
    exclude_patterns = args.exclude

    # Determine output directory from experiment name
    experiment_name = os.path.basename(metrics_dir)
    # Default experiment goes to docs/, others to docs/<experiment>/
    if experiment_name == "Pulsar-vs-Batch":
        docs_dir = os.path.join(base_dir, "docs")
    else:
        docs_dir = os.path.join(base_dir, "docs", experiment_name)

    os.makedirs(docs_dir, exist_ok=True)

    print(f"Loading metrics from {metrics_dir}...")
    jobs = load_metrics(metrics_dir)

    # Filter out excluded patterns
    if exclude_patterns:
        before = len(jobs)
        jobs = [j for j in jobs
                if not any(pat in j["inputs"] for pat in exclude_patterns)]
        excluded = before - len(jobs)
        if excluded:
            print(f"  Excluded {excluded} jobs matching: {', '.join(exclude_patterns)}")

    groups = group_by_history(jobs)

    all_stats = [history_stats(g) for g in groups.values()]

    # Discover tools dynamically
    tool_order, tool_short = discover_tool_order(jobs)

    matchups = find_matchups(all_stats)

    print(f"  {len(jobs)} jobs across {len(all_stats)} workflow runs")
    print(f"  {len(tool_order)} unique tools: {', '.join(tool_order)}")
    print(f"  Matchups: {', '.join(matchups.keys()) if matchups else 'none'}")

    # Report failed jobs
    total_failed = sum(s["failed_steps"] for s in all_stats)
    if total_failed > 0:
        print(f"  {total_failed} failed/errored jobs")
    print()

    md_path = os.path.join(docs_dir, "index.md")
    md = generate_markdown(all_stats, matchups, experiment_name, tool_order, tool_short)
    with open(md_path, "w") as f:
        f.write(md)
    print(f"  Wrote {md_path}")

    html_path = os.path.join(docs_dir, "charts.html")
    html = generate_html(all_stats, matchups, experiment_name, tool_order, tool_short)
    with open(html_path, "w") as f:
        f.write(html)
    print(f"  Wrote {html_path}")


if __name__ == "__main__":
    main()
