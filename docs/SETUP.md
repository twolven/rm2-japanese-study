# xovi + AppLoad + Vellum + KOReader on a reMarkable 2 (firmware 3.25.1.1)

Notes from one working install. Everything is under `/home/root`, so it survives OS updates; a reboot returns to stock until you run `xovi/start`.

## Compatibility findings (firmware 3.25.1.1, rM2)

- **xovi 0.3.x**: lists rM2, no OS cap in the [Vellum feed](https://vellum.delivery/feeds/rm2.rss).
- **AppLoad**: only **0.4.x (OS 3.22–3.26)** covers 3.25. 0.5.x needs 3.26+, 0.6.x needs 3.28+.
- **`launcherctl-appload`** (only 0.5.x / 0.6.x exist) pulls in `lockscreen_hook`, which needs 3.27.1+. Skip it and install `appload` directly.
- **KOReader**: no OS cap; the wiki lists rM1/rM2 support from 3.20.

## Steps

1. Back up `/home/root/.local/share/remarkable/xochitl/` and `/usr/share/remarkable/templates/` (e.g. `tar` over `ssh`), and compare file counts.
2. Enable SSH key auth. Optional SSH over WLAN: `touch /home/root/.config/remarkable/rm_enable_ssh_wifi_marker && systemctl start dropbear-wlan.socket`.
3. Optional — stop OS auto-updates: `systemctl stop update-engine && systemctl disable update-engine`, plus a drop-in
   `/etc/systemd/system/update-engine.service.d/disable.conf` containing `[Unit]` / `ConditionPathExists=/nonexistent` (`systemctl mask` fails because a real unit file exists).
4. Install Vellum: download `bootstrap.sh` from the [vellum-cli releases](https://github.com/vellum-dev/vellum-cli/releases), verify the SHA-256 listed in its README, read the script, then run it on the tablet.
5. `vellum add appload koreader` (installs xovi, xovi-extensions, qt-resource-rebuilder, AppLoad 0.4.2 and KOReader).
6. `bash /home/root/xovi/rebuild_hashtable` (press Enter at the prompt), then `bash /home/root/xovi/start`.
7. On the tablet: sidebar → AppLoad → KOReader.
8. Fonts go in `koreader/fonts/<folder>/`, StarDict dictionaries in `koreader/data/dict/<name>/` (both under `/home/root/xovi/exthome/appload/koreader/`).

## Temporarily disable xovi / revert

- `bash /home/root/xovi/stock` returns to stock xochitl; `xovi/start` re-enables it; a reboot also returns to stock.
- Full removal: `xovi/stock`, `vellum del koreader appload xovi-extensions qt-resource-rebuilder xovi`, `rm -rf /home/root/xovi /home/root/.vellum /home/root/shims`, remove the `.vellum` lines from `/home/root/.bashrc`, restore `templates.json`, and re-enable `update-engine`.

## After an OS update

`vellum check-os <new version>` first. Afterwards `vellum upgrade`, `xovi/rebuild_hashtable`, `xovi/start`. Custom templates must be re-copied (system partition is replaced). If AppLoad disappears from the sidebar, pick an AppLoad build whose OS range covers the new version.
