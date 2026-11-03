"""Post-process the frb-generated Dart so `bool` means the real Dart bool.

frb 1.80.1 emits `typedef bool = ffi.NativeFunction<...>` at the top of the
generated file. That typedef shadows core `bool` for every library importing it,
so `if (await bind.foo())`, `bool x = false` and `!bind.bar()` stop compiling.

Fix:
  1. rename that typedef to `ndbool` (it really is a callback type),
  2. use ffi.Bool for the wire layer,
  3. let wire wrappers take a Dart bool and hand FFI a real Pointer<Bool>.
"""
import io
import re

P = r"D:\build\rustdesk-src\flutter\lib\generated_bridge.dart"
s = io.open(P, encoding="utf-8").read()

old = "typedef bool = ffi.NativeFunction<ffi.Int Function(ffi.Pointer<ffi.Int>)>;"
assert old in s
s = s.replace(old, "typedef ndbool = ffi.NativeFunction<ffi.Int Function(ffi.Pointer<ffi.Int>)>;")

s = s.replace("ffi.Pointer<bool>", "ffi.Pointer<ffi.Bool>")

s = re.sub(r"\bndbool\b(?=\s+\w+\s*\()", "bool", s)
s = s.replace("Future<ndbool>", "Future<bool>").replace("Future<ndbool?>", "Future<bool?>")
s = s.replace("Stream<ndbool>", "Stream<bool>").replace("List<ndbool>", "List<bool>")

WRAP = re.compile(
    r"(  (?:\w+|WireSyncReturn) (wire_\w+)\((.*?)\) \{\n)(.*?)(\n  \}\n)", re.S
)


def fix_wrapper(m):
    head, name, params, body, tail = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
    bools = re.findall(r"ffi\.Pointer<ffi\.Bool> (\w+)", params)
    if not bools:
        return m.group(0)
    new_params = re.sub(r"ffi\.Pointer<ffi\.Bool> (\w+)", r"bool \1", params)
    call = re.search(rf"_?{re.escape(name)}\((.*?)\);", body, re.S)
    if call:
        args = call.group(1)
        for b in bools:
            args = re.sub(rf"\b{re.escape(b)}\b", f"_ab({b})", args)
        body = body[: call.start(1)] + args + body[call.end(1) :]
    return head[: -len(params) - 4] + new_params + ") {\n" + body + tail


s, n = WRAP.subn(fix_wrapper, s)

helper = """
ffi.Pointer<ffi.Bool> _ab(bool v) {
  final p = ffi.calloc<ffi.Bool>();
  p.value = v;
  return p;
}
"""
s = s.replace("typedef ndbool = ", helper + "\ntypedef ndbool = ", 1)

io.open(P, "w", encoding="utf-8", newline="\n").write(s)
print("wrappers rewritten:", n, "| leftover Pointer<bool>:", s.count("ffi.Pointer<bool>"))
