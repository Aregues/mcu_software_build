from __future__ import annotations

import argparse
import json
import re
import statistics
from dataclasses import dataclass
from pathlib import Path

import fitz


TOP_EDGE_RATIO = 0.12
BOTTOM_EDGE_RATIO = 0.12
REPEATED_LINE_MIN_RATIO = 0.6
HEADING_SCALE = 1.28
PARAGRAPH_GAP_RATIO = 0.9
HEADING_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)*$")
LIST_RE = re.compile(r"^(?:[-*•●◆■]\s*|(?:\d+|[A-Za-z])[.)]\s+|\d+、\s*)")
PAGE_NO_RE = re.compile(r"^-?\s*\d+\s*-?$")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODULES_DIR = PROJECT_ROOT / "docs" / "Module"
LEGACY_MODULE_DIR_NAMES = {"pdf", "image", "images", "markdown"}
DEFAULT_SOURCE_DIR = DEFAULT_MODULES_DIR / "pdf"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "Module" / "markdown"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


@dataclass(frozen=True)
class TextLine:
    text: str
    bbox: tuple[float, float, float, float]
    font_size: float
    is_bold: bool


@dataclass(frozen=True)
class LayoutElement:
    kind: str
    bbox: tuple[float, float, float, float]
    lines: list[TextLine]
    rows: list[list[str]] | None = None


@dataclass(frozen=True)
class PageLayout:
    number: int
    elements: list[LayoutElement]
    image_only: bool
    width: float
    height: float


def normalize_text(text: str) -> str:
    normalized = text.replace("\x00", "")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = re.sub(r"\d+", "#", normalized)
    return normalized.lower()


