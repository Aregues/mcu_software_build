---
name: hardware-interface-writer
description: Guide MCU hardware interface feasibility analysis and hardware connection file writing. Use when Codex needs to confirm a requirement document, collect an MCU pin definition table or pinout diagram, collect module manuals organized under docs/Module/module-name folders with PDFs and images, convert manuals to Markdown, extract image-confirmed exposed module pins, analyze module and MCU peripheral sufficiency, and write a hardware_interface-style connection JSON when the design is feasible.
---

# Hardware Interface Writer

Use this skill to turn a requirement document, MCU pin information, and module manuals into a feasibility decision and a hardware connection file.

## Required Inputs

- Requirement document: confirm the exact file first. If the user has not identified one, ask them to upload or choose it before analysis.
- MCU pin definition table: always request it. Treat this as required for final pin allocation.
- MCU pinout diagram: request it when the pin table does not include multiplexing, package pins, power pins, or alternate functions clearly enough.
- Module manuals: request module folders under `docs\Module\<模块名>` for modules that implement required functions. Each module folder may contain PDFs and images. Do not require manuals for basic parts such as buttons, LEDs, simple resistors, or generic pull-ups unless the user asks for them.

## Workflow

1. Confirm the requirement document and extract the required hardware-facing functions: sensors, communication links, displays, actuators, buttons, debug interfaces, power rails, voltage constraints, and quantity requirements.
2. Ask for the MCU pin definition table if it is missing. If the requirement-to-pin analysis depends on unavailable pin information, stop and request it instead of guessing.
3. Ask for module manuals for non-basic modules needed by the requirement. Prefer `docs\Module\<模块名>\` folders containing all related PDFs and images. Keep a short intake table with module name, required function, provided files, and status. Legacy flat folders `docs\Module\pdf`, `docs\Module\image`, and `docs\Module\markdown` may exist, but prefer the module-folder layout when both are present.
4. Perform a shallow sufficiency check before conversion:
   - Mark a module `likely sufficient` only if its name or visible metadata clearly matches the required function.
   - Mark it `unclear` when the interface, voltage, range, channel count, or protocol cannot be confirmed yet.
   - Mark it `insufficient` when the visible information already conflicts with the requirement.
5. Convert module manuals to Markdown with the bundled script. Do not call or depend on any external PDF-conversion skill. In the preferred layout, the script writes `docs\Module\<模块名>\manual.md`, textifies PDFs first, and appends image-review placeholders.

   The script requires `PyMuPDF`. Install it once before first use:

   ```powershell
   pip install pymupdf
   ```

```powershell
python "<skill_dir>\scripts\pdf_to_md.py" --modules-dir ".\docs\Module"
```

For a specific module folder:

```powershell
python "<skill_dir>\scripts\pdf_to_md.py" ".\docs\Module\INA219"
```

For legacy flat PDF folders only:

```powershell
python "<skill_dir>\scripts\pdf_to_md.py" --source-dir ".\docs\Module\pdf" --output-dir ".\docs\Module\markdown"
```

6. Review each image referenced in `manual.md` and fill the image-review placeholder with only image-confirmed hardware facts: exposed module pins, terminal labels, connector direction, voltage labels, jumper/solder-pad settings, and special wiring notes. If a PDF chip manual and a module image disagree, use the image-confirmed module-exposed pins in the connection file. Mark anything unreadable or not visible as `unclear`; do not guess or substitute bare IC pins for module connector pins.
7. Deep-analyze the converted Markdown manuals. For each module, extract only hardware-relevant facts: supply voltage, logic level, interface type, exposed module pin names, signal direction, required pull-ups or level shifting, UART/I2C/SPI parameters, channel counts, timing constraints, and special electrical notes.
8. Analyze MCU feasibility from the converted manuals and MCU pin definition table:
   - Check whether required peripherals are available in sufficient count: GPIO, EXTI, ADC, DAC, PWM, timers, UART/USART, I2C, SPI, CAN, USB, and any project-specific interface.
   - Check whether chosen MCU pins can legally provide the required alternate functions.
   - Check whether any pin is double-booked, reserved for boot/debug/oscillator/reset, or unavailable in the package.
   - Check whether voltage levels and power rails are compatible or need level shifting/regulation.
   - Record assumptions instead of silently filling gaps.
9. If feasible, read `references/hardware_interface_spec.md` and write the hardware connection file in that schema. Use the fixed output path `docs\Hardware\<项目名称>-<YY-MM-DD>.json`, where `<项目名称>` comes from the requirement document or the `project` field and `<YY-MM-DD>` uses the current local date. Create `docs\Hardware` when it does not exist. Inspect any same-name existing file before overwriting it.
10. If not feasible, do not write the connection file unless the user explicitly requests a partial draft. Report the blocking issues and the specific data or hardware change needed to proceed.

## Output Expectations

When reporting results, include:

- Requirement document used.
- Inputs still missing, if any.
- Module sufficiency summary with `likely sufficient`, `unclear`, or `insufficient`.
- Manual files used, including module `manual.md` files and any image-confirmed exposed pin overrides.
- MCU pin/peripheral allocation table when enough pin data is available.
- Feasibility decision: `feasible`, `feasible with assumptions`, or `not feasible`.
- Created or updated hardware connection file path when a file was written.

## Hardware Connection Rules

Before writing the connection JSON, load `references/hardware_interface_spec.md`.

Use these additional rules:

- Include every referenced device in `devices` before using it in `connections` or `power_connections`.
- For any device backed by a folder under `docs\Module\<模块名>`, use the exact folder name `<模块名>` as the device name in `devices`, `connections`, and `power_connections`. Do not rename it with extra descriptive suffixes or marketing labels.
- Keep signal names globally consistent.
- Write signal connections separately from power connections.
- Prefer symmetric signal entries for both sides of a connection.
- Put non-default electrical requirements in `notes`, such as pull-up resistors, voltage dividers, level shifters, boot-pin cautions, or shared-bus address constraints.
- Use image-confirmed module-exposed pins when they differ from bare IC pins in a PDF. Record the source image and unresolved pin uncertainty in `notes`.
- For any MCU or MCU board device, treat board-level power outputs such as `<MCU设备名>:3V3_OUT` and `<MCU设备名>:5V_OUT` as ordinary pins when the board exposes them. If such a power output is used, include it in both `connections` and `power_connections`.
