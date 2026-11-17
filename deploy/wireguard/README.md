# WireGuard gateway (agx64 -> VPS)

This is the deployed shape, not a secret-bearing config. Generate keys on the
hosts and keep private keys in `/etc/wireguard` only.

## VPS (`megasrv`)

- `wg0`: `10.66.0.1/24`, UDP `51820`.
- Peer: agx64 public key, `AllowedIPs = 10.66.0.2/32`.
- UFW: allow `51820/udp`; do not expose `11434`.

## agx64

- `wg0`: `10.66.0.2/24`; peer endpoint `152.53.196.118:51820`;
  `AllowedIPs = 10.66.0.1/32`; `PersistentKeepalive = 25`.
- Ubuntu 20.04 has no kernel WireGuard module here, so the deployed unit starts
  `wireguard-go` and applies the peer with `wg`. It does not touch `wg1`.
- Verify with `sudo wg show wg0` and `ping -c 2 10.66.0.1`.

## Firewall on agx64

The host uses `SPARKNET-FW-IN` for TCP `11434`. Allow only the WireGuard source:

```text
-A SPARKNET-FW-IN -s 10.66.0.0/24 -j RETURN
```

A systemd drop-in re-adds the rule after the Sparknet firewall unit.

Do not copy private keys, preshared keys or rendered configs into this repo.