def clean_inline_text(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def clean_table_cell(text: str) -> str:
    raw_lines = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    parts: list[str] = []
    for raw_line in raw_lines:
        line = clean_inline_text(raw_line)
        if not line or re.fullmatch(r"_+", line):
            continue
        parts.append(line)

    text = " ".join(parts)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\bV\s+(BAT|SSA|SSA|SS|DDA|DD|REF[+-]?)\b", r"V\1", text)
    text = re.sub(r"\bOSC32\s+(IN|OUT)\b", r"OSC32 \1", text)
    text = re.sub(r"\s+([,;:)\]])", r"\1", text)
    text = re.sub(r"([(/[])\s+", r"\1", text)
    return text


def bbox_intersects(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return not (ax1 <= bx0 or bx1 <= ax0 or ay1 <= by0 or by1 <= ay0)


def bbox_union(boxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def table_to_rows(table: fitz.table.Table) -> list[list[str]]:
    rows = table.extract() or []
    cleaned: list[list[str]] = []
    for row in rows:
        cleaned_row = [clean_table_cell(cell or "") for cell in row]
        if any(cell for cell in cleaned_row):
            cleaned.append(cleaned_row)
    return cleaned


def extract_text_lines(block: dict) -> list[TextLine]:
    lines: list[TextLine] = []
    for line in block.get("lines", []):
        spans = line.get("spans", [])
        parts: list[str] = []
        sizes: list[float] = []
        is_bold = False
        for span in spans:
            text = clean_inline_text(span.get("text", ""))
            if not text:
                continue
            parts.append(text)
            sizes.append(float(span.get("size", 0.0)))
            flags = int(span.get("flags", 0))
            font_name = str(span.get("font", ""))
            if flags & 16 or "bold" in font_name.lower():
                is_bold = True

        text = " ".join(parts).strip()
        if not text:
            continue

        line_bbox = tuple(float(v) for v in line.get("bbox", block.get("bbox")))
        font_size = max(sizes) if sizes else 0.0
        lines.append(TextLine(text=text, bbox=line_bbox, font_size=font_size, is_bold=is_bold))
    return lines


def extract_page_layout(page: fitz.Page) -> PageLayout:
    table_finder = page.find_tables()
    table_elements: list[LayoutElement] = []
    table_boxes: list[tuple[float, float, float, float]] = []
    for table in table_finder.tables:
        rows = table_to_rows(table)
        if not rows:
            continue
        bbox = tuple(float(v) for v in table.bbox)
        table_elements.append(LayoutElement(kind="table", bbox=bbox, lines=[], rows=rows))
        table_boxes.append(bbox)

    elements = list(table_elements)
    data = page.get_text("dict")
    text_block_count = 0
    image_block_count = 0

    for block in data.get("blocks", []):
        block_type = block.get("type")
        bbox = tuple(float(v) for v in block.get("bbox", (0, 0, 0, 0)))
        if block_type == 1:
            image_block_count += 1
            elements.append(LayoutElement(kind="image", bbox=bbox, lines=[], rows=None))
            continue
        if block_type != 0:
            continue
        if any(bbox_intersects(bbox, table_box) for table_box in table_boxes):
            continue

        lines = extract_text_lines(block)
        if not lines:
            continue
        text_block_count += 1
        elements.append(LayoutElement(kind="text", bbox=bbox, lines=lines))

    return PageLayout(
        number=page.number + 1,
        elements=elements,
        image_only=text_block_count == 0 and image_block_count > 0,
        width=float(page.rect.width),
        height=float(page.rect.height),
    )


def detect_repeated_edges(pages: list[PageLayout]) -> tuple[set[str], set[str]]:
    if len(pages) < 2:
        return set(), set()

    header_counts: dict[str, int] = {}
    footer_counts: dict[str, int] = {}
    threshold = max(2, int(len(pages) * REPEATED_LINE_MIN_RATIO + 0.999))

    for page in pages:
        header_seen: set[str] = set()
        footer_seen: set[str] = set()
        top_limit = page.height * TOP_EDGE_RATIO
        bottom_limit = page.height * (1 - BOTTOM_EDGE_RATIO)

        for element in page.elements:
            if element.kind != "text":
                continue
            for line in element.lines:
                normalized = normalize_text(line.text)
                if not normalized:
                    continue
                if line.bbox[1] <= top_limit:
                    header_seen.add(normalized)
                if line.bbox[3] >= bottom_limit:
                    footer_seen.add(normalized)

        for item in header_seen:
            header_counts[item] = header_counts.get(item, 0) + 1
        for item in footer_seen:
            footer_counts[item] = footer_counts.get(item, 0) + 1

    repeated_headers = {item for item, count in header_counts.items() if count >= threshold}
    repeated_footers = {
        item
        for item, count in footer_counts.items()
        if count >= threshold or PAGE_NO_RE.fullmatch(item.replace("#", "1"))
    }
    return repeated_headers, repeated_footers


def filter_page_edges(
    page: PageLayout,
    repeated_headers: set[str],
    repeated_footers: set[str],
) -> PageLayout:
    top_limit = page.height * TOP_EDGE_RATIO
    bottom_limit = page.height * (1 - BOTTOM_EDGE_RATIO)
    filtered: list[LayoutElement] = []

    for element in page.elements:
        if element.kind != "text":
            filtered.append(element)
            continue

        kept_lines: list[TextLine] = []
        for line in element.lines:
            normalized = normalize_text(line.text)
            is_header = line.bbox[1] <= top_limit and normalized in repeated_headers
            is_footer = line.bbox[3] >= bottom_limit and normalized in repeated_footers
            page_no_like = line.bbox[3] >= bottom_limit and PAGE_NO_RE.fullmatch(clean_inline_text(line.text))
            if is_header or is_footer or page_no_like:
                continue
            kept_lines.append(line)

        if kept_lines:
            filtered.append(
                LayoutElement(
                    kind="text",
                    bbox=bbox_union([line.bbox for line in kept_lines]),
                    lines=kept_lines,
                )
            )

    return PageLayout(
        number=page.number,
        elements=filtered,
        image_only=page.image_only,
        width=page.width,
        height=page.height,
    )


def median_body_font(pages: list[PageLayout]) -> float:
    sizes: list[float] = []
    for page in pages:
        for element in page.elements:
            if element.kind != "text":
                continue
            for line in element.lines:
                if line.text:
                    sizes.append(line.font_size)
    if not sizes:
        return 12.0
    return statistics.median(sizes)


def classify_block(element: LayoutElement, body_font: float) -> str:
    if element.kind != "text":
        return element.kind

    texts = [line.text for line in element.lines if line.text]
    if not texts:
        return "paragraph"

    if len(texts) == 1:
        text = texts[0]
        max_size = max(line.font_size for line in element.lines)
        short_text = len(text) <= 40
        numbered_title = re.match(r"^\d+(?:\.\d+)*\s+\S+", text) and "：" not in text and ":" not in text
        if (
            (max_size >= body_font * HEADING_SCALE and short_text)
            or HEADING_NUMBER_RE.fullmatch(text)
            or numbered_title
        ):
            return "heading"

    if (
        len(texts) == 2
        and HEADING_NUMBER_RE.fullmatch(texts[0])
        and len(texts[1]) <= 40
        and all("：" not in text and ":" not in text for text in texts)
    ):
        return "heading"

    if all(LIST_RE.match(text) for text in texts):
        return "list"
    return "paragraph"


def merge_lines_to_block(element: LayoutElement, body_font: float) -> LayoutElement:
    if element.kind != "text":
        return element

    block_type = classify_block(element, body_font)
    if block_type == "heading":
        heading_text = " ".join(line.text for line in element.lines if line.text).strip()
        line = element.lines[0]
        return LayoutElement(
            kind="heading",
            bbox=element.bbox,
            lines=[
                TextLine(
                    heading_text,
                    line.bbox,
                    max(l.font_size for l in element.lines),
                    any(l.is_bold for l in element.lines),
                )
            ],
        )

    grouped: list[str] = []
    current = ""
    previous: TextLine | None = None

    for line in element.lines:
        text = line.text.strip()
        if not text:
            continue

        if previous is None:
            current = text
            previous = line
            continue

        gap = line.bbox[1] - previous.bbox[3]
        same_indent = abs(line.bbox[0] - previous.bbox[0]) <= max(body_font * 0.8, 8.0)
        continuation = not LIST_RE.match(text) and not current.endswith(("。", "；", "：", "?", "？", "!", "！"))
        if gap <= body_font * PARAGRAPH_GAP_RATIO and same_indent and continuation:
            current = f"{current} {text}"
        else:
            grouped.append(current)
            current = text
        previous = line

    if current:
        grouped.append(current)

    kind = "list" if block_type == "list" else "paragraph"
    merged_lines = [TextLine(text=item, bbox=element.bbox, font_size=body_font, is_bold=False) for item in grouped]
    return LayoutElement(kind=kind, bbox=element.bbox, lines=merged_lines)


def reconstruct_blocks(page: PageLayout, body_font: float) -> list[LayoutElement]:
    ordered = sorted(page.elements, key=lambda element: (round(element.bbox[1], 1), round(element.bbox[0], 1)))
    reconstructed: list[LayoutElement] = []
    carry: LayoutElement | None = None

    for raw in ordered:
        element = merge_lines_to_block(raw, body_font)
        if element.kind != "paragraph":
            if carry:
                reconstructed.append(carry)
                carry = None
            reconstructed.append(element)
            continue

        if carry is None:
            carry = element
            continue

        gap = element.bbox[1] - carry.bbox[3]
        same_indent = abs(element.bbox[0] - carry.bbox[0]) <= max(body_font * 0.8, 8.0)
        if gap <= body_font * 1.2 and same_indent:
            carry = LayoutElement(
                kind="paragraph",
                bbox=bbox_union([carry.bbox, element.bbox]),
                lines=carry.lines + element.lines,
            )
        else:
            reconstructed.append(carry)
            carry = element

    if carry:
        reconstructed.append(carry)
    return reconstructed


def heading_level(text: str) -> int:
    match = re.match(r"^(\d+(?:\.\d+)*)", text)
    if not match:
        return 2
    return min(6, match.group(1).count(".") + 2)


def render_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    col_count = max(len(row) for row in rows)
    normalized = [row + [""] * (col_count - len(row)) for row in rows]
    header = normalized[0]
    divider = ["---"] * col_count
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(divider) + " |",
    ]
    for row in normalized[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_markdown(
    pdf_path: Path,
    pages: list[PageLayout],
    keep_page_breaks: bool = False,
    debug_layout: bool = False,
    include_page_headings: bool = True,
) -> str:
    body_font = median_body_font(pages)
    parts: list[str] = [f"# {pdf_path.stem}"]
    debug_payload: list[dict[str, object]] = []

    for page in pages:
        elements = reconstruct_blocks(page, body_font)
        if keep_page_breaks and len(parts) > 1:
            parts.append("\n---\n")

        if include_page_headings:
            parts.append(f"## 第 {page.number} 页")

        if page.image_only:
            parts.append(f"_第 {page.number} 页主要为图片，建议 OCR 处理。_")
            continue

        page_parts: list[str] = []
        for element in elements:
            if element.kind == "heading":
                text = element.lines[0].text.strip()
                if text:
                    page_parts.append(f"{'#' * heading_level(text)} {text}")
            elif element.kind == "paragraph":
                paragraph = "\n".join(line.text for line in element.lines if line.text).strip()
                if paragraph:
                    page_parts.append(paragraph)
            elif element.kind == "list":
                for line in element.lines:
                    item = LIST_RE.sub("", line.text).strip()
                    if item:
                        page_parts.append(f"- {item}")
            elif element.kind == "table" and element.rows:
                table_block = render_table(element.rows)
                if table_block:
                    page_parts.append(table_block)

        parts.extend(page_parts or ["_本页未提取到可见文本_"])

        if debug_layout:
            debug_payload.append(
                {
                    "page": page.number,
                    "image_only": page.image_only,
                    "elements": [
                        {
                            "kind": element.kind,
                            "bbox": [round(v, 2) for v in element.bbox],
                            "text": [line.text for line in element.lines],
                            "rows": element.rows,
                        }
                        for element in elements
                    ],
                }
            )

    markdown = "\n\n".join(part for part in parts if part.strip()).strip() + "\n"
    if debug_layout:
        markdown += "\n<!-- layout-debug\n"
        markdown += json.dumps(debug_payload, ensure_ascii=False, indent=2)
        markdown += "\n-->\n"
    return markdown


def pdf_to_markdown(
    pdf_path: Path,
    keep_page_breaks: bool = False,
    debug_layout: bool = False,
    include_page_headings: bool = True,
) -> str:
    doc = fitz.open(pdf_path)
    pages = [extract_page_layout(page) for page in doc]
    repeated_headers, repeated_footers = detect_repeated_edges(pages)
    filtered_pages = [
        filter_page_edges(page, repeated_headers=repeated_headers, repeated_footers=repeated_footers)
        for page in pages
    ]
    return render_markdown(
        pdf_path=pdf_path,
        pages=filtered_pages,
        keep_page_breaks=keep_page_breaks,
        debug_layout=debug_layout,
        include_page_headings=include_page_headings,
    )


def convert_pdf(
    pdf_path: Path,
    output_path: Path,
    keep_page_breaks: bool = False,
    debug_layout: bool = False,
) -> None:
    markdown = pdf_to_markdown(
        pdf_path,
        keep_page_breaks=keep_page_breaks,
        debug_layout=debug_layout,
    )
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Converted: {pdf_path.name} -> {output_path}")


def path_for_markdown(path: Path, base_dir: Path) -> str:
    try:
        return path.relative_to(base_dir).as_posix()
    except ValueError:
        return path.as_posix()


def image_placeholder_markdown(image_path: Path, module_dir: Path) -> str:
    image_ref = path_for_markdown(image_path, module_dir)
    return "\n".join(
        [
            f"### {image_path.name}",
            "",
            f"来源图片：`{image_ref}`",
            "",
            "待 Codex 视觉识别补充：请查看该图片，并在本节补充仅从图片可确认的硬件事实，"
            "包括模块对外暴露引脚、接口方向、电源端子、电压标注、跳线/焊盘配置和特殊接线注意事项。",
            "",
            "对外引脚优先规则：如果图片可确认的模块外露引脚与 PDF/芯片手册中的芯片裸片引脚冲突，"
            "最终连接文件必须以图片中的模块外露引脚为准；图片无法确认的信息标记为 `unclear`，不得猜测。",
        ]
    )


def module_manual_markdown(
    module_dir: Path,
    keep_page_breaks: bool = False,
    debug_layout: bool = False,
) -> str:
    module_name = module_dir.name
    pdf_paths = sorted(module_dir.rglob("*.pdf"))
    image_paths = sorted(
        path
        for path in module_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )

    sections: list[str] = [
        f"# {module_name} 模块手册汇总",
        "",
        f"来源目录：`{module_dir.as_posix()}`",
        "",
        "## PDF 文本化",
    ]

    if pdf_paths:
        for pdf_path in pdf_paths:
            sections.extend(
                [
                    "",
                    f"## PDF：{path_for_markdown(pdf_path, module_dir)}",
                    "",
                    pdf_to_markdown(
                        pdf_path,
                        keep_page_breaks=keep_page_breaks,
                        debug_layout=debug_layout,
                    ).strip(),
                ]
            )
    else:
        sections.append("\n_未发现 PDF 手册。_")

    sections.append("\n## 图片识别补充")
    if image_paths:
        for image_path in image_paths:
            sections.extend(["", image_placeholder_markdown(image_path, module_dir)])
    else:
        sections.append("\n_未发现图片资料。_")

    return "\n".join(sections).strip() + "\n"


def convert_module_dir(
    module_dir: Path,
    overwrite: bool,
    keep_page_breaks: bool = False,
    debug_layout: bool = False,
) -> bool:
    manual_path = module_dir / "manual.md"
    if manual_path.exists() and not overwrite:
        print(f"Skipped existing: {manual_path}")
        return False

    markdown = module_manual_markdown(
        module_dir,
        keep_page_breaks=keep_page_breaks,
        debug_layout=debug_layout,
    )
    manual_path.write_text(markdown, encoding="utf-8")
    print(f"Converted module: {module_dir.name} -> {manual_path}")
    return True


def iter_module_dirs(modules_dir: Path) -> list[Path]:
    if not modules_dir.is_dir():
        raise SystemExit(f"Modules directory not found: {modules_dir}")

    return [
        path
        for path in sorted(modules_dir.iterdir())
        if path.is_dir() and path.name.lower() not in LEGACY_MODULE_DIR_NAMES
    ]


def convert_modules(
    modules_dir: Path,
    overwrite: bool,
    keep_page_breaks: bool = False,
    debug_layout: bool = False,
) -> int:
    module_dirs = iter_module_dirs(modules_dir)
    if not module_dirs:
        print(f"No module directories found in: {modules_dir}")
        return 0

    converted = 0
    skipped = 0
    for module_dir in module_dirs:
        if convert_module_dir(
            module_dir,
            overwrite,
            keep_page_breaks=keep_page_breaks,
            debug_layout=debug_layout,
        ):
            converted += 1
        else:
            skipped += 1

    print(f"Finished. Converted modules: {converted}, Skipped: {skipped}")
    return converted


def convert_batch(
    source_dir: Path,
    output_dir: Path,
    overwrite: bool,
    keep_page_breaks: bool = False,
    debug_layout: bool = False,
) -> int:
    if not source_dir.is_dir():
        raise SystemExit(f"Source directory not found: {source_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_paths = sorted(source_dir.glob("*.pdf"))
    if not pdf_paths:
        print(f"No PDF files found in: {source_dir}")
        return 0

    converted = 0
    skipped = 0

    for pdf_path in pdf_paths:
        output_path = output_dir / f"{pdf_path.stem}.md"
        if output_path.exists() and not overwrite:
            skipped += 1
            print(f"Skipped existing: {output_path}")
            continue

        convert_pdf(
            pdf_path,
            output_path,
            keep_page_breaks=keep_page_breaks,
            debug_layout=debug_layout,
        )
        converted += 1

    print(f"Finished. Converted: {converted}, Skipped: {skipped}")
    return converted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract module manual PDFs to Markdown and add image-review placeholders."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help=(
            "Optional PDF paths or module directories. If omitted, process module "
            "directories under --modules-dir."
        ),
    )
    parser.add_argument(
        "--modules-dir",
        type=Path,
        default=DEFAULT_MODULES_DIR,
        help="Directory containing docs/Module/<module-name> folders.",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Legacy flat directory containing source PDFs for batch conversion.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Legacy flat directory for generated Markdown files.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite same-name Markdown files instead of skipping them.",
    )
    parser.add_argument(
        "--keep-page-breaks",
        action="store_true",
        help="Keep page separators in the generated Markdown.",
    )
    parser.add_argument(
        "--debug-layout",
        action="store_true",
        help="Append layout debug information as an HTML comment.",
    )
    args = parser.parse_args()

    if args.paths:
        pdf_paths = [path for path in args.paths if path.suffix.lower() == ".pdf"]
        module_paths = [path for path in args.paths if path.suffix.lower() != ".pdf"]

        if pdf_paths:
            output_dir = (args.output_dir or DEFAULT_OUTPUT_DIR).resolve()
            output_dir.mkdir(parents=True, exist_ok=True)
            converted = 0
            skipped = 0

            for pdf_arg in pdf_paths:
                pdf_path = pdf_arg.resolve()
                if not pdf_path.is_file():
                    raise SystemExit(f"PDF not found: {pdf_path}")

                output_path = output_dir / f"{pdf_path.stem}.md"
                if output_path.exists() and not args.overwrite:
                    skipped += 1
                    print(f"Skipped existing: {output_path}")
                    continue

                convert_pdf(
                    pdf_path,
                    output_path,
                    keep_page_breaks=args.keep_page_breaks,
                    debug_layout=args.debug_layout,
                )
                converted += 1

            print(f"Finished PDF paths. Converted: {converted}, Skipped: {skipped}")

        if module_paths:
            converted = 0
            for module_arg in module_paths:
                module_path = module_arg.resolve()
                if not module_path.is_dir():
                    raise SystemExit(f"Module directory not found: {module_path}")
                if convert_module_dir(
                    module_path,
                    args.overwrite,
                    keep_page_breaks=args.keep_page_breaks,
                    debug_layout=args.debug_layout,
                ):
                    converted += 1
            print(f"Finished module paths. Converted modules: {converted}")
        return

    if args.source_dir or args.output_dir:
        source_dir = (args.source_dir or DEFAULT_SOURCE_DIR).resolve()
        output_dir = (args.output_dir or DEFAULT_OUTPUT_DIR).resolve()
        convert_batch(
            source_dir,
            output_dir,
            args.overwrite,
            keep_page_breaks=args.keep_page_breaks,
            debug_layout=args.debug_layout,
        )
        return

    convert_modules(
        args.modules_dir.resolve(),
        args.overwrite,
        keep_page_breaks=args.keep_page_breaks,
        debug_layout=args.debug_layout,
    )


if __name__ == "__main__":
    main()
