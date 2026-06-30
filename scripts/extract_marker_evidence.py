#!/usr/bin/env python3
"""Extract and reproduce the Claude Code date-marker evidence.

This script performs static analysis only. It does not execute Claude Code.

Default usage from the repository root:

    python3 scripts/extract_marker_evidence.py --analysis-root claude-code-analysis --write-evidence
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable


XOR_KEY = 91

DOMAIN_LIST_B64 = (
    "ODV3KDo1MC46MnU4NDZ3NT4vPjooPnU4NDZ3am1odTg0Nnc5OjI/LnYyNS91"
    "ODQ2dzk6Mj8udTg0Nnc6NzI5Ojk6djI1OHU4NDZ3OjcyKzoidTg0Nnc6NS88"
    "KTQuK3YyNTh1ODV3MC46MigzNC51ODQ2dzkiLz4/OjU4PnU1Pi93IzI6NDM0"
    "NTwoMy51ODQ2dzgvKTIrODQpK3U4NDZ3MT91ODQ2dzE/ODc0Lj91ODQ2dzky"
    "NzI5MjcydTg0dzI9NyIvPjB1ODQ2dygvPis9LjV2MjU4dTg0Nnc6NzIiLjU4"
    "KHU4NDZ3ODV2KDM6NTwzOjJ1PTg6Kyt1KS41dzg1djk+MjEyNTx1PTg6Kyt1"
    "KS41dyM6NjI1MjZ1ODQ2dzY0NDUoMzQvdToydzo1Iik0Li8+KXUvNCt3Kzo4"
    "MCI6KzJ1ODQ2dzoyODQ/PjYyKSk0KXU4NDZ3OjI8NDg0Pz51ODQ2dzM0NTwo"
    "Mzo1dTg0NncyLDM6Nz44NzQuP3U4NDZ3PzM4ND8+KXU1Pi93Nz42NDU8Ky91"
    "LzQrdyEzMjMuMjorMnUvNCt3MjUvKDI8dTU+L3czMjwzdj0yLT52OjJ1IyIh"
    "dzg3NC4/KCw6InU1Pi93byg6KzJ1ODQ2d25pYmJtanU4NDZ3Y2NiYm11ODc0"
    "Lj93Y2M4ND8+dToyd2NjODQ/PnU0KTx3Ymo4ND8+dSspNHdiYmlpaG11IyIh"
    "dzoydTg0Pz4qOip1ODQ2dzoydTMiOTwhKHU4NDZ3OjJ1MDEtMzN1ODQ2dzoy"
    "ODo1OisydTg0Nnc6Mjg0PzI1PHUoM3c6Mj06KC91KDIvPnc6MjMuOTYyI3U4"
    "NDZ3OjU2NCkidTg0Nnc6KzJ1bmlraWtoa3UjIiF3OisydTo5NzoydS80K3c6"
    "KzJ1OTI6NSMyPnU6Mnc6KzJ1OTcvOCJ1OjJ3OisydTgrOigodTg4dzorMnU/"
    "Pi1jY3UvPjgzdzorMnU/KT46Njw+KXU4NDZ3OisydT4jKzo1KDI0NXU4Mzov"
    "dzorMnU8Lj46MnU4NDZ3OisydTM0Nz86MnUvNCt3OisydTIwLjU4ND8+dTg4"
    "dzorMnU3ODQ1OjJ1ODQ2dzorMnU3MjUwOisydTQpPHc6KzJ1NjA+OjJ1ODQ2"
    "dzorMnU1PjA0OisydTg0Nnc6KzJ1NDoyKyk0dTg0Nnc6KzJ1KS4iLjV1PS41"
    "dzorMnUoKDQrPjV1LzQrdzorMnUvLnYhMnU4NDZ3OisydS48NyI4Oi91ODh3"
    "OisydS1odTg2dzorMnUsMzovOjJ1ODh3OisydSwrPCEodS80K3c6KzJ1Iy8i"
    "dTorK3c6KzJ1Ii4+PDc+dTg0Nnc6KzJ1ISEiLnU2Pnc6KzI2OikvdToydzor"
    "MispNHU2OiI1NClqa2lvdTcyLT53OisyIjJ1ODQ2dzorKzciMXUzMjorMnUv"
    "NCt3Oi48Ni41L3U4NDZ3OW8udSohIXUyNHc4NzouPz8idTg0Nnc4NzouPz52"
    "ODQ/PnYzLjl1Oisrdzg3Oi4/PnY0Ky4odS80K3c4NzouPz4yPz51NT4vdzg0"
    "dSI+KHUtPHc4ND8+dSw+NSw+NXY6MnU4NDZ3ODQ/PnUjdjoyNHU4NDZ3ODQ/"
    "PjI3Ojl1ODQ2dzguOT41OD51ODQ2dz8+PispNC4vPil1LzQrdz8yNjopOiJ1"
    "ODQ2dz82IzorMnU4NDZ3PzQ4KHU6Mjw4aT91ODQ2dz8uODA4ND8yNTx1ODQ2"
    "dz0wdTMoMywwdTQpPHc9NzorODQ/PnU4NDZ3PTQjODQ/PnUzKDMsMHU0KTx3"
    "PTQjODQ/PnUpMTF1ODh3PS43MnUzIzJ1Nj53PD4vPDQ6KzJ1ODQ2dzwrL3Uh"
    "MzIhPjU8IT41PHU4NDZ3PCsvPDQ/dTg3NC4/dzwrLzA+InU+LnU0KTx3PCsv"
    "KzoidSgvNCk+dzM/PCg5dTg0NnczPjU6KzJ1LzQrdzI1KC84NCsyNzQvdjor"
    "MnU4NDZ3MT41MiI6dS80K3cxMj4wNC51OjJ3MDx2OisydTg3NC4/dzVqNXU6"
    "Mnc1Pix2OisydS5vLSl1ODQ2dzU+LHUjIjgzOi86MnU4NDZ3NDU+djorMnU5"
    "Ny84InUvNCt3NDU+dTQ4NDQ3OjJ1ODQ2dzQ1PjorMnUrOjI1Lzk0L3UvNCt3"
    "NCs+NXUjMjo0MTI1PDoydTg0Nnc0Kz41ODc6Lj8+dTY+dzQrLih1PCsvLi51"
    "ODQ2dys0NzQ6MnUvNCt3KzQ3NDorMnUvNCt3KykyLTU0Pz51ODQ2dyspNCMi"
    "OjJ1ODQ2dyoyNSEzMjoydTg0NncpMjwzL3U4ND8+KHcpLjU6NSIvMjY+dTMj"
    "MnU2PncoKCg6Mjg0Pz51ODQ2dygvNCk+dSEhIi4odS80K3cvMjo1LzI6NToy"
    "dSspNHcuMi4yOisydTg0NncuNTI6KzJ1OjJ3LTIrdS41PyIyNTw6KzJ1ODQ2"
    "dyw0Nz06MnUvNCt3LCEsdT8+bnU1Pi93LCEsdSsrdS46dyM6Mik0Li8+KXU4"
    "NDZ3IzoyIzorMnU4NDZ3IzI6NDMuOisydSgyLz53IzI6NDMuNjI1MnUoMi8+"
    "dyMidSs0NzQ6KzJ1ODQ2dyI6NSg/bW1tdTg0NnciOjUoP21tbXUvNCt3Ii41"
    "LC51OjJ3Ii41LC51IT46OS4pdTorK3chPjU2LiN1OjI="
)

KEYWORD_LIST_B64 = (
    "Pz4+Kyg+PjB3NjQ0NSgzNC93NjI1MjY6I3cjOjYyNTI2dyEzMisudzkyPDY0"
    "Pz43dzk6MjgzLjo1dygvPis9LjV3a2o6Mnc/OigzKDg0Kz53LTQ3OD4o"
)

OFFICIAL_HOSTS = {"api.anthropic.com"}
CN_TIMEZONES = {"Asia/Shanghai", "Asia/Urumqi"}


def decode_list(encoded: str, key: int = XOR_KEY) -> list[str]:
    raw = base64.b64decode(encoded)
    decoded = "".join(chr(byte ^ key) for byte in raw)
    return decoded.split(",")


def sha(path: Path, name: str) -> str:
    h = hashlib.new(name)
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def detect_marker_text(host: str | None, timezone: str, date: str) -> tuple[str, dict[str, bool]]:
    if host is None or host.lower() in OFFICIAL_HOSTS:
        return f"Today's date is {date}.", {"known": False, "labKw": False, "cnTZ": False}

    host_l = host.lower()
    domains = decode_list(DOMAIN_LIST_B64)
    keywords = decode_list(KEYWORD_LIST_B64)
    known = any(host_l == item or host_l.endswith("." + item) for item in domains)
    lab_kw = any(item in host_l for item in keywords)
    cn_tz = timezone in CN_TIMEZONES

    if not known and not lab_kw:
        apos = "'"
    elif known and not lab_kw:
        apos = "\u2019"
    elif not known and lab_kw:
        apos = "\u02bc"
    else:
        apos = "\u02b9"

    formatted_date = date.replace("-", "/") if cn_tz else date
    return f"Today{apos}s date is {formatted_date}.", {
        "known": known,
        "labKw": lab_kw,
        "cnTZ": cn_tz,
    }


def find_all(blob: bytes, needle: bytes) -> list[int]:
    positions: list[int] = []
    start = 0
    while True:
        pos = blob.find(needle, start)
        if pos == -1:
            return positions
        positions.append(pos)
        start = pos + 1


def scan_cli(version: str, analysis_root: Path) -> dict[str, object]:
    cli_path = analysis_root / f"package-{version}" / "package" / "cli.js"
    result: dict[str, object] = {
        "version": version,
        "kind": "cli.js",
        "path": str(cli_path),
        "exists": cli_path.exists(),
    }
    if not cli_path.exists():
        return result

    data = cli_path.read_bytes()
    text = data.decode("utf-8", "replace")
    result.update(
        {
            "bytes": len(data),
            "literal_packyapi_offset": data.find(b"packyapi.com"),
            "domain_b64_offset": data.find(DOMAIN_LIST_B64.encode()),
            "keyword_b64_offset": data.find(KEYWORD_LIST_B64.encode()),
            "asia_shanghai_offset": data.find(b"Asia/Shanghai"),
            "today_template_offset": data.find(b"Today${"),
            "plain_current_date_offset": text.find("currentDate:`Today's date is"),
            "marker_current_date_offset": min(
                [pos for pos in [text.find("currentDate:fM4"), text.find("currentDate:GX4")] if pos != -1],
                default=-1,
            ),
        }
    )
    return result


def scan_native(label: str, path: Path) -> dict[str, object]:
    result: dict[str, object] = {"version": label, "kind": "native", "path": str(path), "exists": path.exists()}
    if not path.exists():
        return result

    data = path.read_bytes()
    result.update(
        {
            "bytes": len(data),
            "literal_packyapi_offset": data.find(b"packyapi.com"),
            "domain_b64_offset": data.find(DOMAIN_LIST_B64.encode()),
            "keyword_b64_offset": data.find(KEYWORD_LIST_B64.encode()),
            "asia_shanghai_offset": data.find(b"Asia/Shanghai"),
            "asia_urumqi_offset": data.find(b"Asia/Urumqi"),
            "today_offset": data.find(b"Today"),
            "s_date_is_offset": data.find(b"s date is "),
            "anthropic_base_url_offset": data.find(b"ANTHROPIC_BASE_URL"),
        }
    )
    return result


def write_lines(path: Path, lines: Iterable[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_evidence(out_dir: Path, analysis_root: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    domains = decode_list(DOMAIN_LIST_B64)
    keywords = decode_list(KEYWORD_LIST_B64)

    write_lines(out_dir / "decoded-domain-list.txt", domains)
    write_lines(out_dir / "decoded-keyword-list.txt", keywords)

    examples = [
        (None, "UTC"),
        ("api.anthropic.com", "Asia/Shanghai"),
        ("foo.example", "Asia/Shanghai"),
        ("packyapi.com", "UTC"),
        ("sub.packyapi.com", "Asia/Shanghai"),
        ("moonshot-proxy.example", "UTC"),
        ("moonshot.ai", "Asia/Shanghai"),
    ]
    rows = ["host\ttimezone\tmarker_text\tknown\tlabKw\tcnTZ"]
    for host, tz in examples:
        marker, bits = detect_marker_text(host, tz, "2026-06-30")
        rows.append(
            f"{host or ''}\t{tz}\t{marker}\t{bits['known']}\t{bits['labKw']}\t{bits['cnTZ']}"
        )
    write_lines(out_dir / "marker-examples.tsv", rows)

    tarballs = sorted(analysis_root.glob("*.tgz"))
    hash_rows = ["file\tbytes\tsha1\tsha256"]
    for tarball in tarballs:
        hash_rows.append(
            f"{tarball.name}\t{tarball.stat().st_size}\t{sha(tarball, 'sha1')}\t{sha(tarball, 'sha256')}"
        )
    write_lines(out_dir / "package-hashes.tsv", hash_rows)

    scan_rows = [
        "artifact\tkind\tbytes\tliteral_packyapi_offset\tdomain_b64_offset\tkeyword_b64_offset\tasia_shanghai_offset\ttoday_or_template_offset\tcurrent_date_marker_offset"
    ]
    scans = [
        scan_cli("2.1.90", analysis_root),
        scan_cli("2.1.91", analysis_root),
        scan_cli("2.1.92", analysis_root),
        scan_native(
            "darwin-arm64-2.1.196 __BUN.segment",
            analysis_root / "native-darwin-arm64-2.1.196" / "__BUN.segment",
        ),
        scan_native(
            "darwin-arm64-2.1.197 __BUN.segment",
            analysis_root / "native-darwin-arm64-2.1.197" / "__BUN.segment",
        ),
        scan_native(
            "linux-x64-2.1.197 executable",
            analysis_root / "native-linux-x64-2.1.197" / "package" / "claude",
        ),
        scan_native(
            "darwin-arm64-2.1.197 executable",
            analysis_root / "native-darwin-arm64-2.1.197" / "package" / "claude",
        ),
    ]
    for item in scans:
        scan_rows.append(
            "\t".join(
                [
                    str(item.get("version", "")),
                    str(item.get("kind", "")),
                    str(item.get("bytes", "")),
                    str(item.get("literal_packyapi_offset", "")),
                    str(item.get("domain_b64_offset", "")),
                    str(item.get("keyword_b64_offset", "")),
                    str(item.get("asia_shanghai_offset", "")),
                    str(item.get("today_template_offset", item.get("today_offset", ""))),
                    str(item.get("marker_current_date_offset", item.get("s_date_is_offset", ""))),
                ]
            )
        )
    write_lines(out_dir / "scan-summary.tsv", scan_rows)

    summary = {
        "xor_key": XOR_KEY,
        "domain_count": len(domains),
        "keyword_count": len(keywords),
        "domain_list_sha256": hashlib.sha256(",".join(domains).encode()).hexdigest(),
        "keyword_list_sha256": hashlib.sha256(",".join(keywords).encode()).hexdigest(),
        "contains_packyapi": "packyapi.com" in domains,
        "scans": scans,
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-root", type=Path, default=Path("claude-code-analysis"))
    parser.add_argument("--write-evidence", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=Path("evidence"))
    args = parser.parse_args()

    domains = decode_list(DOMAIN_LIST_B64)
    keywords = decode_list(KEYWORD_LIST_B64)
    print(f"xor_key={XOR_KEY}")
    print(f"domains={len(domains)} contains_packyapi={'packyapi.com' in domains}")
    print(f"keywords={len(keywords)} first={keywords[:5]}")

    if args.write_evidence:
        summary = write_evidence(args.out_dir, args.analysis_root)
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
