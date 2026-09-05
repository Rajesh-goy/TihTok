#!/usr/bin/env python3
"""Apply TihTok region-spoof patches to an apktool --no-res decode tree.

Strategy: minimal anchor-based insertions into ORIGINAL smali files.
- Every early-return keeps the MethodCollector i()/o() pair balanced.
- Any missing/ambiguous anchor fails the build loudly (nonzero exit).
"""
import re
import sys
import os

TRACKER_I = "MethodCollector;->i(I)V"
TRACKER_O = "MethodCollector;->o(I)V"


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().split("\n")


def write(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def method_sections(lines):
    """Yield (start, end) line-index ranges for each .method block."""
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith(".method"):
            start = i
        elif ln.startswith(".end method") and start is not None:
            yield start, i
            start = None


def find_method_range(lines, signature):
    hits = [r for r in method_sections(lines) if signature in lines[r[0]]]
    if len(hits) != 1:
        raise SystemExit(f"FAIL {signature}: found {len(hits)} method matches, need exactly 1")
    return hits[0]


def tracker_reg(line):
    m = re.search(r"\{(v\d+)\}", line)
    if not m:
        raise SystemExit(f"FAIL: no register in tracker line: {line}")
    return m.group(1)


def early_return(lines, signature, ret):
    """Insert a balanced early-return right after the tracker i() call.

    ret: 'false' | 'true' | 'null' | 'void'
    """
    s, e = find_method_range(lines, signature)
    reg = None
    for i in range(s, e):
        if TRACKER_I in lines[i]:
            reg = tracker_reg(lines[i])
            ins = i + 1
            break
    if reg is None:
        raise SystemExit(f"FAIL {signature}: no tracker i() call found")
    block = [f"    invoke-static {{{reg}}}, Lcom/bytedance/frameworks/apm/trace/{TRACKER_O}"]
    if ret == "false":
        block += ["    const/4 v0, 0x0", "    return v0"]
    elif ret == "true":
        block += ["    const/4 v0, 0x1", "    return v0"]
    elif ret == "null":
        block += ["    const/4 v0, 0x0", "    return-object v0"]
    elif ret == "void":
        block += ["    return-void"]
    else:
        raise SystemExit(f"unknown ret {ret}")
    lines[ins:ins] = block
    print(f"patched {signature}: early return {ret}")


def insert_after_index(lines, idx, block):
    lines[idx + 1:idx + 1] = block
    print(f"patched after line {idx + 1}: {lines[idx].strip()[:60]}...")


def insert_after_unique(lines, anchor, block):
    idx = [i for i, ln in enumerate(lines) if anchor in ln]
    if len(idx) != 1:
        raise SystemExit(f"FAIL anchor not unique ({len(idx)}x): {anchor}")
    lines[idx[0] + 1:idx[0] + 1] = block
    print(f"patched after anchor: {anchor[:60]}...")


def patch_0izS(root):
    p = os.path.join(root, "smali_classes31/X/0izS.smali")
    lines = read(p)
    # 1) Override every region static with "US" at the end of <clinit>
    #    + force en_US locale and America/New_York timezone process-wide
    #    (this clinit runs very early: first region query during app init)
    insert_after_unique(
        lines,
        "sput-object v1, LX/0izS;->LJ:Ljava/lang/String;",
        [
            '    const-string v0, "US"',
            "    sput-object v0, LX/0izS;->LIZIZ:Ljava/lang/String;",
            "    sput-object v0, LX/0izS;->LIZJ:Ljava/lang/String;",
            "    sput-object v0, LX/0izS;->LIZLLL:Ljava/lang/String;",
            "    sput-object v0, LX/0izS;->LJ:Ljava/lang/String;",
            # NOTE: v2 holds the tracker id for the closing o(I)V call — use v0 only.
            '    const-string v0, "en-US"',
            "    invoke-static {v0}, Ljava/util/Locale;->forLanguageTag(Ljava/lang/String;)Ljava/util/Locale;",
            "    move-result-object v0",
            "    invoke-static {v0}, Ljava/util/Locale;->setDefault(Ljava/util/Locale;)V",
            '    const-string v0, "America/New_York"',
            "    invoke-static {v0}, Ljava/util/TimeZone;->getTimeZone(Ljava/lang/String;)Ljava/util/TimeZone;",
            "    move-result-object v0",
            "    invoke-static {v0}, Ljava/util/TimeZone;->setDefault(Ljava/util/TimeZone;)V",
        ],
    )
    # 2) ITtmockService provider now returns null (keep tracker balanced)
    early_return(
        lines,
        "LIZ()Lcom/ss/android/ugc/aweme/offline/ttmock/ITtmockService;",
        "null",
    )
    write(p, lines)


def patch_08dR(root):
    p = os.path.join(root, "smali_classes5/X/08dR.smali")
    lines = read(p)
    s, e = find_method_range(lines, "LIZ()Ljava/lang/String;")
    body = lines[s:e]
    if not any(ln.strip() == ":goto_0" for ln in body):
        raise SystemExit("FAIL 08dR: :goto_0 label not found in LIZ()")
    tr_idx = [i for i in range(s, e) if TRACKER_I in lines[i]]
    if len(tr_idx) != 1:
        raise SystemExit(f"FAIL 08dR: expected 1 tracker i() in LIZ(), found {len(tr_idx)}")
    # Jump straight to the shared exit label: return-object v2 with v2 = "310" (US MCC)
    insert_after_index(lines, tr_idx[0], ['    const-string v2, "310"', "    goto/16 :goto_0"])
    write(p, lines)


def patch_geoblock(root):
    p = os.path.join(
        root,
        "smali_classes29/com/ss/android/ugc/aweme/compliance/business/"
        "geoblocking/GeoBlockingServiceImpl.smali",
    )
    lines = read(p)
    early_return(lines, "LIZ()Z", "false")                    # master geo-block switch
    early_return(lines, "LIZLLL(Landroid/os/Bundle;)Z", "true")   # path-allowlist -> always allowed
    early_return(lines, "LJFF(Ljava/lang/String;)Z", "false")     # popup id gate
    early_return(lines, "LIZJ(ILjava/lang/String;)V", "void")     # trigger popup event
    early_return(lines, "LJ(Ljava/lang/String;Ljava/lang/String;)V", "void")  # popup click handler
    early_return(lines, "LJI(Ljava/lang/String;)V", "void")       # popup shower
    early_return(lines, "LJII(Ljava/lang/String;)V", "void")      # popup id recorder
    write(p, lines)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "decoded"
    if not os.path.isdir(root):
        raise SystemExit(f"FAIL: decode root {root} missing")
    patch_0izS(root)
    patch_08dR(root)
    patch_geoblock(root)
    print("All mods applied.")


if __name__ == "__main__":
    main()
