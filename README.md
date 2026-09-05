# TihTok

Decompilation / modding workspace for the TihTok APK.

## How it works

1. The APK (`Tihtok.apk`) is attached as an asset on a GitHub **release** (it's 214MB, too big for git).
2. The [`Decompile APK`](.github/workflows/decompile.yml) Action downloads it, runs **apktool** on it, and tars the result.
3. The decompiled tree (`decoded.tar.zst`) is uploaded back to the release, so it can be pulled anywhere — no local decompiling needed.

## Usage

- Re-run decompile: **Actions → Decompile APK → Run workflow**
- Get decompiled source: download `decoded.tar.zst` from the latest release, then
  `tar --zstd -xf decoded.tar.zst`
