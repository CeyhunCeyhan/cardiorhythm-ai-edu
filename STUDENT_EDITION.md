# Student Edition — classroom pilot

Separate entrypoint: `streamlit run student_app.py`. Research app.py and all
validation modules remain untouched. Entry point uses five deterministic synthetic
cases, not patient ECGs. It does NOT activate the experimental morphology detector.
All displayed rates come from known synthetic beat times, explicitly labelled.

## Deployment
Create a separate Streamlit deployment for this repository, branch student-edition,
entrypoint student_app.py. Keep the existing validation-v03 deployment unchanged.
Existing requirements.txt is reused. No new runtime dependency required.
Configure individual users with existing security.py password hashes in Secrets.
Never commit passwords, hashes or real Secrets. Use existing create_password_hash.py
privately or generate hashes locally using security.make_hash. Provide each learner
only their own credential. Student app has no public bootstrap account creation.

Secrets schema (placeholders are NOT working credentials):
```toml
[users.instructor]
role = "admin"
password_hash = "REPLACE_PRIVATELY"
[users.student01]
role = "student"
password_hash = "REPLACE_PRIVATELY"
[student_edition]
approved_cases = []
```
Instructor logs in, reviews all five cases, then sets approved_cases to the
approved case IDs: regular60, regular90, variable, early, noise. No claim of
clinical approval before this review. Students see only approved cases.

## Session and resource behavior
Case generation is local: no PhysioNet download or API during a lesson.
Only the login limiter is globally shared; student answers live in session_state.
Logout clears all session keys. Idle expiry is checked on the next interaction
at 30 minutes. Authorization is rechecked on reruns. Login limiter is per username,
process-local, bounded to 1024 entries and reset on server restart. Not a production
identity service; multi-instance deployments require centralized rate limiting/SSO.
No upload endpoint, patient data, database writes or user-content caching.
No background/full-record validation in the student entrypoint.

## Release gates
- Automated login, role filtering, answer feedback, logout and session isolation tests.
- 15 parallel AppTest sessions are a server logic smoke test, NOT a browser/load SLA.
- Actual iPhone Safari and Android Chrome with 10–15 simultaneous users, slow network,
  reconnect and cold startup must be checked on the chosen host before class.
- Instructor approval of cases and working individual accounts required.
- Next phase: anonymous photo viewing; no validated photo-to-signal analysis exists.
