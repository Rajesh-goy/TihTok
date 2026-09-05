# TihTok Mods

Overlay applied onto the apktool-decoded tree at build time (see `.github/workflows/build.yml`).

## Patches (v1 — "100% USA" region spoof, no VPN)

| File | What it does |
|---|---|
| `smali_classes31/X/0izS.smali` | TikTok's internal region-mock holder (`ITtmockService` statics). All region slots (carrier/sim region, sys region, MCC region, current region, op region) hardcoded to `"US"`. Every region getter in `X/0v8q` checks these first, so the whole app resolves US. |
| `smali_classes5/X/08dR.smali` | MCC reader now always returns `"310"` (US MCC). Used by geo-blocking and analytics params. |
| `smali_classes29/.../GeoBlockingServiceImpl.smali` | The geo-block engine is neutered: master switch returns `false`, popup/show methods are no-ops, popup-ID lookup returns null. The "region restricted" dialog can never be triggered by this path. |

## Why this can't cause self-restarts

Every replaced method keeps its original `MethodCollector` tracker id and balanced `i()`/`o()` calls — the native-side watchdog that normally force-restarts an app when a tracked method never closes stays quiet.

## Known limit (the honest one)

If TikTok's **servers** decide by your **IP address** (India → "server error" / feed refusal), no client-side patch can change that — the server sees the connection's IP. The no-VPN workaround is traffic-level:

- TikTok's network stack (OkHttp/Cronet) honors the **Wi-Fi proxy** setting
- Set Wi-Fi proxy to a US proxy (e.g. a tiny VPS running squid/tinyproxy at `IP:3128`)
- TikTok traffic exits from a US IP; every other app stays on your normal connection
- No VPN app, no VPN profile, kill-switch-free

## Rebuild

Push changes to `mods/`, then run **Actions → Build Modded APK**. The signed `TihTok-modded.apk` lands on the release page.
