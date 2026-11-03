"""Bake the stealth defaults into the DeskLink client.

The stock client shows a tray icon and pops the connection-manager window on
every incoming session. Both are gated behind options we cannot set from a
packed portable exe (custom.txt has to be signed), so the defaults flip in code:
anything the user sets in the config still wins.
"""
import io
import re

SRC = r"D:\build\rustdesk-src"

# 1. approve-mode defaults to password, verification to the permanent password,
#    and hide_cm is always allowed for our build (stock needs a pro/custom flag).
p = SRC + r"\libs\hbb_common\src\password_security.rs"
s = io.open(p, encoding="utf-8").read()

old = '''fn verification_method() -> VerificationMethod {
    let method = Config::get_option("verification-method");'''
assert old in s
s = s.replace(old, '''fn verification_method() -> VerificationMethod {
    let method = Config::get_option("verification-method");
    if method.is_empty() {
        // DeskLink: unattended by default, never the ask-a-human flow
        return VerificationMethod::OnlyUsePermanentPassword;
    }''', 1)

old = '''pub fn approve_mode() -> ApproveMode {
    let mode = Config::get_option("approve-mode");'''
assert old in s
s = s.replace(old, '''pub fn approve_mode() -> ApproveMode {
    let mode = Config::get_option("approve-mode");
    if mode.is_empty() {
        // DeskLink: no accept window, a password is enough
        return ApproveMode::Password;
    }''', 1)

old = '''pub fn hide_cm() -> bool {
    approve_mode() == ApproveMode::Password
        && verification_method() == VerificationMethod::OnlyUsePermanentPassword
        && crate::config::option2bool("allow-hide-cm", &Config::get_option("allow-hide-cm"))
}'''
assert old in s
s = s.replace(old, '''pub fn hide_cm() -> bool {
    approve_mode() == ApproveMode::Password
        && verification_method() == VerificationMethod::OnlyUsePermanentPassword
        && (crate::config::option2bool("allow-hide-cm", &Config::get_option("allow-hide-cm"))
            || crate::common::is_custom_client())
}''', 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("password_security patched")

# 2. no tray icon
p = SRC + r"\src\tray.rs"
s = io.open(p, encoding="utf-8").read()
hits = len(re.findall(r'get_builtin_option\(keys::OPTION_HIDE_TRAY\) == "Y"', s))
assert hits == 2, hits
s = re.sub(r'get_builtin_option\(keys::OPTION_HIDE_TRAY\) == "Y"',
           'get_builtin_option(keys::OPTION_HIDE_TRAY) == "Y"\n            || crate::common::is_custom_client()', s)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("tray patched, sites:", hits)
