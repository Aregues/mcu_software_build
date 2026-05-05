---
name: hardware-interface-writer
description: Guide MCU hardware interface feasibility analysis and hardware connection file writing. Use when Codex needs to confirm a release requirements document, locate the target STM32 MCU model, fetch the matching STMicroelectronics STM32_open_pin_data XML under docs/mcu, collect module manuals organized under docs/modules/module-name folders with PDFs and images, convert supplemental PDF module/manual sources to Markdown, extract image-confirmed exposed module pins, analyze module and MCU peripheral sufficiency, and write docs/releases/VERSION/hardware.json when the design is feasible.
---

# Hardware Interface Writer

Use this skill to turn a requirement document, ST MCU XML pin data, and module manuals into a feasibility decision and a hardware connection file.

## Release Document Layout

Use the single-project release layout:

```text
docs/releases/<version>/
  requirements.md
  hardware.json
  software_design.md
  cubemx_build.md
  notes.md
```

If the user names a release version, use that version exactly after sanitizing it to a directory-safe name such as `v1.0`. If the user does not name a version, use the newest semantic version under `docs/releases`. If no release exists, create `docs/releases/v0.1`.

## Required Inputs

- Requirement document: confirm the active release first and use `docs/releases/<version>/requirements.md`. If the user has not identified a release and multiple releases exist, choose the newest semantic version unless the user asks for another one.
- STM32 MCU model: extract the complete ordering code from `requirements.md` or the user's input, for example `STM32F103C8T6`. The model must be specific enough to determine package, memory/capacity, and ordering suffix.
- ST MCU XML: use the bundled `scripts\fetch_stm32_pin_xml.py` first. It matches the complete STM32 ordering code against a built-in list of official `STM32_open_pin_data/mcu` XML filenames, downloads the unique match to `docs\mcu\`, and writes a sibling `.source.json` trace file. If it returns candidates instead of downloading, rerun it with a more specific ordering code.
- MCU source trace: record the source repository URL, download date, matched XML filename, and `.source.json` path in the report and in project notes when notes are being updated.
- Supplemental MCU PDFs or images: request them only when the ST repository has no matching XML, the MCU model is incomplete or ambiguous, the package suffix cannot be determined, or the user explicitly provides supplemental datasheets/pinout images.
- Module manuals: request module folders under `docs\modules\<module-name>` for modules that implement required functions. Each module folder may contain PDFs and images. Do not require manuals for basic parts such as buttons, LEDs, simple resistors, or generic pull-ups unless the user asks for them.

## Workflow

1. Confirm the requirement document and extract the required hardware-facing functions: sensors, communication links, displays, actuators, buttons, debug interfaces, power rails, voltage constraints, and quantity requirements.
2. Locate the target STM32 MCU model and fetch the ST XML:
   - Extract a complete MCU ordering code from `requirements.md` or the user request, such as `STM32F103C8T6`.
   - Run the bundled fetch script from the repository root:

```powershell
python ".\skills\hardware-interface-writer\scripts\fetch_stm32_pin_xml.py" STM32F103C8T6 --output-dir ".\docs\mcu"
```

   - The script treats ST filename `x` characters as single-character wildcards and grouped fields such as `(8-B)` or `(C-E)` as ordering-code character ranges. For `STM32F103C8T6`, the expected unique match is `STM32F103C(8-B)Tx.xml`.
   - If the XML already exists, the script leaves it in place unless `--force` is supplied. Use `--dry-run` to verify matching without writing files, and `--json` when another tool needs structured output.
   - If the input is incomplete or ambiguous, the script prints the top candidates and exits non-zero instead of choosing one. Stop and request the missing package/capacity/suffix or rerun with a more precise ordering code.
   - Record the raw source URL, download date, matched XML filename, and `docs\mcu\<xml-file>.source.json` path in the output report and any release notes you update.
   - If no ST XML exists after a precise ordering code is provided, request supplemental datasheet/pinout source instead of guessing.
3. Ask for module manuals for non-basic modules needed by the requirement. Prefer `docs\modules\<module-name>\` folders containing all related PDFs and images. Keep a short intake table with module name, required function, provided files, and status. Legacy flat folders such as `docs\modules\pdf`, `docs\modules\image`, and `docs\modules\markdown` may exist, but prefer the module-folder layout when both are present.
4. Perform a shallow sufficiency check before conversion:
   - Mark a module `likely sufficient` only if its name or visible metadata clearly matches the required function.
   - Mark it `unclear` when the interface, voltage, range, channel count, or protocol cannot be confirmed yet.
   - Mark it `insufficient` when the visible information already conflicts with the requirement.
5. Convert supplemental PDFs to Markdown with the bundled script. This is required for module manuals provided as PDFs and optional for supplemental MCU datasheets/pinout PDFs; it does not replace the ST XML default source. Do not call or depend on any external PDF-conversion skill. In the preferred module layout, the script writes `docs\modules\<module-name>\manual.md`, textifies PDFs first, and appends image-review placeholders.

   The script requires `PyMuPDF`. Install it once before first use:

   ```powershell
   pip install pymupdf
   ```

```powershell
python "<skill_dir>\scripts\pdf_to_md.py" --modules-dir ".\docs\modules"
```

If the user provides a supplemental MCU PDF, convert it to Markdown as supporting evidence only:

```powershell
python "<skill_dir>\scripts\pdf_to_md.py" ".\docs\mcu\supplemental_pinout.pdf" --output-dir ".\docs\mcu\markdown"
```

For a specific module folder:

```powershell
python "<skill_dir>\scripts\pdf_to_md.py" ".\docs\modules\INA219"
```

For legacy flat PDF folders only:

```powershell
python "<skill_dir>\scripts\pdf_to_md.py" --source-dir ".\docs\modules\pdf" --output-dir ".\docs\modules\markdown"
```

6. Review each image referenced in `manual.md` and fill the image-review placeholder with only image-confirmed hardware facts: exposed module pins, terminal labels, connector direction, voltage labels, jumper/solder-pad settings, and special wiring notes. If a PDF chip manual and a module image disagree, use the image-confirmed module-exposed pins in the connection file. Mark anything unreadable or not visible as `unclear`; do not guess or substitute bare IC pins for module connector pins.
7. Deep-analyze the converted Markdown manuals. For each module, extract only hardware-relevant facts: supply voltage, logic level, interface type, exposed module pin names, signal direction, required pull-ups or level shifting, UART/I2C/SPI parameters, channel counts, timing constraints, and special electrical notes.
8. Analyze MCU feasibility directly from `docs\mcu\*.xml` plus the converted module manuals:
   - Check whether required peripherals are available in sufficient count: GPIO, EXTI, ADC, DAC, PWM, timers, UART/USART, I2C, SPI, CAN, USB, and any project-specific interface.
   - Check whether chosen MCU pins can legally provide the required alternate functions.
   - Check whether any pin is double-booked, reserved for boot/debug/oscillator/reset, or unavailable in the package.
   - Check package-specific pin availability, power pins, reset/boot/debug pins, and reserved pins from the XML before assigning functions.
   - Check whether voltage levels and power rails are compatible or need level shifting/regulation.
   - Use supplemental MCU PDF/image information only to resolve gaps or conflicts; record when it differs from the ST XML.
   - Record assumptions instead of silently filling gaps.
9. If feasible, read `references/hardware_interface_spec.md` and write the hardware connection file in that schema. Use the fixed output path `docs\releases\<version>\hardware.json`. Create `docs\releases\<version>` when it does not exist. Inspect any existing `hardware.json` before overwriting it.
10. If not feasible, do not write the connection file unless the user explicitly requests a partial draft. Report the blocking issues and the specific data or hardware change needed to proceed.

## Output Expectations

When reporting results, include:

- Requirement document used.
- Inputs still missing, if any.
- Module sufficiency summary with `likely sufficient`, `unclear`, or `insufficient`.
- Manual files used, including module `manual.md` files and any image-confirmed exposed pin overrides.
- ST MCU XML files used, including source URL, download date, and matched XML filename.
- Supplemental MCU PDF/Image/Markdown files used, if any.
- MCU pin/peripheral allocation table when enough pin data is available.
- Feasibility decision: `feasible`, `feasible with assumptions`, or `not feasible`.
- Created or updated hardware connection file path when a file was written.

## Hardware Connection Rules

Before writing the connection JSON, load `references/hardware_interface_spec.md`.

Use these additional rules:

- Include every referenced device in `devices` before using it in `connections` or `power_connections`.
- For any device backed by a folder under `docs\modules\<module-name>`, use the exact folder name `<module-name>` as the device name in `devices`, `connections`, and `power_connections`. Do not rename it with extra descriptive suffixes or marketing labels.
- Keep signal names globally consistent.
- Write signal connections separately from power connections.
- Prefer symmetric signal entries for both sides of a connection.
- Put non-default electrical requirements in `notes`, such as pull-up resistors, voltage dividers, level shifters, boot-pin cautions, or shared-bus address constraints.
- Use image-confirmed module-exposed pins when they differ from bare IC pins in a PDF. Record the source image and unresolved pin uncertainty in `notes`.
- For any MCU or MCU board device, treat board-level power outputs such as `<MCU设备名>:3V3_OUT` and `<MCU设备名>:5V_OUT` as ordinary pins when the board exposes them. If such a power output is used, include it in both `connections` and `power_connections`.
