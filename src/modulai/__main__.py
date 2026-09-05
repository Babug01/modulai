"""Enables `python -m modulai ...` as an equivalent to the `modulai` console
script. Exists because pip's auto-generated .exe launcher stubs can get
blocked by AV/EDR heuristics on locked-down Windows machines (freshly
created, unsigned executables about to run) even when python.exe itself
runs fine — found live. `python -m modulai` routes through python.exe
directly, sidestepping the stub entirely.
"""

from modulai.cli import main

if __name__ == "__main__":
    main()
