# Work item lifecycle

The normal state sequence is:

```text
draft -> discovery -> ready_for_development -> in_development
      -> ready_for_validation -> validation_in_progress
      -> ready_for_delivery -> delivered
```

`blocked`, `approval_required`, `changes_requested`, `cancelled`, and `superseded` are explicit exceptional states.

The executable feature workflow uses stages `discovery`, `rnd`, `plan`, `dev`, `verify`, `review`, `qa`, and `final`. Verification, review, and QA are separate judgments. A stage is idempotent: rerunning it replaces its stage result but preserves command evidence under a unique filename.

