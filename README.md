# CardioRhythm AI — Educational ECG Prototype v0.2

An educational ECG signal viewer using the public PhysioNet MIT-BIH Arrhythmia Database (record 100). Experimental R-peak candidate detection, RR statistics and CSV export. **Not for clinical diagnosis or patient care. Do not upload patient data.**

## Access and roles

Login is required before any ECG display. Roles: `admin`, `resident`, `student`. Every account has an independent password hash. The `admin` role is a placeholder for future administration features: accounts are currently provisioned **manually** through Streamlit Secrets; there is no user-management UI. The login gate is a teaching prototype, **not production-grade authentication**: session-scoped lockout does not prevent distributed brute-force attacks, and this app has not undergone security assessment. Do not use for sensitive or patient data.

## Deploy on Streamlit Community Cloud

1. Create a **separate public GitHub repository** containing only these files. Never add real secrets, passwords, patient records or `.streamlit/secrets.toml`.
2. Streamlit Community Cloud > Create app > Deploy from GitHub > select repository, branch `main`, main file `app.py`.
3. Before opening access to users, go to App settings > Secrets. Use `.streamlit-secrets.example.toml` as a template. For each user, create a strong unique password privately, generate a PBKDF2 hash with `python create_password_hash.py` on a trusted computer, and paste **only the hash** into Secrets.
4. Deploy, verify unauthenticated users see only the login form, then verify valid and invalid logins, logout and role display.
5. Rotate a user's password by replacing their hash in Secrets and restarting the app. Existing sessions may persist until the app restarts; account revocation is not immediate across all sessions.

**Do not deploy with demo credentials.** If Secrets are missing, the app fails closed. Do not share passwords in ChatGPT or commit them to GitHub.

## Local run

```bash
pip install -r requirements.txt
mkdir -p .streamlit
# Create .streamlit/secrets.toml from the example with real hashes (never commit it)
streamlit run app.py
```

## Limitations

Requires internet access to download public sample ECG. Detection is unvalidated, and no arrhythmia diagnosis is produced. Use an established identity provider (OIDC), centralized rate limiting, session revocation and a security review before using with a large group or sensitive data. Public repository code is visible to everyone; login gates only the app interface, not the source code.
