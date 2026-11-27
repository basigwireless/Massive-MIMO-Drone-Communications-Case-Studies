"""
Core analytical model for massive-MIMO drone (UAV) communications.

Python port of the closed-form expressions in ``Magazine_Plots.m``
(original MATLAB author: Prabhu Chandhar, Chandhar Research Labs, Chennai, India).

Notation
--------
M      : number of ground-station (GS) antennas
K      : number of drones served simultaneously
rho_u  : uplink data SNR (linear)
rho_p  : pilot SNR (linear)
B      : system bandwidth (Hz)
Bc     : coherence bandwidth (Hz)
fc     : carrier frequency (Hz)
v      : drone speed (m/s)
"""

import numpy as np

C = 3e8          # speed of light (m/s)
N0 = 2e-20       # noise PSD (W/Hz)  ~ k*T*NF with T=300 K, NF=7 dB


def coherence_time(v, fc):
    """Channel coherence time Tc = c / (2 v fc) in seconds."""
    return C / (2.0 * v * fc)


def pilot_efficiency(K, v, fc, Bc):
    """Fraction of the coherence interval left for data (Lambda).

    Lambda = 9/10 - K / (Bc * Tc); 10 % is reserved for other overheads,
    and K orthogonal pilots consume K of the Bc*Tc symbols per interval.
    """
    K = np.asarray(K, dtype=float)
    return 0.9 - K * 2.0 * v * fc / (Bc * C)


def sinr_denominator(K, rho_u, rho_p, perfect_csi=False):
    """Effective interference-plus-noise term of the ZF/MRC-type SINR."""
    K = np.asarray(K, dtype=float)
    rho_u = np.asarray(rho_u, dtype=float)
    est = 0.0 if perfect_csi else (1.0 / (rho_u * rho_p)) * (1.0 + K * rho_u)
    return rho_u * (K - 1.0) + 1.0 + est


def sum_throughput(K, M, rho_u, rho_p, B, Bc, fc, v, perfect_csi=False):
    """Uplink sum throughput (bit/s) of K drones served by an M-antenna GS."""
    lam = pilot_efficiency(K, v, fc, Bc)
    sinr = M * np.asarray(rho_u, dtype=float) / sinr_denominator(K, rho_u, rho_p, perfect_csi)
    return B * np.asarray(K, dtype=float) * lam * np.log2(1.0 + sinr)


def free_space_range(Pt, fc, B, rho_u, N0=N0):
    """Free-space range (m) at which received SNR equals rho_u."""
    return np.sqrt(Pt) * C / (fc * 4.0 * np.pi * np.sqrt(N0 * B * rho_u))


def required_antennas(K, rho_u, rho_p, per_drone_rate, B, Bc, fc, v):
    """Minimum number of GS antennas M so each drone achieves ``per_drone_rate`` bit/s."""
    lam = pilot_efficiency(K, v, fc, Bc)
    pre = K - 1.0 + 1.0 / rho_u + (1.0 / (rho_u ** 2 * rho_p)) * (1.0 + K * rho_u)
    return pre * (2.0 ** (per_drone_rate / (B * lam)) - 1.0)
