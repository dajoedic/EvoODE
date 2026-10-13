# WP-T2a-impl-d — fix one test call in `test/test_candidate_prior.jl`
**Language: Julia**

## Why

Claude ran `julia --project=. --startup-file=no test/test_candidate_prior.jl` after WP-T2a-impl-c. All testsets pass
except "T2a manifest prior paths are portable" (3 pass, 1 error):

```
MethodError: no method matching _t2a_test_manifest_row(::var"#144#145", ::String)
Closest candidates are: _t2a_test_manifest_row(!Matched::AbstractString, ::Any)
  [1] (::var"#142#143"{Vector{NamedTuple}})(dir::String)
  [2] mktempdir(fn, parent::String; prefix::String)
```

A `do`-block passes the closure as the first positional argument of `_t2a_test_manifest_row`, whose signature expects a
string first. The code under test is fine: Claude verified by hand that a relative prior path resolves from a copied
directory (identical fingerprint, loss, support, loss evaluations) and that an absolute path is refused with the
intended error.

## Deliverables

- Fix the call (or the helper's signature) so the testset runs and keeps all of its assertions. No other change.
- One line in `STATUS.md`; no separate report needed.

## Verboten

- Changing anything outside `test/test_candidate_prior.jl`. Running Julia. Committing. Editing this file.

## Abnahme

- `STATUS.md` `done` (Julia not executed) or `blocked`.
