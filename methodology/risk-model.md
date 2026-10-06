# Risk model

Risk is the highest of the baseline work-item risk and its factors.

| Level | Typical factors | Required response |
|---|---|---|
| low | copy or isolated presentation | prototype or standard checks |
| medium | user-visible, navigation, network contract | standard profile and risk-based QA |
| high | auth, payments, persistence migration, privacy | strict profile and human approval |
| critical | destructive release or credible data-loss/security exposure | stop until explicitly approved |

Each risk entry records an id, factor, likelihood, impact, mitigation, owner, and disposition. Unknown high-impact behavior is blocking rather than silently downgraded.

