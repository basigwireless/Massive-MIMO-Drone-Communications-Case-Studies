"""
Numerical results of the three case studies in ``Magazine_Plots.m``.

  1. 4K video surveillance swarm at 2.4 GHz (K = 23 drones)
  2. 8K/multi-camera inspection at 60 GHz (K = 20 drones)
  3. Uncompressed VGA video at 5.8 GHz (K = 25 and 50 drones)

Usage:  python case_studies.py      (prints a table and writes ../figures/case_studies.png
                                      plus ../results/case_studies.csv)
"""

import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from mimo_drone import coherence_time, free_space_range, required_antennas

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")


def video_rate(rpx, rpy, bits_per_pixel, fps, streams=1):
    """Raw (uncompressed) video bit rate in bit/s."""
    return rpx * rpy * bits_per_pixel * fps * streams


def case(name, fc, K, v, Pt, B, Bc, raw_rate, CR, rho_u=1.0, rho_p=100.0):
    Tc = coherence_time(v, fc)
    per_drone = raw_rate / CR
    return {
        "case": name,
        "fc (GHz)": fc / 1e9,
        "K": K,
        "v (m/s)": v,
        "B (MHz)": B / 1e6,
        "Bc (kHz)": Bc / 1e3,
        "Per-drone rate (Mbps)": per_drone / 1e6,
        "Sum throughput (Gbps)": K * per_drone / 1e9,
        "Coherence time (ms)": Tc * 1e3,
        "Coherence interval (symbols)": Bc * Tc,
        "Range (m)": free_space_range(Pt, fc, B, rho_u),
        "Required antennas M": required_antennas(K, rho_u, rho_p, per_drone, B, Bc, fc, v),
    }


def run():
    q4k = video_rate(2048, 4096, 24, 60)
    rows = [
        case("CS1: 2.4 GHz, Bc = 3 MHz", 2.4e9, 23, 20, 1.0, 20e6, 3e6, q4k, CR=200),
        case("CS1: 2.4 GHz, Bc = 300 kHz", 2.4e9, 23, 20, 1.0, 20e6, 300e3, q4k, CR=200),
        case("CS2: 60 GHz, B = 300 MHz", 60e9, 20, 20, 1.0, 300e6, 3e6,
             video_rate(2048, 4096, 24, 60, streams=16), CR=200),
        case("CS2: 60 GHz, B = 200 MHz", 60e9, 20, 20, 1.0, 200e6, 3e6,
             video_rate(2048, 4096, 24, 60, streams=16), CR=200),
        case("CS3: 5.8 GHz, K = 25", 5.8e9, 25, 30, 0.1, 20e6, 3e6,
             video_rate(480, 640, 8, 30), CR=1),
        case("CS3: 5.8 GHz, K = 50", 5.8e9, 50, 30, 0.1, 20e6, 3e6,
             video_rate(480, 640, 8, 30), CR=1),
    ]
    return rows


def print_table(rows):
    keys = list(rows[0])
    for r in rows:
        print("-" * 60)
        for k in keys:
            v = r[k]
            print(f"{k:32s}: {v:,.3f}" if isinstance(v, float) else f"{k:32s}: {v}")


def write_csv(rows):
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    path = os.path.join(ROOT, "results", "case_studies.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    print("saved results/case_studies.csv")


def plot(rows):
    names = [r["case"] for r in rows][::-1]
    M = [r["Required antennas M"] for r in rows][::-1]
    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    ax.barh(names, M, color="#257de0", height=0.55)
    for y, m in enumerate(M):
        ax.text(m + 12, y, f"{m:,.0f}", va="center", color="#1a1a1a", fontsize=9)
    ax.set_xlabel("Required ground-station antennas M")
    ax.set_title("Case studies: antennas needed to meet the video-rate target",
                 loc="left", fontsize=10.5, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color="#e7e7e7")
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(M) * 1.15)
    fig.tight_layout()
    os.makedirs(os.path.join(ROOT, "figures"), exist_ok=True)
    fig.savefig(os.path.join(ROOT, "figures", "case_studies_required_antennas.png"), dpi=200)
    print("saved figures/case_studies_required_antennas.png")


if __name__ == "__main__":
    rows = run()
    print_table(rows)
    write_csv(rows)
    plot(rows)
