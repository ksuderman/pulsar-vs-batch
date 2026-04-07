#!/usr/bin/env python3
"""Generate docs/index.md and docs/charts.html from metrics JSON files.

Usage:
    python3 bin/generate_docs.py [metrics_dir]

Reads all JSON files from metrics/<experiment>/ and produces:
    docs/<experiment>/index.md   - Markdown results report
    docs/<experiment>/charts.html - Interactive Chart.js dashboard

Supports any number of cloud runners and any workflow — tools are discovered
dynamically from the data, sorted by average runtime (descending).
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
# Constants
# ---------------------------------------------------------------------------

SIZE_ORDER = {"2GB": 0, "5GB": 1, "10GB": 2}

# Map dataset identifiers to canonical size labels
INPUT_SIZE_MAP = {
    "SRR24043307-80": "2GB",
    "SRR24043307-50": "5GB",
    "SRR24043307-full": "10GB",
    "chipseq-10g": "10GB",
    "chipseq-5g": "5GB",
    "chipseq-2g": "2GB",
}

CLOUD_DISPLAY = {
    "batch": "Direct",
    "pulsar": "Pulsar",
    "pulsar+k8s": "Pulsar+K8s",
    "single": "Direct+K8s",
}


def cloud_display(cloud):
    return CLOUD_DISPLAY.get(cloud, cloud.title())


CLOUD_COLORS = {
    "batch":  ("#3b82f6", "#93bbfd"),
    "pulsar": ("#f59e0b", "#fcd679"),
    "single": ("#22c55e", "#86efac"),
}
_EXTRA_COLORS = [("#8b5cf6", "#c4b5fd"), ("#ef4444", "#fca5a5")]


def cloud_color(cloud, idx=0):
    if cloud in CLOUD_COLORS:
        return CLOUD_COLORS[cloud]
    return _EXTRA_COLORS[idx % len(_EXTRA_COLORS)]


def size_sort_key(size_str):
    return SIZE_ORDER.get(size_str, 999)


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
            elif m["name"] == "start_epoch":
                start = float(m["raw_value"])
            elif m["name"] == "end_epoch":
                end = float(m["raw_value"])
            elif m["name"] == "galaxy_slots":
                slots = float(m["raw_value"])
            elif m["name"] == "galaxy_memory_mb":
                mem = float(m["raw_value"])
        jobs.append({
            "run": d["run"], "cloud": d["cloud"],
            "history_id": d["history_id"],
            "tool": tool, "state": d["metrics"]["state"],
            "runtime": runtime or 0, "start_epoch": start, "end_epoch": end,
            "create_time": d["metrics"]["create_time"],
            "update_time": d["metrics"]["update_time"],
            "inputs": d.get("inputs", ""), "server": d.get("server", ""),
            "slots": slots or 0, "mem_mb": mem or 0,
        })
    return jobs


def get_size_label(inputs_str):
    # Find all matching patterns and return the largest size
    matched = [label for pattern, label in INPUT_SIZE_MAP.items() if pattern in inputs_str]
    if matched:
        return max(matched, key=lambda l: SIZE_ORDER.get(l, 999))
    size_values = {"2GB": 2, "5GB": 5, "10GB": 10}
    sizes = [s for s in size_values if s in inputs_str]
    if sizes:
        return max(sizes, key=lambda s: size_values[s])
    tokens = inputs_str.strip().split()
    if not tokens:
        return "unknown"
    ref_ext = {".gtf", ".gbff", ".gbff.gz", ".fa", ".fa.gz", ".fasta",
               ".fasta.gz", ".bed", ".gff", ".gff3", ".len"}
    data = [t for t in tokens if not any(t.lower().endswith(e) for e in ref_ext)]
    if data:
        return " ".join(sorted(set(data)))
    return f"input-{hashlib.sha256(inputs_str.encode()).hexdigest()[:8]}"


def discover_clouds(all_stats):
    return sorted(set(s["cloud"] for s in all_stats))


def discover_tool_order(jobs):
    tool_runtimes = defaultdict(list)
    all_tools = set()
    for j in jobs:
        all_tools.add(j["tool"])
        if j["state"] == "ok" and j["runtime"] > 0:
            tool_runtimes[j["tool"]].append(j["runtime"])
    for t in all_tools:
        if t not in tool_runtimes:
            tool_runtimes[t] = [0]
    tool_order = sorted(tool_runtimes.keys(),
                        key=lambda t: sum(tool_runtimes[t]) / len(tool_runtimes[t]),
                        reverse=True)
    tool_short = {}
    for t in tool_order:
        tool_short[t] = t[:12] if len(t) > 12 else t
    seen = {}
    for t in tool_order:
        short = tool_short[t]
        if short in seen:
            idx = 2
            while f"{short[:10]}_{idx}" in seen.values():
                idx += 1
            tool_short[t] = f"{short[:10]}_{idx}"
        seen[tool_short[t]] = t
    return tool_order, tool_short


def derive_experiment_title(name):
    title = name
    for prefix in ["Pulsar-vs-Batch-", "Pulsar-vs-Batch"]:
        if title.startswith(prefix):
            title = title[len(prefix):]
            break
    if not title:
        title = "Variant Analysis"
    return title.replace("-", " ")


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
    ok_jobs = [j for j in jobs if j["state"] == "ok"]
    compute = sum(j["runtime"] for j in ok_jobs)
    return {
        "cloud": jobs[0]["cloud"], "run": jobs[0]["run"],
        "history_id": jobs[0]["history_id"],
        "size": get_size_label(jobs[0]["inputs"]),
        "wall_clock": wall_clock, "compute": compute,
        "overhead": wall_clock - compute,
        "steps": len(jobs), "ok_steps": len(ok_jobs),
        "failed_steps": len(jobs) - len(ok_jobs),
        "failed_tools": [j["tool"] for j in jobs if j["state"] != "ok"],
        "server": jobs[0]["server"],
        "date_start": min(creates).strftime("%Y-%m-%d"),
        "date_end": max(updates).strftime("%Y-%m-%d"),
        "jobs": jobs,
    }


# ---------------------------------------------------------------------------
# Matching & comparison helpers
# ---------------------------------------------------------------------------

def find_matchups(all_stats):
    """Find size groups where at least 2 clouds have data."""
    by_size = defaultdict(lambda: defaultdict(list))
    for s in all_stats:
        by_size[s["size"]][s["cloud"]].append(s)
    matchups = {}
    for size in sorted(by_size.keys(), key=size_sort_key):
        clouds = dict(by_size[size])
        if len(clouds) >= 2:
            matchups[size] = clouds
    return matchups


def avg_tool_times(stats_list):
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
    tool_slots = defaultdict(list)
    for s in stats_list:
        per_history = defaultdict(float)
        for j in s["jobs"]:
            if j["state"] == "ok" and j["slots"] > 0:
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
    clouds = discover_clouds(all_stats)
    all_tools = set()
    for s in all_stats:
        for j in s["jobs"]:
            all_tools.add(j["tool"])

    lines = []
    w = lines.append

    all_dates = set()
    servers = {}
    for s in all_stats:
        all_dates.add(s["date_start"]); all_dates.add(s["date_end"])
        servers[s["cloud"]] = s["server"]

    w("---")
    w(f"title: {workflow_title} Benchmark")
    w("---")
    w("")
    w(f"# {workflow_title} Benchmark")
    w("")
    w("**[Home](../index.html)** | "
      "**[Interactive Charts](charts.html)** | "
      "**[Cost Summary](costs.html)** | "
      "**[Cost Charts](cost-charts.html)**")
    w("")

    # Setup
    w("## Experiment Setup")
    w("")
    w(f"- **Workflow:** {workflow_title} ({len(all_tools)} unique tool types)")
    w("- **Galaxy version:** 26.1")
    w("- **Infrastructure:** GCE VM on RKE2 Kubernetes (us-east4)")
    w(f"- **Runners:** {', '.join(clouds)}")
    for c in clouds:
        if c in servers:
            w(f"- **{cloud_display(c)} server:** {servers[c]}")
    w(f"- **Date:** {min(all_dates)} to {max(all_dates)}")
    w("")

    # Workflow runs
    total_jobs = sum(s["steps"] for s in all_stats)
    total_ok = sum(s["ok_steps"] for s in all_stats)
    total_failed = total_jobs - total_ok
    w("### Workflow Runs")
    w("")
    if total_failed == 0:
        w(f"{len(all_stats)} workflow invocations, {total_jobs} total jobs. All completed successfully.")
    else:
        w(f"{len(all_stats)} workflow invocations, {total_jobs} total jobs ({total_ok} succeeded, {total_failed} failed/errored).")
    w("")

    # Failed jobs
    if total_failed > 0:
        w("### Failed/Errored Jobs")
        w("")
        failed_by = defaultdict(lambda: defaultdict(list))
        for s in all_stats:
            for j in s["jobs"]:
                if j["state"] != "ok":
                    failed_by[s["cloud"]][j["tool"]].append(j["state"])
        w("| Cloud | Tool | State | Count |")
        w("|-------|------|-------|-------|")
        from collections import Counter
        for cloud in sorted(failed_by.keys()):
            for tool in sorted(failed_by[cloud].keys()):
                for state, count in sorted(Counter(failed_by[cloud][tool]).items()):
                    w(f"| {cloud} | {tool} | {state} | {count} |")
        w("")

    # All runs table
    w("## Results Summary")
    w("")
    w("### All Runs")
    w("")
    w("| Runner | Run | Input Size | Wall Clock | Compute Time | Scheduling Overhead | Steps OK |")
    w("|--------|-----|------------|-----------|-------------|-------------------|----------|")
    for s in sorted(all_stats, key=lambda x: (x["cloud"], x["run"], size_sort_key(x["size"]))):
        oh_pct = f"{s['overhead'] / s['wall_clock'] * 100:.0f}%" if s["wall_clock"] > 0 else "--"
        w(f"| {s['cloud']} | {s['run']} | {s['size']} | {fmt_min(s['wall_clock'])} min | "
          f"{fmt_min(s['compute'])} min | {fmt_min(s['overhead'])} min ({oh_pct}) | "
          f"{s['ok_steps']}/{s['steps']} |")
    w("")

    # Head-to-head per size
    for size, size_clouds in sorted(matchups.items(), key=lambda x: size_sort_key(x[0])):
        present = sorted(size_clouds.keys())
        w(f"### Comparison: {size}")
        w("")
        header = "| Metric |"
        sep = "|--------|"
        for c in present:
            n = len(size_clouds[c])
            label = f"{cloud_display(c)} (avg of {n})" if n > 1 else cloud_display(c)
            header += f" {label} |"
            sep += f" {'-' * max(len(label), 5)} |"
        w(header)
        w(sep)
        # Compute per-cloud averages
        avgs = {}
        for c in present:
            stats = size_clouds[c]
            avgs[c] = {
                "wall": sum(s["wall_clock"] for s in stats) / len(stats),
                "comp": sum(s["compute"] for s in stats) / len(stats),
                "oh": sum(s["overhead"] for s in stats) / len(stats),
                "ok": sum(s["ok_steps"] for s in stats) // len(stats),
                "total": stats[0]["steps"],
            }
        for metric, key in [("Wall clock", "wall"), ("Compute time", "comp"), ("Scheduling overhead", "oh")]:
            row = f"| **{metric}** |"
            for c in present:
                row += f" {fmt_min(avgs[c][key])} min |"
            w(row)
        row = "| Steps completed |"
        for c in present:
            row += f" {avgs[c]['ok']}/{avgs[c]['total']} |"
        w(row)
        w("")

    # Per-step compute time tables
    w("## Per-Step Compute Time (runtime_seconds)")
    w("")
    for size, size_clouds in sorted(matchups.items(), key=lambda x: size_sort_key(x[0])):
        present = sorted(size_clouds.keys())
        times = {c: avg_tool_times(size_clouds[c]) for c in present}
        w(f"### {size}")
        w("")
        header = "| Tool |"
        sep = "|------|"
        for c in present:
            header += f" {cloud_display(c)} |"
            sep += " ------- |"
        w(header)
        w(sep)
        totals = {c: 0 for c in present}
        for tool in tool_order:
            if not any(tool in times[c] for c in present):
                continue
            row = f"| {tool} |"
            for c in present:
                v = times[c].get(tool, 0)
                totals[c] += v
                row += f" {v:.0f}s |"
            w(row)
        row = "| **Total** |"
        for c in present:
            row += f" **{totals[c]:.0f}s** |"
        w(row)
        w("")

    # Wall Clock vs Compute Time
    w("## Wall Clock vs Compute Time")
    w("")
    w("| Runner | Input | Wall Clock | Compute | Overhead | Overhead % |")
    w("|--------|-------|-----------|---------|----------|------------|")
    for s in sorted(all_stats, key=lambda x: (x["cloud"], size_sort_key(x["size"]))):
        oh_pct = f"{s['overhead'] / s['wall_clock'] * 100:.0f}%" if s["wall_clock"] > 0 else "--"
        w(f"| {s['cloud']} R{s['run']} | {s['size']} | {fmt_min(s['wall_clock'])}m | "
          f"{fmt_min(s['compute'])}m | {fmt_min(s['overhead'])}m | {oh_pct} |")
    w("")

    # Scaling analysis per cloud
    for cloud in clouds:
        cloud_stats = sorted([s for s in all_stats if s["cloud"] == cloud],
                             key=lambda x: size_sort_key(x["size"]))
        sizes = list(dict.fromkeys(s["size"] for s in cloud_stats))
        if len(sizes) > 1:
            w(f"## {cloud_display(cloud)} Scaling Analysis")
            w("")
            by_size = defaultdict(list)
            for s in cloud_stats:
                by_size[s["size"]].append(s)
            w("| Input | Wall Clock | Compute |")
            w("|-------|-----------|---------|")
            for sz in sorted(by_size.keys(), key=size_sort_key):
                avg_wall = sum(s["wall_clock"] for s in by_size[sz]) / len(by_size[sz])
                avg_comp = sum(s["compute"] for s in by_size[sz]) / len(by_size[sz])
                n = len(by_size[sz])
                label = f"{sz} (avg of {n})" if n > 1 else sz
                w(f"| {label} | {fmt_min(avg_wall)}m | {fmt_min(avg_comp)}m |")
            w("")

    # Key Findings
    w("## Key Findings")
    w("")
    finding_num = 1
    for size, size_clouds in sorted(matchups.items(), key=lambda x: size_sort_key(x[0])):
        present = sorted(size_clouds.keys())
        walls = {}
        comps = {}
        for c in present:
            stats = size_clouds[c]
            walls[c] = sum(s["wall_clock"] for s in stats) / len(stats)
            comps[c] = sum(s["compute"] for s in stats) / len(stats)
        fastest = min(present, key=lambda c: walls[c])
        w(f"### {finding_num}. {size}: Wall clock comparison")
        w("")
        for c in present:
            if c == fastest:
                w(f"- **{cloud_display(c)}**: {fmt_min(walls[c])}m (fastest)")
            else:
                w(f"- **{cloud_display(c)}**: {fmt_min(walls[c])}m ({fmt_pct(walls[c] - walls[fastest], walls[fastest])})")
        w("")
        finding_num += 1

    # Per-cloud scheduling overhead
    w(f"### {finding_num}. Scheduling overhead per step")
    w("")
    for cloud in clouds:
        cloud_stats = [s for s in all_stats if s["cloud"] == cloud]
        if cloud_stats:
            oh = [s["overhead"] / s["steps"] for s in cloud_stats if s["steps"] > 0]
            if oh:
                w(f"- **{cloud_display(cloud)}**: {sum(oh)/len(oh)/60:.1f} min/step avg")
    w("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML chart generation
# ---------------------------------------------------------------------------

def generate_html(all_stats, matchups, experiment_name, tool_order, tool_short):
    workflow_title = derive_experiment_title(experiment_name)
    clouds = discover_clouds(all_stats)
    all_tools = set()
    for s in all_stats:
        for j in s["jobs"]:
            all_tools.add(j["tool"])

    # Assign colors
    cc = {}
    extra_idx = 0
    for c in clouds:
        if c in CLOUD_COLORS:
            cc[c] = CLOUD_COLORS[c]
        else:
            cc[c] = _EXTRA_COLORS[extra_idx % len(_EXTRA_COLORS)]
            extra_idx += 1

    # Chart data per size
    chart_data = {}
    for size, size_clouds in sorted(matchups.items(), key=lambda x: size_sort_key(x[0])):
        chart_data[size] = {}
        for cloud in sorted(size_clouds.keys()):
            times = avg_tool_times(size_clouds[cloud])
            slots = avg_tool_slots(size_clouds[cloud])
            chart_data[size][cloud] = {
                "times": [round(times.get(t, 0)) for t in tool_order],
                "slots": [round(slots.get(t, 0)) for t in tool_order],
            }

    # Overview data
    overview_data = []
    for s in sorted(all_stats, key=lambda x: (x["cloud"], size_sort_key(x["size"]), x["run"])):
        overview_data.append({
            "label": f"{s['cloud']} R{s['run']} {s['size']}",
            "compute": round(s["compute"] / 60, 1),
            "overhead": round(s["overhead"] / 60, 1),
            "cloud": s["cloud"],
        })

    tools_json = json.dumps([tool_short.get(t, t) for t in tool_order])
    matchup_sizes = sorted(matchups.keys(), key=size_sort_key)

    # Tab IDs
    tab_ids = ["overview"]
    tab_labels = ["Overview"]
    for size in matchup_sizes:
        safe_id = re.sub(r'[^a-zA-Z0-9]', '-', size.lower())
        tab_ids.append(f"tab-{safe_id}")
        tab_labels.append(size)

    html = []
    h = html.append

    h('<!DOCTYPE html>')
    h('<html lang="en">')
    h('<head>')
    h('<meta charset="UTF-8">')
    h('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    h(f'<title>{workflow_title} Benchmark Charts</title>')
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
    h('  .chart-container { background: #fff; border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }')
    h('  .chart-container h2 { font-size: 1.1rem; margin-bottom: 0.3rem; }')
    h('  .chart-container .chart-desc { font-size: 0.85rem; color: #888; margin-bottom: 1rem; }')
    h('  .footer { text-align: center; color: #aaa; font-size: 0.8rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; }')
    h('</style>')
    h('</head>')
    h('<body>')
    h('')
    h(f'<h1>{workflow_title} Benchmark</h1>')
    h(f'<p class="subtitle">{len(all_tools)} tool types &mdash; {len(all_stats)} runs &mdash; {", ".join(cloud_display(c) for c in clouds)}</p>')
    h('')
    h('<div class="nav">')
    h('  <a href="../index.html">&larr; Home</a>')
    h('  <a href="index.html">Results Report</a>')
    h('  <a href="costs.html">Cost Summary</a>')
    h('  <a href="cost-charts.html">Cost Charts</a>')
    h('</div>')
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
    h('    <p class="chart-desc">Stacked bars: compute time (solid) + scheduling/staging overhead (lighter) for each run.</p>')
    h('    <canvas id="overviewStacked" height="80"></canvas>')
    h('  </div>')
    h('  <div class="chart-container">')
    h('    <h2>Per-Step Scheduling Overhead</h2>')
    h('    <p class="chart-desc">Average overhead per workflow step.</p>')
    h('    <canvas id="overviewOHPerStep" height="80"></canvas>')
    h('  </div>')
    h('</div>')
    h('')

    # ===== SIZE COMPARISON TABS =====
    for size in matchup_sizes:
        safe_id = re.sub(r'[^a-zA-Z0-9]', '-', size.lower())
        tid = f"tab-{safe_id}"
        h(f'<div class="tab-content" id="{tid}">')
        h(f'  <div class="chart-container"><h2>Per-Step Compute Time &mdash; {size}</h2>')
        h(f'    <p class="chart-desc">Actual runtime_seconds per tool, all runners.</p>')
        h(f'    <canvas id="bar_{tid}" height="100"></canvas></div>')
        h(f'  <div class="chart-container"><h2>Cumulative Compute &mdash; {size}</h2>')
        h(f'    <p class="chart-desc">Running total of compute seconds.</p>')
        h(f'    <canvas id="cum_{tid}" height="100"></canvas></div>')
        h('</div>')
        h('')

    # Footer
    h('<div class="footer">')
    h(f'  Galaxy 26.1 &middot; us-east4 &middot; {len(all_stats)} workflow runs &middot; Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>')
    h('')

    # ===== JAVASCRIPT =====
    h('<script>')
    h(f'const tools = {tools_json};')
    h('Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif";')
    h('Chart.defaults.font.size = 12;')
    h('const secTooltip = ctx => `${ctx.dataset.label}: ${ctx.raw}s (${(ctx.raw/60).toFixed(1)}m)`;')
    h('function cumSum(arr) { let s=0; return arr.map(v => s += v); }')
    h('')

    # Emit per-size data
    for size in matchup_sizes:
        safe = re.sub(r'[^a-zA-Z0-9]', '_', size.lower())
        for cloud in sorted(chart_data[size].keys()):
            csafe = re.sub(r'[^a-zA-Z0-9]', '_', cloud)
            h(f'const data_{csafe}_{safe} = {json.dumps(chart_data[size][cloud]["times"])};')
    h('')

    # Overview stacked chart
    h(f'const ovLabels = {json.dumps([d["label"] for d in overview_data])};')
    h(f'const ovCompute = {json.dumps([d["compute"] for d in overview_data])};')
    h(f'const ovOverhead = {json.dumps([d["overhead"] for d in overview_data])};')
    ov_colors = [cc[d["cloud"]][0] for d in overview_data]
    ov_oh_colors = [cc[d["cloud"]][1] for d in overview_data]
    h(f'const ovColors = {json.dumps(ov_colors)};')
    h(f'const ovOHColors = {json.dumps(ov_oh_colors)};')
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

    # Per-step overhead chart
    oh_labels = []
    oh_data = []
    oh_colors = []
    for s in sorted(all_stats, key=lambda x: (x["cloud"], size_sort_key(x["size"]))):
        oh_labels.append(f"{s['cloud']} R{s['run']} {s['size']}")
        oh_data.append(round(s["overhead"] / s["steps"] / 60, 1) if s["steps"] > 0 else 0)
        oh_colors.append(cc[s["cloud"]][0])
    h(f'new Chart(document.getElementById("overviewOHPerStep"), {{')
    h(f'  type: "bar",')
    h(f'  data: {{ labels: {json.dumps(oh_labels)}, datasets: [{{ label: "Overhead per step", data: {json.dumps(oh_data)}, backgroundColor: {json.dumps(oh_colors)}, borderRadius: 4 }}] }},')
    h(f'  options: {{ responsive: true, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ title: {{ display: true, text: "Minutes" }}, beginAtZero: true }}, x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }} }} }}')
    h('});')
    h('')

    # Per-size comparison charts
    for size in matchup_sizes:
        safe = re.sub(r'[^a-zA-Z0-9]', '_', size.lower())
        safe_id = re.sub(r'[^a-zA-Z0-9]', '-', size.lower())
        tid = f"tab-{safe_id}"
        present = sorted(chart_data[size].keys())

        # Bar chart
        h(f'new Chart(document.getElementById("bar_{tid}"), {{')
        h(f'  type: "bar", data: {{ labels: tools, datasets: [')
        for cloud in present:
            csafe = re.sub(r'[^a-zA-Z0-9]', '_', cloud)
            color = cc[cloud][0]
            h(f'    {{ label: "{cloud_display(cloud)}", data: data_{csafe}_{safe}, backgroundColor: "{color}", borderRadius: 4 }},')
        h(f'  ] }}, options: {{ responsive: true, plugins: {{ legend: {{ position: "top" }}, tooltip: {{ callbacks: {{ label: secTooltip }} }} }}, scales: {{ y: {{ title: {{ display: true, text: "Seconds" }}, beginAtZero: true }}, x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }} }} }}')
        h('});')

        # Cumulative chart
        h(f'new Chart(document.getElementById("cum_{tid}"), {{')
        h(f'  type: "line", data: {{ labels: tools, datasets: [')
        for cloud in present:
            csafe = re.sub(r'[^a-zA-Z0-9]', '_', cloud)
            color = cc[cloud][0]
            light = cc[cloud][1]
            h(f'    {{ label: "{cloud_display(cloud)}", data: cumSum(data_{csafe}_{safe}).map(v => +(v/60).toFixed(1)), borderColor: "{color}", backgroundColor: "{light}33", fill: true, tension: 0.3, pointRadius: 4, pointBackgroundColor: "{color}" }},')
        h(f'  ] }}, options: {{ responsive: true, plugins: {{ tooltip: {{ callbacks: {{ label: ctx => `${{ctx.dataset.label}}: ${{ctx.raw}} min` }} }} }}, scales: {{ y: {{ title: {{ display: true, text: "Minutes" }}, beginAtZero: true }}, x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }} }} }}')
        h('});')
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
# Main
# ---------------------------------------------------------------------------

def generate_experiment(jobs, experiment_name, docs_dir):
    os.makedirs(docs_dir, exist_ok=True)
    groups = group_by_history(jobs)
    all_stats = [history_stats(g) for g in groups.values()]
    tool_order, tool_short = discover_tool_order(jobs)
    matchups = find_matchups(all_stats)
    clouds = discover_clouds(all_stats)

    print(f"  {len(jobs)} jobs across {len(all_stats)} workflow runs")
    print(f"  Clouds: {', '.join(clouds)}")
    print(f"  {len(tool_order)} unique tools: {', '.join(tool_order)}")
    print(f"  Matchups: {', '.join(matchups.keys()) if matchups else 'none'}")
    total_failed = sum(s["failed_steps"] for s in all_stats)
    if total_failed > 0:
        print(f"  {total_failed} failed/errored jobs")

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


def deduplicate_jobs(jobs):
    """Remove duplicate/failed data from reruns, keeping only ok jobs."""
    by_hist = defaultdict(lambda: {"ok": 0, "fail": 0, "jobs": []})
    for j in jobs:
        key = (j["cloud"], j.get("history_id", ""))
        by_hist[key]["jobs"].append(j)
        if j["state"] == "ok":
            by_hist[key]["ok"] += 1
        else:
            by_hist[key]["fail"] += 1

    # Group histories by (cloud, size) to find duplicates
    by_group = defaultdict(list)
    for (cloud, hid), info in by_hist.items():
        size = get_size_label(info["jobs"][0].get("inputs", ""))
        by_group[(cloud, size)].append((hid, info))

    exclude_histories = set()
    for (cloud, size), histories in by_group.items():
        failed = [(hid, info) for hid, info in histories if info["fail"] > 0]
        clean = [(hid, info) for hid, info in histories if info["fail"] == 0]
        if failed and clean:
            for hid, info in failed:
                exclude_histories.add(hid)
        if len(clean) > 1:
            clean.sort(key=lambda x: max(j["create_time"] for j in x[1]["jobs"]))
            for hid, info in clean[:-1]:
                exclude_histories.add(hid)

    if exclude_histories:
        print(f"  Dedup: excluding {len(exclude_histories)} histories")

    return [j for j in jobs if j.get("history_id", "") not in exclude_histories
            and j["state"] == "ok"]


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description="Generate docs from metrics JSON files.")
    parser.add_argument("metrics_dir", nargs="*",
                        help="Directories containing metrics JSON files")
    parser.add_argument("--name", help="Experiment name for output directory")
    parser.add_argument("--inputs-match", action="append", default=[],
                        help="Only include jobs whose inputs contain this string")
    parser.add_argument("--exclude", action="append", default=[],
                        help="Exclude workflow runs whose inputs contain this string (repeatable)")
    args = parser.parse_args()

    metrics_dirs = args.metrics_dir
    if not metrics_dirs:
        metrics_dirs = [os.path.join(base_dir, "metrics", "Pulsar-vs-Batch")]

    experiment_name = args.name or os.path.basename(metrics_dirs[0])

    print(f"Loading metrics from {', '.join(metrics_dirs)}...")
    jobs = []
    for d in metrics_dirs:
        jobs.extend(load_metrics(d))
    print(f"  Loaded {len(jobs)} total jobs")

    if args.inputs_match:
        before = len(jobs)
        jobs = [j for j in jobs if any(pat in j.get("inputs", "") for pat in args.inputs_match)]
        print(f"  Filtered to inputs matching: {', '.join(args.inputs_match)} ({before - len(jobs)} removed)")

    if args.exclude:
        before = len(jobs)
        jobs = [j for j in jobs if not any(pat in j["inputs"] for pat in args.exclude)]
        if before - len(jobs):
            print(f"  Excluded {before - len(jobs)} jobs matching: {', '.join(args.exclude)}")

    jobs = deduplicate_jobs(jobs)
    print(f"  After dedup: {len(jobs)} ok jobs")

    docs_dir = os.path.join(base_dir, "docs", experiment_name)
    print(f"\n[{experiment_name}]")
    generate_experiment(jobs, experiment_name, docs_dir)


if __name__ == "__main__":
    main()
