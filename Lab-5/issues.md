@"
# Lab 5 - Static Analysis Issues

## Pylint
- Added module and function documentation.
- Improved naming and control flow.
- Removed unused imports.
- Replaced the mutable default argument with None.
- Simplified fare calculation logic.

## Bandit
- Replaced MD5 with SHA-256 for ticket checksums.
- Replaced automatic SSH host-key acceptance with host-key verification.
- Used defusedxml for XML parsing.
- Added remote-path validation and shell quoting for the SSH command.

## Flake8
- Removed unused imports.
- Fixed formatting and line-length issues.
- Improved lambda assignment style.

## Final Results
- Pylint: 10.00/10.
- Bandit: No issues identified.
- Flake8: No reported violations.
"@ | Set-Content issues.md