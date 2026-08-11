#!/usr/bin/env python3
"""waveform_copy.py -- unified waveform-copy metric for any small pair (STEP 2).

For two baseline-subtracted waveforms V_a (major), V_b (minor) over a signal
window, compute the FULL copy metric set (not just correlation):
  r          normalized cross-correlation at best lag
  lag        best lag (samples)
  k_best     best scale = <V_b, V_a_shift>/<V_a, V_a>
  resid      RMS[V_b - k*V_a_shift] / RMS[V_b]   (scaled residual -- KEY metric)
  resid_rise residual over the rising edge only
  resid_tail residual over the tail only
The scaled residual distinguishes a true electronics COPY (resid ~ noise/signal,
very low) from two independent plastic pulses (high corr but resid larger due to
independent amplitude/shape fluctuations).
"""
import numpy as np

SIG_LO, SIG_HI = 190, 311   # signal search window (samples)


def _window(bs_major, bs_minor):
    pk = np.argmax(bs_major[SIG_LO:SIG_HI]) + SIG_LO
    lo = max(pk - 25, 0); hi = min(pk + 55, bs_major.shape[0])
    return slice(lo, hi)


def copy_metric(bs_major, bs_minor):
    """bs_*: baseline-subtracted 1D waveform. Returns dict of metrics."""
    s = _window(bs_major, bs_minor)
    a = bs_major[s].astype(float); b = bs_minor[s].astype(float)
    a = a - np.mean(a[:15]); b = b - np.mean(b[:15])
    na = np.sqrt(np.sum(a * a)) + 1e-12; nb = np.sqrt(np.sum(b * b)) + 1e-12
    an = a / na; bn = b / nb
    xc = np.correlate(an, bn, "full")
    lag = int(xc.argmax() - (len(bn) - 1))
    r = float(xc.max())
    a_s = np.roll(a, lag)
    k = float(np.sum(b * a_s) / (np.sum(a_s * a_s) + 1e-12))
    resid = float(np.sqrt(np.mean((b - k * a_s) ** 2)) / (nb + 1e-12))
    # rise/tail: first 20 / last 35 samples of window
    nr = min(20, len(b))
    resid_rise = float(np.sqrt(np.mean((b[:nr] - k * a_s[:nr]) ** 2)) / (np.sqrt(np.sum(b[:nr] ** 2)) + 1e-12))
    nt = min(35, len(b))
    resid_tail = float(np.sqrt(np.mean((b[-nt:] - k * a_s[-nt:]) ** 2)) / (np.sqrt(np.sum(b[-nt:] ** 2)) + 1e-12))
    return dict(r=r, lag=lag, k=k, resid=resid, resid_rise=resid_rise, resid_tail=resid_tail)


def pair_from_event(df_row, bs):
    """Return (major_ch, minor_ch, major_wf, minor_wf) for a 2-hit event."""
    hits = []
    for ch in range(4):
        if df_row[f"hit{ch}"] == 1:
            hits.append((ch, df_row[f"ch{ch}_integral"]))
    if len(hits) < 2:
        return None
    hits.sort(key=lambda x: -x[1])   # major first
    (maj_ch, _), (min_ch, _) = hits[0], hits[1]
    idx = df_row.name
    return maj_ch, min_ch, bs[idx, maj_ch], bs[idx, min_ch]
