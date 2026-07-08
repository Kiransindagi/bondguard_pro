# Breach Management

## Lifecycle
Breaches follow a strict state machine:
1. **OPEN**: Created on the first violation.
2. **ACKNOWLEDGED**: A user explicitly reviews and notes the breach.
3. **RESOLVED**: Automatically transitioned when the metric falls within the limit threshold.

## Behavior Rules
* **Deduplication**: A repeated violation updates the `latest_evaluation_run_id` and `observed_value` of an existing active (OPEN or ACKNOWLEDGED) breach, avoiding duplicate breach creation.
* **Acknowledgement retention**: Repeated violations do not revert an ACKNOWLEDGED breach back to OPEN.
* **Re-breach**: If a metric recovers (breach becomes RESOLVED), and then violates the limit again, a brand new OPEN breach is created.

## Audit Events
All state transitions are append-only.
Events generated:
* `EVALUATION_COMPLETED` (or FAILED)
* `BREACH_OPENED`
* `BREACH_UPDATED`
* `BREACH_ACKNOWLEDGED`
* `BREACH_RESOLVED`
* `LIMIT_CREATED`, `LIMIT_UPDATED`, `LIMIT_DEACTIVATED`
