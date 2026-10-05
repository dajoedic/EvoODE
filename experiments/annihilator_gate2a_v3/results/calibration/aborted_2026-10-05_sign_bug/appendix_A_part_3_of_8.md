# Appendix A - Gate 2A v3 Stage K

- ell_max: 4
- tau: 3.386508022297224e-07
- overall_passed: False
- runtime_seconds: 7388.6997185

## K-c Monte Carlo

| Function | Ex-ante | Checked | Point 1 | Point 2 | Point 3 |
|---|---:|---:|---:|---:|---:|
| K1 | I | True | False | False | False |
| K2 | I | True | True | True | True |
| K3 | N1 | False | None | None | None |
| K4 | N1 | False | None | None | None |
| K5 | N2 | False | None | None | None |
| K6 | I | True | False | True | False |

## K-c Clean

| Cell | State | Passed |
|---|---:|---:|
| K2_narrow | CORRECT | True |
| K6_narrow | AMBIGUOUS | True |
