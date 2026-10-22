# HR email sign-in (local testing)

Start `.venv\Scripts\python.exe -m app.enterprise.launch --port 8000 --email-login`, then open http://127.0.0.1:8000/login.

Approved addresses:
- aditya.jais2005@gmail.com
- omerovias@gmail.com
- ashwinkm.2005@gmail.com

Each account receives HR_ADMIN access (employee records; retail data remains subject to the existing role restrictions). Other addresses see an access-denied page. Tokens are emailed only to the approved address entered, expire after 10 minutes, and work once. Five failed verification attempts require a new token. Resending is limited to once per minute per approved address. New sign-in revokes that account's previous session. Sessions last 8 hours; restarting the server signs everyone out.

## Configure the sender once

Use a Gmail account you own. Enable 2-Step Verification and create an App Password named RetailOps AI: https://support.google.com/accounts/answer/185833 . Some managed or protected accounts do not offer App Passwords. Do not use your normal Gmail password.

Add these settings to the repository's local `.env` file (preserve any existing settings):

```dotenv
RETAILOPS_SMTP_HOST=smtp.gmail.com
RETAILOPS_SMTP_PORT=587
RETAILOPS_SMTP_USERNAME=your-sender@gmail.com
RETAILOPS_SMTP_SENDER=your-sender@gmail.com
RETAILOPS_SMTP_PASSWORD=your-app-password-without-spaces
```

Keep `.env` local, do not commit it or paste the password in chat. Restart the server after configuring it. Enter an approved email and press Send access token; check inbox/spam, paste the emailed token, then sign in. No tokens are sent automatically at startup. Missing or failed SMTP delivery blocks sign-in with an explanatory message.

For a different provider, use its authenticated STARTTLS SMTP host and port. HTTPS is required if deploying beyond localhost. This testing implementation uses one server process and in-memory sessions.

Normal startup uses terminal-generated access tokens. Email sign-in is paused until a sender is configured; enable it explicitly with `--email-login`. The optional `--token-login` flag also selects the default terminal-token mode. If using uvicorn directly instead of the launcher, set `RETAILOPS_EMAIL_LOGIN=true`.
