"""Validation pipeline run against a generated module directory.

fmt -> init -> validate -> test -> checkov. `terraform test` runs against the
generated tests/*.tftest.hcl, which use `mock_provider` — no real cloud
credentials are needed for any step here, which is what makes it safe to run
for anonymous users of a public tool.

Live-verified end to end (terraform v1.16.1, checkov 3.3.16) against a
generated azurerm_key_vault module: fmt/init/validate/test all pass for real,
including a validation-block rejection case and a nested dynamic-block case.
Two bugs found and fixed by that same run — see _run() and the fmt step below.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StepResult:
    name: str
    passed: bool
    output: str


@dataclass
class ValidationReport:
    steps: list[StepResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(s.passed for s in self.steps)


def _resolve_windows_script(cmd: list[str]) -> list[str]:
    """A pip-installed console script can be a .cmd/.bat wrapper rather than
    a .exe on Windows — subprocess can't launch those directly via
    CreateProcess without going through cmd.exe first. Found live: checkov
    installs as checkov.cmd here and raised FileNotFoundError despite the
    file existing and running fine from an actual shell. No-op elsewhere.
    """
    if sys.platform != "win32":
        return cmd
    resolved = shutil.which(cmd[0]) or cmd[0]
    if resolved.lower().endswith((".cmd", ".bat")):
        return ["cmd", "/c", resolved, *cmd[1:]]
    return cmd


def _run(cmd: list[str], cwd: Path, timeout: int) -> subprocess.CompletedProcess:
    cmd = _resolve_windows_script(cmd)
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        # A genuinely missing binary is a normal, reportable step failure —
        # not a crash that discards every already-passed step's results.
        return subprocess.CompletedProcess(cmd, returncode=127, stdout="", stderr=f"{cmd[0]}: command not found")


def run_validation_pipeline(module_dir: Path, terraform_bin: str = "terraform", checkov_bin: str = "checkov") -> ValidationReport:
    report = ValidationReport()

    # Apply formatting rather than gate on it — a spacing/alignment mismatch
    # is trivially self-healing and should never block generation the way an
    # actual validate/test failure does. `-check` here was found live to fail
    # the whole pipeline over cosmetic misalignment in generated HCL.
    fmt = _run([terraform_bin, "fmt", "-recursive"], module_dir, 30)
    reformatted = fmt.stdout.strip().splitlines()
    fmt_summary = f"reformatted: {', '.join(reformatted)}" if reformatted else "already formatted"
    report.steps.append(StepResult("fmt", fmt.returncode == 0, fmt_summary))
    if fmt.returncode != 0:
        return report  # fmt itself erroring (not just reformatting) means invalid HCL syntax

    init = _run([terraform_bin, "init", "-input=false", "-backend=false"], module_dir, 120)
    report.steps.append(StepResult("init", init.returncode == 0, init.stdout + init.stderr))
    if init.returncode != 0:
        return report

    validate = _run([terraform_bin, "validate"], module_dir, 60)
    report.steps.append(StepResult("validate", validate.returncode == 0, validate.stdout + validate.stderr))
    if validate.returncode != 0:
        return report

    test = _run([terraform_bin, "test"], module_dir, 180)
    report.steps.append(StepResult("test", test.returncode == 0, test.stdout + test.stderr))

    # "." not str(module_dir) — cwd is already module_dir below, so the full
    # path a second time double-applies it (found live: silently resolved to
    # a nonexistent nested directory, which checkov skips and exits 0 for —
    # a false pass, not a real one).
    checkov = _run(
        [checkov_bin, "-d", ".", "--framework", "terraform", "--compact"],
        module_dir, 120,
    )
    # Checkov exits non-zero on any failed check by design — surface it as a
    # report finding, not a pipeline crash; the caller decides what's blocking.
    report.steps.append(StepResult("checkov", checkov.returncode == 0, checkov.stdout + checkov.stderr))

    return report
