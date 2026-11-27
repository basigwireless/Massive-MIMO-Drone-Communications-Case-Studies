"""
Monte-Carlo study of antenna-orientation / polarization mismatch between a
drone and an M-element ground-station (GS) linear array.

Python port of ``polMismatch_Mag.m`` (original MATLAB author: Prabhu Chandhar).
The per-antenna loop of the MATLAB code is vectorised over the M antennas.

Each drop places a drone uniformly inside a sphere of radius R (drops closer
than 20 m are discarded), draws a random 3-D orientation for the drone antenna
and (optionally) for every GS element, and computes the half-wave-dipole
gain-and-polarization coupling factor X_l for every element l. The transmit
power needed to reach unit SNR at the GS is then

    Pt = N0 * B * (4*pi*d / lambda)^2 / mean_l(X_l).
"""

import numpy as np


def _rotx(a):
    c, s = np.cos(np.deg2rad(a)), np.sin(np.deg2rad(a))
    return np.array([[np.ones_like(c), 0 * c, 0 * c], [0 * c, c, -s], [0 * c, s, c]])


def _roty(a):
    c, s = np.cos(np.deg2rad(a)), np.sin(np.deg2rad(a))
    return np.array([[c, 0 * c, s], [0 * c, np.ones_like(c), 0 * c], [-s, 0 * c, c]])


def _rotz(a):
    c, s = np.cos(np.deg2rad(a)), np.sin(np.deg2rad(a))
    return np.array([[c, -s, 0 * c], [s, c, 0 * c], [0 * c, 0 * c, np.ones_like(c)]])


def _rot(ax, ay, az):
    """R = Rx(ax) Ry(ay) Rz(az), angles in degrees (matches MATLAB rotx/roty/rotz).

    Scalars give a (3, 3) matrix; arrays of length M give (M, 3, 3).
    """
    rx, ry, rz = _rotx(ax), _roty(ay), _rotz(az)
    if rx.ndim == 3:  # (3, 3, M) -> (M, 3, 3)
        rx, ry, rz = (np.moveaxis(r, -1, 0) for r in (rx, ry, rz))
    return rx @ ry @ rz


def _dipole(angle):
    """Half-wave dipole field pattern cos(pi/2 cos t) / sin t."""
    return np.cos(np.pi / 2 * np.cos(angle)) / np.sin(angle)


def _acos(x):
    return np.arccos(np.clip(x, -1.0, 1.0))


def pol_mismatch(M, R, identical, isotropic, delta, E_GS, E_UAV, lam, N0, B,
                 n_drops=1000, min_dist=20.0, rng=None):
    """Return (z, Pt): mismatch factor 1/mean(X) and required Pt (W) for each drop.

    Parameters mirror ``polMismatch_Mag.m``:
    identical : True -> all GS elements identically oriented, False -> random
    isotropic : True -> ignore the dipole pattern (unit gain)
    delta     : inter-element spacing (m)
    E_GS, E_UAV : 2-element (theta, psi) polarization vectors
    """
    rng = np.random.default_rng(rng)
    E_GS = np.asarray(E_GS, dtype=complex)
    E_UAV = np.asarray(E_UAV, dtype=complex)
    l = np.arange(M)
    z_out, pt_out = [], []

    for _ in range(n_drops):
        Rk = _rot(*(rng.random(3) * 360))

        el = np.arcsin(2 * rng.random() - 1) + np.pi / 2
        az = 2 * np.pi * rng.random()
        dk = R * rng.random() ** (1 / 3)
        if dk <= min_dist:
            continue

        if identical:
            Rl = np.broadcast_to(np.eye(3), (M, 3, 3))
        else:
            Rl = _rot(*(rng.random((3, M)) * 360))

        th, ph = el, az
        # Fresnel (second-order) distance from drone to element l
        dkl = dk * (1 + (1 / (2 * dk)) * ((l * delta) ** 2 - l * delta * np.sin(th) * np.cos(ph)))
        th_l = _acos(dk * np.cos(th) / dkl)
        num = dk * np.sin(th) * np.cos(ph) - l * delta
        den = dk * np.sin(th) * np.sin(ph)
        with np.errstate(divide="ignore"):
            ph_l = np.arctan(den / num) - (np.pi / 2) * (np.sign(den) - 1)  # acot(num/den)

        u = np.stack([np.sin(th_l) * np.cos(ph_l), np.sin(th_l) * np.sin(ph_l), np.cos(th_l)], axis=1)

        t1 = _acos(-u @ Rk[2])
        p1 = _acos(-u @ Rk[1])
        t2 = _acos(np.einsum("mi,mi->m", u, Rl[:, 2]))
        p2 = _acos(np.einsum("mi,mi->m", u, Rl[:, 1]))

        if isotropic:
            F_GS = np.ones((M, 2))
        else:
            F_GS = np.stack([_dipole(t1), _dipole(p1)], axis=1)

        E_GS_R = E_GS[None, :] * F_GS
        # NB: the original MATLAB code also weights the UAV field with F_GS; kept for fidelity.
        E_UAV_R = E_UAV[None, :] * F_GS

        a = Rl[:, 2] - np.cos(t2)[:, None] * u
        b = Rl[:, 1] - np.cos(p2)[:, None] * u
        cosa1 = (a @ Rk[2]) / np.sin(t2)
        cosa2 = (b @ Rk[2]) / np.sin(p2)
        cosb1 = (a @ Rk[1]) / np.sin(t2)
        cosb2 = (b @ Rk[1]) / np.sin(p2)

        R2 = np.stack([np.stack([cosa1, cosa2], -1), np.stack([cosb1, cosb2], -1)], -2)  # (M,2,2)
        proj = np.einsum("mi,mij,mj->m", E_GS_R, R2, E_UAV_R)
        X = 1.64 ** 2 * np.abs(proj) ** 2

        z = 1.0 / np.mean(X)
        z_out.append(z)
        pt_out.append(N0 * B * (4 * np.pi * dk / lam) ** 2 * z)

    return np.array(z_out), np.array(pt_out)
