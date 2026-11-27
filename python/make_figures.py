"""
Reproduce the figures of ``Magazine_Plots.m`` in Python and save them to ../figures.

Usage:  python make_figures.py [--drops 1000] [--seed 1]
"""

import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from mimo_drone import N0, C, free_space_range, sum_throughput
from pol_mismatch import pol_mismatch

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "figures")

# Categorical palette (fixed order) + text/grid inks
S1, S2, S3, S4 = "#257de0", "#f47230", "#00b894", "#f2a600"
INK, MUTED, GRID, AXIS = "#1a1a1a", "#5c5c5c", "#e7e7e7", "#c2c2c2"

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 200, "font.size": 10.5,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK, "axes.titlecolor": INK,
    "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlelocation": "left",
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": MUTED, "ytick.color": MUTED, "lines.linewidth": 2,
    "legend.frameon": False, "legend.labelcolor": INK,
})


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print("saved", os.path.relpath(path, os.path.join(HERE, "..")))


def fig2a():
    """Sum throughput vs number of drones for three data SNRs."""
    K = np.arange(10, 1001, 10)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for snr_db, col in [(10, S1), (0, S2), (-10, S3)]:
        R = sum_throughput(K, M=100, rho_u=10 ** (snr_db / 10), rho_p=100,
                           B=20e6, Bc=3e6, fc=2.4e9, v=30)
        ax.plot(K, R / 1e9, color=col, label=f"Data SNR = {snr_db} dB")
    ax.set(xlim=(0, 1000), ylim=(1, 2.2), xlabel="Number of drones, K",
           ylabel="Sum throughput (Gbps)")
    ax.set_title("Fig. 2a  Sum throughput vs number of drones (M = 100, 2.4 GHz, v = 30 m/s)", fontsize=10.5)
    ax.legend(loc="lower right")
    save(fig, "fig2a_throughput_vs_drones.png")


def fig2b(n_drops, seed):
    """CDF of required transmit power under polarization / orientation mismatch."""
    fc = 2.4e9
    lam = C / fc
    common = dict(M=100, R=500, isotropic=False, delta=0.5 * lam, lam=lam, N0=N0, B=20e6,
                  n_drops=n_drops)
    circ = np.array([1j, 1j]) / np.sqrt(2)
    lin = np.array([1, 0])
    cases = [
        ("Circular, identical GS orientation", circ, True, S1, "-"),
        ("Circular, random GS orientation", circ, False, S2, "--"),
        ("Linear, identical GS orientation", lin, True, S3, "-"),
        ("Linear, random GS orientation", lin, False, S4, "--"),
    ]
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for i, (lbl, E, ident, col, ls) in enumerate(cases):
        _, Pt = pol_mismatch(E_GS=E, E_UAV=E, identical=ident, rng=seed + i, **common)
        p_dbm = np.sort(10 * np.log10(Pt[np.isfinite(Pt) & (Pt > 0)]) + 30)
        ax.step(p_dbm, np.arange(1, p_dbm.size + 1) / p_dbm.size, where="post",
                color=col, ls=ls, label=lbl)
        print(f"  fig2b {lbl}: median Pt = {np.median(p_dbm):.1f} dBm")
    ax.set(xlabel="Required transmit power (dBm)", ylabel="CDF", ylim=(0, 1.02))
    ax.set_xlim(right=np.percentile(p_dbm, 99) + 5)
    ax.set_title("Fig. 2b  Transmit power needed under antenna-orientation mismatch", fontsize=10.5)
    ax.legend(loc="lower right", fontsize=9)
    save(fig, "fig2b_pol_mismatch_cdf.png")


def fig3a():
    """Sum throughput vs data SNR at 2.4 GHz and 60 GHz."""
    snr_db = np.arange(-20, 21)
    rho = 10 ** (snr_db / 10)
    kw = dict(M=100, rho_p=100, B=20e6, Bc=3e6, v=30)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for K, csi, ls in [(20, False, "-"), (2, True, ":")]:
        for fc, col, name in [(2.4e9, S1, "2.4 GHz"), (60e9, S2, "60 GHz")]:
            R = sum_throughput(K, rho_u=rho, fc=fc, perfect_csi=csi, **kw)
            tag = "imperfect CSI" if not csi else "perfect CSI"
            ax.plot(snr_db, R / 1e9, color=col, ls=ls, label=f"{name}, K = {K} ({tag})")
    ax.set(xlim=(-20, 20), xlabel="Data SNR (dB)", ylabel="Sum throughput (Gbps)")
    ax.set_title("Fig. 3a  Sum throughput vs data SNR (M = 100, v = 30 m/s)", fontsize=10.5)
    ax.legend(loc="center right", fontsize=9)
    save(fig, "fig3a_throughput_vs_snr.png")


def fig3b():
    """Range and sum throughput vs bandwidth at 60 GHz (two panels, shared x-axis)."""
    B = np.arange(10, 501) * 1e6
    fc, Pt, K, M, v = 60e9, 0.1, 20, 145, 20
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(6.4, 6.0), sharex=True)
    for snr_db, col in [(-10, S1), (0, S2)]:
        a1.plot(B / 1e6, free_space_range(Pt, fc, B, 10 ** (snr_db / 10)), color=col,
                label=f"Data SNR = {snr_db} dB")
    a1.set(ylim=(0, 250), ylabel="Range (m)")
    a1.set_title("Fig. 3b  60 GHz link: range and throughput vs bandwidth (Pt = 100 mW)", fontsize=10.5)
    a1.legend(loc="upper right")

    R = sum_throughput(K, M, rho_u=0.1, rho_p=100, B=B, Bc=3e6, fc=fc, v=v)
    a2.plot(B / 1e6, R / 1e9, color=S1)
    a2.set(xlim=(10, 500), ylim=(0, 40), xlabel="Bandwidth (MHz)",
           ylabel="Sum throughput (Gbps)")
    a2.text(0.02, 0.9, "K = 20, M = 145, data SNR = -10 dB", transform=a2.transAxes,
            color=MUTED, fontsize=9)
    save(fig, "fig3b_range_throughput_vs_bandwidth.png")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--drops", type=int, default=1000, help="Monte-Carlo drops for Fig. 2b")
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()
    fig2a()
    fig2b(args.drops, args.seed)
    fig3a()
    fig3b()
