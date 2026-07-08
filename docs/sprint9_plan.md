# Sprint 9: Production Data Pipeline, Authentication, RBAC & Audit Trail

## Part A: Authentication, RBAC, and Global Audit Trail
This foundational layer will introduce enterprise-level access control and traceability before orchestrating automated jobs.

### 1. Database & Security Foundation
*   **Dependencies**: Install `passlib`, `bcrypt`, `python-jose`, and `python-multipart` for secure password hashing and JWT token generation.
*   **Models (`backend/app/auth/models.py`)**: Create `User` model with `role`, `is_active`, and credentials.
*   **Global Audit Extension (`backend/app/audit/models.py`)**: Generalize the existing `AuditEvent` (from Sprint 7) to be global, recording the user ID, action, resource, and status.
*   **Alembic Migration**: Generate and apply the migration for `users` and updated `audit_events`.

### 2. Services & RBAC
*   **Authentication Service**: Implement JWT login endpoint (`/token`), password verification, and hashing using `auth/security.py` and `auth/service.py`.
*   **RBAC Dependencies (`backend/app/auth/dependencies.py`)**: Create FastAPI dependency overrides (`get_current_user`, `require_role(roles)`) to protect endpoints based on roles: `Admin`, `Risk Manager`, `Analyst`, `Viewer`, `Auditor`.

### 3. Frontend Integration
*   **Auth Context**: Create a React Context (`AuthContext`) to manage user session and JWT tokens.
*   **Protected Routes**: Wrap existing routes in `ProtectedRoute` components that verify roles.
*   **Login Interface**: Implement a dedicated login screen.
*   **User Management & Audit Dashboards**: Build standard UIs for Admins and Auditors to manage access and trace events.

---

## Part B: Production Data Pipeline & Data Quality
This layer automates data ingestion and calculates risk dynamically while verifying structural integrity.

### 1. Data Quality Engine
*   **Models (`backend/app/data_quality/models.py`)**: `DataQualityRule`, `DataQualityExecution`, `DataQualityAnomaly`.
*   **Checks**: Build deterministic validation checks (e.g., duplicate detection, stale price detection, outlier flags, yield-curve completeness checks) inside `data_quality/checks.py`.

### 2. Job Orchestration Pipeline
*   **Models (`backend/app/jobs/models.py`)**: `JobExecution` to track state (PENDING, RUNNING, SUCCESS, FAILED), retries, and errors.
*   **Task Definitions**: Create modular functions in `jobs/tasks/` for:
    *   Ingesting market data
    *   Validating data quality
    *   Triggering risk computation engines
    *   Evaluating limits
    *   Generating snapshots
*   **Pipeline Orchestrator (`jobs/pipeline.py`)**: Tie the tasks together into a coherent DAG-like execution sequence.

### 3. Operations & Observability
*   **API Routes**: Expose `/api/v1/jobs` and `/api/v1/data-quality` to trigger pipelines and fetch status.
*   **Frontend Operations Dashboard**: Build an observability UI tracing pipeline health, data freshness, and anomalies.
