"""Vollstaendiger Schaetzlauf auf der V2|B-Spezifikation, mit Checkpointing.

Nur `run_estimation()` - `shape_data()` bleibt aussen vor, damit
data/processed/shaped_data.h5 (Nov 2024) unveraendert bleibt.

Arbeitsverzeichnis muss DREI Ebenen unter der Repo-Wurzel liegen, weil die
relativen `paths.*` der Config (../../../data/ usw.) sonst nicht aufloesen;
zugleich schreibt der Hydra-FileHandler nach ./outputs/DATE/TIME/, das Hydra
im selben Verzeichnis anlegt. Beides passt bei cwd = src/pfd/models mit
hydra.job.chdir=false.

Wiederaufnahme: bei einem Abbruch einfach erneut starten. Fertige Phasen
liegen als data/interim/ckpt_*.pkl, fertige Sampler-Laeufe als
models/trace_nuts_*.nc und werden nicht neu gerechnet.
"""
import os
import sys

REPO = "/mnt/c/Users/micha/OneDrive/Michi/pfd"
os.chdir(f"{REPO}/src/pfd/models")
sys.path.insert(0, f"{REPO}/src")
sys.argv = [
    "run_estimation",
    "hydra.job.chdir=false",
    "estimation.checkpoint=true",
]

from pfd.models import run_estimation  # noqa: E402

print("cwd:", os.getcwd(), flush=True)
print("shaped_data.h5 sichtbar:",
      os.path.isfile("../../../data/processed/shaped_data.h5"), flush=True)
for f in sorted(os.listdir("../../../data/interim")):
    if f.startswith("ckpt_"):
        print("vorhandener Checkpoint:", f, flush=True)

run_estimation()
print("RUN_FERTIG", flush=True)
