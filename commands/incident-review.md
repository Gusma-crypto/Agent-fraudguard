# /incident-review

Provide a trusted incident ID in chat context so the agent selects `get_incident`.
For audit, provide a Core trace ID and request audit so it selects `get_trace_audit`.
This command is read-only and must not modify learning state or trigger enforcement.
