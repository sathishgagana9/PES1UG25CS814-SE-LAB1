@"
# Lab 5 - Reflection

Static analysis helped identify code-quality, security, and formatting problems in the transit fare calculator. Pylint highlighted documentation and maintainability issues. Bandit identified security concerns related to hashing, XML parsing, and SSH command execution. Flake8 highlighted style issues.

The code was modified to improve readability, input validation, XML handling, checksum security, and SSH host-key verification. After modification, the program executed successfully. Pylint reported a score of 10.00/10, Bandit identified no issues, and Flake8 reported no violations.

This lab demonstrated that different static-analysis tools detect different categories of problems. However, passing these tools does not guarantee that software is completely free of vulnerabilities.
"@ | Set-Content reflection.md