#!/usr/bin/env python3
"""Static layer-boundary checks for CubeMX implementation-owned code."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence


DEFAULT_DIRS: tuple[str, ...] = ("Common", "Module", "app", "APP", "Board", "board", "Config", "config")
CORE_DIRS: tuple[str, ...] = ("Core/Src", "Core/Inc")
SOURCE_SUFFIXES = {".c", ".h", ".cc", ".hh", ".cpp", ".hpp", ".cxx", ".hxx"}

APP_LAYERS = {"app", "APP"}
BOARD_LAYERS = {"Board", "board"}
CONFIG_LAYERS = {"Config", "config"}

INCLUDE_RE = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]')
APP_INCLUDE_RE = re.compile(r"(^|[/\\])(app|APP)([/\\]|$)")

HARDWARE_INCLUDE_RE = re.compile(
    r"("
    r"stm32[a-z0-9_]*hal[a-z0-9_]*\.h|"
    r"stm32[a-z0-9_]*ll[a-z0-9_]*\.h|"
    r"(?:^|[/\\])(main|gpio|tim|i2c|spi|usart|uart|adc|dac|dma|rtc|crc|iwdg|wwdg|can|fdcan)\.h$|"
    r"_[a-z0-9]*(gpio|pwm|i2c|spi|uart|usart|adc|dac|tim|timer|dma|can|fdcan)\.h$"
    r")",
    re.IGNORECASE,
)

BOARD_INCLUDE_RE = re.compile(r"(^|[/\\])(?:board|Board)([/\\].*|\.h$)", re.IGNORECASE)

HARDWARE_TYPE_RE = re.compile(
    r"\b("
    r"GPIO_TypeDef|GPIO_PinState|"
    r"I2C_HandleTypeDef|SPI_HandleTypeDef|UART_HandleTypeDef|USART_HandleTypeDef|"
    r"TIM_HandleTypeDef|DMA_HandleTypeDef|ADC_HandleTypeDef|DAC_HandleTypeDef|"
    r"IWDG_HandleTypeDef|WWDG_HandleTypeDef|RTC_HandleTypeDef|"
    r"CAN_HandleTypeDef|FDCAN_HandleTypeDef"
    r")\b"
)

CONCRETE_CAST_RE = re.compile(
    r"\([A-Za-z_][A-Za-z0-9_]*_(gpio|pwm|i2c|spi|uart|usart|adc|dac|tim|timer|dma|can|fdcan)_t\s*\*\)"
)

DYNAMIC_MEMORY_RE = re.compile(r"\b(malloc|calloc|realloc|free)\s*\(")

BOARD_BINDING_RE = re.compile(
    r"\b(board_init|board_get_[A-Za-z0-9_]*|HAL_[A-Za-z0-9_]*HandleTypeDef|"
    r"GPIO_TypeDef|GPIO_PinState|GPIO_PIN_[0-9A-Z_]+|GPIO[A-Z]\b|"
    r"h(?:i2c|spi|uart|usart|tim|adc|dac|dma|can|fdcan)[0-9]*)\b|"
    r"\bstatic\s+.*_[A-Za-z0-9_]*(?:gpio|pwm|i2c|spi|uart|usart|adc|dac|tim|timer|dma)_t\b",
    re.IGNORECASE,
)

SCATTERED_CONFIG_RE = re.compile(
    r"^\s*(#\s*define|static\s+const|const\s+|enum\b).*"
    r"(?<![A-Za-z0-9])(timeout|threshold|retry|calib|calibration|stack|queue|period|interval|delay)(?![A-Za-z0-9])",
    re.IGNORECASE,
)

LOCAL_CONFIG_RE = re.compile(r'^\s*#\s*include\s*[<"][^>"]*(?:_config\.h|config\.h)[>"]', re.IGNORECASE)

RTOS_DELAY_RE = re.compile(r"\bosDelay\s*\(")
WATCHDOG_RE = re.compile(r"\b(HAL_IWDG_Refresh|HAL_WWDG_Refresh|IWDG|WWDG)\b")
CALLBACK_DECL_RE = re.compile(r"^\s*(?:void|static\s+void)\s+[A-Za-z0-9_]*(?:IRQHandler|Callback)\s*\(")


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    path: str
    line: int
    message: str
    excerpt: str


@dataclass(frozen=True)
class SourceFile:
    path: Path
    relpath: str
    layer: str
    lines: list[str]
    code_lines: list[str]


def normalize_rel(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def existing_scan_roots(root: Path, include_core: bool) -> list[Path]:
    names = list(DEFAULT_DIRS)
    if include_core:
        names.extend(CORE_DIRS)
    result: list[Path] = []
    seen: set[str] = set()
    for name in names:
        candidate = root / Path(name)
        if candidate.exists() and candidate.is_dir():
            key = str(candidate.resolve()).casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(candidate)
    return result


def source_files(root: Path, scan_roots: Sequence[Path]) -> Iterator[SourceFile]:
    for scan_root in scan_roots:
        for path in sorted(scan_root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            rel = normalize_rel(path.relative_to(root))
            layer = rel.split("/", 1)[0]
            try:
                text = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                text = path.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            yield SourceFile(path=path, relpath=rel, layer=layer, lines=lines, code_lines=strip_comments(lines))


def strip_comments(lines: Sequence[str]) -> list[str]:
    stripped: list[str] = []
    in_block = False
    for line in lines:
        out: list[str] = []
        i = 0
        while i < len(line):
            if in_block:
                end = line.find("*/", i)
                if end < 0:
                    break
                i = end + 2
                in_block = False
                continue
            if line.startswith("/*", i):
                in_block = True
                i += 2
                continue
            if line.startswith("//", i):
                break
            out.append(line[i])
            i += 1
        stripped.append("".join(out))
    return stripped


def line_finding(rule_id: str, severity: str, source: SourceFile, index: int, message: str) -> Finding:
    return Finding(
        rule_id=rule_id,
        severity=severity,
        path=source.relpath,
        line=index + 1,
        message=message,
        excerpt=source.lines[index].strip(),
    )


def scan_file(source: SourceFile) -> Iterator[Finding]:
    is_app = source.layer in APP_LAYERS
    is_common = source.layer == "Common"
    is_module = source.layer == "Module"
    is_board = source.layer in BOARD_LAYERS
    is_config = source.layer in CONFIG_LAYERS
    is_core = source.layer == "Core"

    for index, line in enumerate(source.code_lines):
        include = INCLUDE_RE.search(line)
        if include:
            include_path = include.group(1)
            if is_app and HARDWARE_INCLUDE_RE.search(include_path):
                yield line_finding(
                    "APP_HARDWARE_INCLUDE",
                    "violation",
                    source,
                    index,
                    f"business application includes hardware or concrete driver header '{include_path}'",
                )
            if is_common and (HARDWARE_INCLUDE_RE.search(include_path) or BOARD_INCLUDE_RE.search(include_path)):
                yield line_finding(
                    "COMMON_HARDWARE_POLLUTION",
                    "violation",
                    source,
                    index,
                    f"Common capability layer includes hardware, board, or concrete driver header '{include_path}'",
                )
            if is_config and HARDWARE_INCLUDE_RE.search(include_path):
                yield line_finding(
                    "CONFIG_HARDWARE_POLLUTION",
                    "violation",
                    source,
                    index,
                    f"project configuration includes generated, hardware, or concrete driver header '{include_path}'",
                )
            if is_config and APP_INCLUDE_RE.search(include_path):
                yield line_finding(
                    "CONFIG_APP_DEPENDENCY",
                    "violation",
                    source,
                    index,
                    f"project configuration depends on application header '{include_path}'",
                )
            if (is_common or is_module) and APP_INCLUDE_RE.search(include_path):
                yield line_finding(
                    "MODULE_TO_APP_DEPENDENCY",
                    "violation",
                    source,
                    index,
                    f"lower layer depends on application header '{include_path}'",
                )
            if (is_app or is_module) and LOCAL_CONFIG_RE.search(line):
                yield line_finding(
                    "SCATTERED_CONFIG",
                    "review",
                    source,
                    index,
                    "implementation layer includes a local config header; verify project parameters stay centralized",
                )

        if is_common and HARDWARE_TYPE_RE.search(line):
            yield line_finding(
                "COMMON_HARDWARE_POLLUTION",
                "violation",
                source,
                index,
                "Common capability layer exposes CubeMX/HAL hardware type",
            )
        if is_config and HARDWARE_TYPE_RE.search(line):
            yield line_finding(
                "CONFIG_HARDWARE_POLLUTION",
                "violation",
                source,
                index,
                "project configuration exposes CubeMX/HAL hardware resource type",
            )
        if is_app and CONCRETE_CAST_RE.search(line):
            yield line_finding(
                "APP_CONCRETE_CAST",
                "violation",
                source,
                index,
                "business application casts an abstract pointer to a concrete implementation type",
            )
        if (is_app or is_module) and BOARD_BINDING_RE.search(line):
            yield line_finding(
                "BOARD_BINDING_LOCATION",
                "review",
                source,
                index,
                "possible board-resource binding outside dedicated Board/board layer",
            )
        if DYNAMIC_MEMORY_RE.search(line):
            yield line_finding(
                "DYNAMIC_MEMORY",
                "violation",
                source,
                index,
                "dynamic memory use is forbidden unless explicitly designed with bounded behavior",
            )
        if (is_app or is_module) and SCATTERED_CONFIG_RE.search(line):
            yield line_finding(
                "SCATTERED_CONFIG",
                "review",
                source,
                index,
                "possible project-tunable parameter outside centralized Config/config layer",
            )
        if (is_app or is_module or is_core) and RTOS_DELAY_RE.search(line):
            yield line_finding(
                "RTOS_DELAY_REVIEW",
                "review",
                source,
                index,
                "osDelay use requires review for synchronization versus periodic pacing",
            )
        if (is_app or is_module or is_core or is_board) and WATCHDOG_RE.search(line):
            yield line_finding(
                "WATCHDOG_REVIEW",
                "review",
                source,
                index,
                "watchdog ownership and refresh policy require review",
            )

    if is_app or is_module or is_core:
        yield from callback_length_findings(source)


def callback_length_findings(source: SourceFile) -> Iterator[Finding]:
    for start, line in enumerate(source.code_lines):
        if not CALLBACK_DECL_RE.search(line):
            continue
        depth = 0
        seen_body = False
        for end in range(start, len(source.code_lines)):
            depth += source.code_lines[end].count("{")
            if depth > 0:
                seen_body = True
            depth -= source.code_lines[end].count("}")
            if seen_body and depth == 0:
                length = end - start + 1
                if length > 40:
                    yield line_finding(
                        "CALLBACK_LENGTH_REVIEW",
                        "review",
                        source,
                        start,
                        f"ISR/callback body is {length} lines; keep callbacks minimal and deterministic",
                    )
                break


def parse_allow(values: Sequence[str]) -> list[tuple[str, str]]:
    allow: list[tuple[str, str]] = []
    for value in values:
        if ":" not in value:
            raise argparse.ArgumentTypeError(f"--allow must use RULE_ID:<glob>, got '{value}'")
        rule_id, pattern = value.split(":", 1)
        if not rule_id or not pattern:
            raise argparse.ArgumentTypeError(f"--allow must use RULE_ID:<glob>, got '{value}'")
        allow.append((rule_id, normalize_rel(pattern.lstrip("./"))))
    return allow


def is_allowed(finding: Finding, allow: Sequence[tuple[str, str]]) -> bool:
    path = normalize_rel(finding.path)
    for rule_id, pattern in allow:
        if finding.rule_id == rule_id and fnmatch.fnmatchcase(path, pattern):
            return True
    return False


def scan(root: Path, include_core: bool, allow: Sequence[tuple[str, str]]) -> tuple[list[str], list[Finding]]:
    root = root.resolve()
    scan_roots = existing_scan_roots(root, include_core)
    findings: list[Finding] = []
    for source in source_files(root, scan_roots):
        for finding in scan_file(source):
            if not is_allowed(finding, allow):
                findings.append(finding)
    scanned = [normalize_rel(path.relative_to(root)) for path in scan_roots]
    return scanned, sorted(findings, key=lambda item: (item.path, item.line, item.rule_id))


def counts(findings: Iterable[Finding]) -> dict[str, int]:
    result = {"violation": 0, "review": 0}
    for finding in findings:
        result[finding.severity] = result.get(finding.severity, 0) + 1
    return result


def exit_code(findings: Sequence[Finding], strict_review: bool) -> int:
    summary = counts(findings)
    if summary.get("violation", 0) > 0:
        return 1
    if strict_review and summary.get("review", 0) > 0:
        return 1
    return 0


def print_text(scanned: Sequence[str], findings: Sequence[Finding], strict_review: bool) -> None:
    summary = counts(findings)
    print(f"Scanned paths: {', '.join(scanned) if scanned else '(none found)'}")
    print(f"Findings: {summary.get('violation', 0)} violation(s), {summary.get('review', 0)} review item(s)")
    if strict_review:
        print("Strict review: enabled")
    if not findings:
        print("No layer dependency findings.")
        return
    for finding in findings:
        print(f"{finding.path}:{finding.line}: {finding.rule_id} [{finding.severity}] {finding.message}")
        if finding.excerpt:
            print(f"  {finding.excerpt}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check CubeMX implementation layer dependency boundaries.",
    )
    parser.add_argument("--root", default=".", help="CubeMX project root to scan. Defaults to current directory.")
    parser.add_argument(
        "--include-core",
        action="store_true",
        help="Also scan Core/Src and Core/Inc CubeMX user integration points.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    parser.add_argument(
        "--strict-review",
        action="store_true",
        help="Exit nonzero when review findings are present, even if there are no violations.",
    )
    parser.add_argument(
        "--allow",
        action="append",
        default=[],
        metavar="RULE_ID:GLOB",
        help="Suppress findings for a rule and relative path glob. May be repeated.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        allow = parse_allow(args.allow)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    root = Path(args.root)
    scanned, findings = scan(root, args.include_core, allow)
    if args.format == "json":
        print(
            json.dumps(
                {
                    "root": str(root.resolve()),
                    "strict_review": args.strict_review,
                    "scanned_paths": scanned,
                    "counts": counts(findings),
                    "findings": [asdict(finding) for finding in findings],
                },
                indent=2,
            )
        )
    else:
        print_text(scanned, findings, args.strict_review)
    return exit_code(findings, args.strict_review)


if __name__ == "__main__":
    sys.exit(main())
