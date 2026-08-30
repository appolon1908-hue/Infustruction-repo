# Codestra contract collisions

## C-I0-001 — Email consent and suppression authority

**State:** unresolved; R6 owner decision required.

| Claimant | Repository evidence | Implemented evidence |
|---|---|---|
| Codestra Communication CC | Declares itself the customer-communications control plane and lists consent/suppression as owned state. | `communication_consents` and `communication_suppressions` models, acceptance-time enforcement, and mutation endpoints. |
| Klyrow | Declares itself the commercial email tenant/API control plane and durable owner of consent state. | Consent, preference, and suppression models/endpoints plus send-time enforcement. |

The estate registry cannot truthfully assign one `control-plane` tier for this
capability until the owner selects the authority and records the state/event
boundary. No provisional owner or rename has been applied.
