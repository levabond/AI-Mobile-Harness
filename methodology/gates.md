# Gate semantics

- `pass`: every required artifact exists and every required executable check has recorded evidence.
- `retry`: a classified, bounded repair can be attempted without expanding authority or scope.
- `approval_required`: the next action crosses a human authority boundary.
- `fail`: required evidence is missing, a check failed, or a blocking finding exists.

No gate converts `not_run` into `passed`. Unsupported adapter capabilities are reported as `unsupported`; a profile may explicitly allow that status, otherwise the gate fails.

