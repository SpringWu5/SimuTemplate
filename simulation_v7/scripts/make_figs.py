import os, sys, csv, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(HERE))
from simulation_v7 import stats_v7 as S
# reload best-fit pred from audit
# (recompute quickly with stored component signatures)
sys.path.insert(0, HERE)
from simulation_v7.scripts.run_step1_audit import best_B, frB  # may fail; fallback below
