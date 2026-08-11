#!/usr/bin/env python3
"""load_hardware_data.py -- unified data ingestion for simulation_v8 (STEP 3).

Single source of truth for the Haasoscope hardware data package. All downstream
scripts must use these loaders, never read the CSVs directly.

Variable definitions per DATA_DICTIONARY.md / README:
  Q (ch{i}_integral) = baseline-subtracted pulse integral [p-4, p+18) x 32 ns,
                        unit = "CSV_export_unit_ns" (NOT pC, NOT PE).
  amplitude          = signal-window peak above median baseline (clipped => biased).
  Q_min/Q_sum/etc    = pair observables over the two hit small channels.
  panel_matched_score_v4 = noise-normalized 8-SiPM coherent matched-filter score
                            (dimensionless; NOT PE).
  M8 = all 8 panel channels exceed offline threshold.
Categories: A (cross-M8), B2 (cross-nonM8 weak, template>=0.92), B3 (cross-nonM8
  strong+dark), SD (same-layer dark), SM8 (same-layer M8), M3.
"""
import os, json, hashlib
import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(_HERE, "..", "input_data", "haasoscope_data_for_simulation")
PKG = os.path.normpath(PKG)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def package_root():
    return PKG


def load_event_table():
    """262-event feature table (446 columns). Indexed by row = event order."""
    return pd.read_csv(os.path.join(PKG, "tables", "event_features_for_simulation.csv"))


_WF_CACHE = None
def load_all_waveforms():
    """Full waveform NPZ: raw_waveforms[262,12,511], baseline-subtracted, etc."""
    global _WF_CACHE
    if _WF_CACHE is None:
        d = np.load(os.path.join(PKG, "arrays", "all_waveforms.npz"), allow_pickle=True)
        _WF_CACHE = {k: d[k] for k in d.keys()}
    return _WF_CACHE


def event_id_list():
    return load_all_waveforms()["event_ids"]


def load_event_waveform(event_id):
    """Return dict of arrays for one event (by event_id string)."""
    wf = load_all_waveforms()
    idx = int(np.where(wf["event_ids"] == event_id)[0][0])
    return dict(
        event_id=str(event_id), idx=idx,
        raw=wf["raw_waveforms"][idx], bsub=wf["baseline_subtracted_waveforms"][idx],
        baseline=wf["baseline"][idx], rms=wf["baseline_rms"][idx],
        time_ns=wf["time_ns"], sample_period=float(wf["sample_period_ns"][idx, 0]),
    )


def category_mask(df, name):
    """Boolean mask for data category: A, B2, B3, SD, SM8, M3, cross, same."""
    topo = df["topology"]
    m8 = df["panel_M8"] == 1
    cross = topo.isin(["T02", "T13", "T03", "T12"])
    same = topo.isin(["U01", "L23"])
    bsub = df.get("B_subclass", pd.Series([""] * len(df)))
    if name == "A":      return cross & m8
    if name == "B2":     return bsub.eq("B2_two_real_looking_weak")
    if name == "B3":     return bsub.eq("B3_two_real_strongish_no_M8")
    if name == "SD":     return same & ~m8
    if name == "SM8":    return same & m8
    if name == "M3":     return topo.eq("M3")
    if name == "cross":  return cross
    if name == "same":   return same
    raise ValueError(f"unknown category {name}")


def load_category(name, df=None):
    if df is None:
        df = load_event_table()
    return df[category_mask(df, name)]


def load_panel_calibration():
    return pd.read_csv(os.path.join(PKG, "tables", "panel_channel_calibration.csv"))


def load_light_sharing():
    return pd.read_csv(os.path.join(PKG, "tables", "panel_light_sharing.csv"))


def build_manifest():
    """Lock the data version: ZIP SHA256, file list, counts."""
    zip_path = os.path.join(_HERE, "..", "..", "..", "haasoscope_data_for_simulation.zip")
    zip_path = os.path.normpath(zip_path)
    df = load_event_table()
    wf = load_all_waveforms()
    manifest = dict(
        zip_sha256=_sha256(zip_path) if os.path.exists(zip_path) else "ZIP_NOT_FOUND",
        read_date=pd.Timestamp.now().date().isoformat(),
        n_events=int(len(df)),
        waveform_shape=list(wf["raw_waveforms"].shape),
        n_channels=int(wf["raw_waveforms"].shape[1]),
        n_samples=int(wf["raw_waveforms"].shape[2]),
        sample_period_ns=float(wf["sample_period_ns"][0, 0]),
        counts=dict(
            U01=int((df["topology"] == "U01").sum()), L23=int((df["topology"] == "L23").sum()),
            T02=int((df["topology"] == "T02").sum()), T13=int((df["topology"] == "T13").sum()),
            T03=int((df["topology"] == "T03").sum()), T12=int((df["topology"] == "T12").sum()),
            M3=int((df["topology"] == "M3").sum()), other=int((df["topology"] == "other").sum()),
            cross_M8=int(category_mask(df, "A").sum()), same_M8=int(category_mask(df, "SM8").sum()),
            B2=int(category_mask(df, "B2").sum()), B3=int(category_mask(df, "B3").sum()),
            SD=int(category_mask(df, "SD").sum()),
        ),
        units=dict(Q="CSV_export_unit_ns", amplitude="CSV_export_unit",
                   panel_score="dimensionless_matched_filter", M8="all_8_panel_above_offline_thr"),
        unknown_hardware=["small_hardware_threshold", "runtime_hold", "ADC_range",
                          "gain", "supergain", "absolute_PE", "absolute_pC", "live_time"],
    )
    # per-file sha256 for core tables
    manifest["file_sha256"] = {}
    for fn in ["tables/event_features_for_simulation.csv", "arrays/all_waveforms.npz",
               "tables/panel_channel_calibration.csv", "tables/panel_light_sharing.csv",
               "tables/same_layer_minor_major.csv", "tables/cross_dark_B2.csv",
               "tables/cross_dark_B3.csv"]:
        p = os.path.join(PKG, fn)
        if os.path.exists(p):
            manifest["file_sha256"][fn] = _sha256(p)
    out = os.path.join(_HERE, "..", "input_manifest.json")
    with open(out, "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest


if __name__ == "__main__":
    m = build_manifest()
    print(json.dumps(m, indent=2))
