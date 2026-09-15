# ClawLink Study relay

This service binds only to `127.0.0.1:19101`. It accepts valid CLX/1 JSON
envelopes at `POST /v1/messages`, sends bounded `ASK` messages to Worker Agent's
local agent gateway, and appends inbound/outbound records to
`relay/logs/messages.jsonl` with `fsync` on every write.

It is deliberately not exposed through Tailscale Serve or a public listener.
Coordinator Agent reaches it only through the already-authenticated SSH-over-Tailscale
channel. This isolates the experiment while keeping a complete audit trail.
