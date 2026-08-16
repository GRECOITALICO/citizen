# Windows uninstall (Citizen WSL2 adapter)

**Preflight — not a public release.**

## Remove Citizen service (inside WSL)

```bash
systemctl --user disable --now citizen-seed-living.service
rm -f ~/.config/systemd/user/citizen-seed-living.service
systemctl --user daemon-reload
```

## Remove Windows integration

```powershell
Unregister-ScheduledTask -TaskName CONRRAD-Citizen-WSL2-Autostart -Confirm:$false -ErrorAction SilentlyContinue
```

## Remove WSL distro (optional)

```powershell
wsl --unregister CONRRAD-Citizen
```

This does **not** remove unrelated WSL distributions.

## Remove Citizen state (destructive)

Delete `CITIZEN_HOME` on the Linux filesystem only when intentional:

```bash
rm -rf ~/.local/share/conrrad-citizen
```

## Notes

- Uninstall does not require AWS, Azure, or KMS credentials
- Linux release `v0.2.0` artifacts are unaffected
