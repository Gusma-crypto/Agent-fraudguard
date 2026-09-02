# /payment-check

Send `external_payment_id`, `amount`, `currency`, and `recipient_ref` as structured
chat context. The agent selects `safety_payment` and Core applies idempotency/policy.
Never request PIN, password, OTP, CVV, or bank credentials. Never imply that the agent
moved funds or bypassed Core.
