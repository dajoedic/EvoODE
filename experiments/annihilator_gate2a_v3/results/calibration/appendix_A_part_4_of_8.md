# Appendix A - Gate 2A v3 Stage K

- ell_max: 4
- tau: 3.386508022297224e-07
- overall_passed: False
- runtime_seconds: 16469.9063641

## K-c Monte Carlo

| Function | Ex-ante | Checked | Point 1 | Point 2 | Point 3 |
|---|---:|---:|---:|---:|---:|
| K1 | I | True | True | True | True |
| K2 | I | True | True | True | True |
| K3 | N1 | False | None | None | None |
| K4 | N1 | False | None | None | None |
| K5 | N2 | False | None | None | None |
| K6 | I | True | False | True | False |

## K-c Clean

| Cell | State | Passed |
|---|---:|---:|
| K3_wide | CORRECT | True |
| K7_wide | AMBIGUOUS | False |
