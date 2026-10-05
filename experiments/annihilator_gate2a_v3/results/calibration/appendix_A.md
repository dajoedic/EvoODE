# Appendix A - Gate 2A v3 Stage K

- ell_max: 4
- tau: 3.386508022297224e-07
- overall_passed: False
- runtime_seconds: 8358.230160699997

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
| K1_wide | CORRECT | True |
| K5_wide | CORRECT | True |
| K1_narrow | CORRECT | True |
| K5_narrow | AMBIGUOUS | True |
| K2_wide | CORRECT | True |
| K6_wide | CORRECT | True |
| K2_narrow | CORRECT | True |
| K6_narrow | AMBIGUOUS | True |
| K3_wide | CORRECT | True |
| K7_wide | AMBIGUOUS | False |
| K3_narrow | AMBIGUOUS | True |
| K7_narrow | WRONG | False |
| K4_wide | CORRECT | True |
| K8_wide | AMBIGUOUS | False |
| K4_narrow | AMBIGUOUS | True |
| K8_narrow | AMBIGUOUS | True |
