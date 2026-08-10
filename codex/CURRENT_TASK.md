# CURRENT TASK

**Language: Julia**

## WP-D4a-fix — Correct one wrong assertion in the new contract test

Minimal follow-up to WP-D4a. The production change is correct and stays untouched. One assertion in
the new test is wrong and fails.

### The finding

`test/test_discover_contract.jl` line 61 asserts that the returned structure equals
`StructureSpec([[1]])`. It fails with the confusing output
`StructureSpec([[1]]) == StructureSpec([[1]])`.

The reason is that `StructureSpec` defines no `==`, `isequal` or `hash` method. Julia therefore falls
back to identity comparison, and because the type holds a `Vector{Vector{Int}}`, two separately
constructed specs with identical content are never equal. The assertion can never pass.

This was verified to be a test-only problem: no production code compares structures with `==`.

### 1. Fix the assertion

Compare the content of the returned structure — its active term indices — against the expected
content, rather than comparing two `StructureSpec` objects.

### 2. Do not add an equality method

Do not define `==`, `isequal` or `hash` for `StructureSpec` to make the original assertion work.

A canonical equality and hash for structures is a real and known gap — it is the precondition for
candidate deduplication — but introducing it now would be a behaviour-relevant change to a type used
throughout the search, immediately before the campaign. It belongs in the post-campaign backlog, not
in a test fix.

### 3. Run the test

Run `test/test_discover_contract.jl` and include the actual output in the report. WP-D4a was
reported without this file ever having been executed; that is what let a never-passing assertion
through. Test files are cheap to run and are not covered by the no-long-runs rule.

### Out of scope

Everything else. `src/core/discover.jl` and `src/core/types.jl` as WP-D4a left them, the other test
files, the runners.

### Report

Append to `codex/REPORT_WP_D4a.md`: the corrected assertion and the full output of the executed test.
