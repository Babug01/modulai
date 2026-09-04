"""Validation pipeline run against a generated module directory.

fmt -> init -> validate -> test -> checkov. `terraform test` runs against the
generated tests/*.tftest.hcl, which use `mock_provider` — no real cloud
credentials are needed for any step here, which is what makes it safe to run
for anonymous users of a public tool.

Not runnable without the terraform and checkov binaries installed — this
module has not been executed end-to-end yet.
"""

from __future__ import annotations

import subprocess
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


def _run(cmd: list[str], cwd: Path, timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def run_validation_pipeline(module_dir: Path, terraform_bin: str = "terraform", checkov_bin: str = "checkov") -> ValidationReport:
    report = ValidationReport()

    fmt = _run([terraform_bin, "fmt", "-check", "-recursive"], module_dir, 30)
    report.steps.append(StepResult("fmt", fmt.returncode == 0, fmt.stdout + fmt.stderr))
    if fmt.returncode != 0:
        return report  # no point continuing against unformatted HCL

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

    checkov = _run(
        [checkov_bin, "-d", str(module_dir), "--framework", "terraform", "--compact"],
        module_dir, 120,
    )
    # Checkov exits non-zero on any failed check by design — surface it as a
    # report finding, not a pipeline crash; the caller decides what's blocking.
    report.steps.append(StepResult("checkov", checkov.returncode == 0, checkov.stdout + checkov.stderr))

    return report
