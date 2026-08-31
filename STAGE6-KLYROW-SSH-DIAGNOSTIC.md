# Stage 6 Klyrow SSH Diagnostic

Captured: 2026-08-31T12:24:43Z

The documented connection authority is:

```text
alias=klyrow-server
host=37.27.128.39
user=klyrow-deploy
port=22
identity=dedicated configured identity (contents not read)
interface=klyrow-stack
```

The bounded current check connected at `2026-08-31T12:21:37Z`; authenticated
restricted read operations subsequently succeeded. Direct Docker access was
not requested or granted. Because the endpoint recovered before additional
bounded checks were necessary and no server-side sshd/firewall evidence was
available through the restricted interface, the cause of the earlier active
refusal is UNKNOWN. No access-control changes were made.
