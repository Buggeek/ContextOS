# Context OS Integrated Runtime Benchmark

`tools/runtime` contains the internal v1.0 integration proof for the released
Context OS runtime. It composes public engine APIs in read-only mode and checks
cross-capability identity, provenance, authority, truth, and invalidation
boundaries.

It is not a product orchestration surface and does not replace `contextos`
commands. Mutation-capable Bootstrap and Construction stages are represented by
exact, hashed release-verification evidence and are never replayed against the
canonical repository.

Run the focused proof:

```bash
python3 tools/runtime/test_runtime_integration_benchmark.py
```

Run the internal human benchmark:

```bash
python3 tools/runtime/contextos_runtime_benchmark.py \
  --root . \
  --goal "Prove the complete governed Organizational Context Runtime" \
  --mission-id V10-RUNTIME-INTEGRATION-BENCHMARK-001
```

Use `--format json` for pure machine output. Exit code `0` means every
integration check passed, `7` means a release-blocking gap was observed, and
`9` means the benchmark was misconfigured.
