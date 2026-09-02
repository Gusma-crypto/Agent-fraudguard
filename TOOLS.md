# Runtime Tool Notes

Source of truth inventory: `src/fraudguard_agent/tools.py`.

Tools hanya memanggil fixed FraudGuard Core endpoints. Tidak ada shell, SQL, filesystem,
generic network, banking, messaging, policy-editing, atau public-reporting capability.
Credential diinject lewat environment dan tidak masuk prompt atau response.
`create_intervention` memakai idempotency key dan hanya dijalankan dari decision Core
non-`ALLOW` melalui action matrix runtime.
