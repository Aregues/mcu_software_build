# mcu-software-build

End-to-end MCU embedded software development plugin for Claude Code.

Covers the full lifecycle from requirements gathering to on-target debugging, designed for STM32 / ARM Cortex-M projects using STM32CubeMX.

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| requirements-doc-filling | `/requirements-doc-filling` | Interactively collect project requirements and generate a structured SRS document |
| hardware-interface-writer | `/hardware-interface-writer` | Analyze MCU pins, module manuals, and write hardware connection JSON |
| software-design-doc-writer | `/software-design-doc-writer` | Auto-generate a software design document from requirements + hardware connection |
| cubemx-framework-guide | `/cubemx-framework-guide` | Generate a step-by-step CubeMX setup guide, then verify the generated framework |
| cubemx-code-implementation | `/cubemx-code-implementation` | Implement full application code on top of a CubeMX-generated project skeleton |
| embedded-gdb-openocd-debug | `/embedded-gdb-openocd-debug` | Debug STM32 firmware with OpenOCD + arm-none-eabi-gdb |

## Recommended Workflow

```
1. /requirements-doc-filling    → docs/releases/<version>/requirements.md
2. /hardware-interface-writer   → docs/releases/<version>/hardware.json
3. /software-design-doc-writer  → docs/releases/<version>/software_design.md
4. /cubemx-framework-guide      → docs/releases/<version>/cubemx_build.md → user generates in CubeMX → review
5. /cubemx-code-implementation  → app/ + Module/ code on CubeMX skeleton
6. /embedded-gdb-openocd-debug  → on-target debug session
```

## Project Document Layout

This plugin assumes a single repository serves one MCU project. Project deliverables are versioned as release snapshots:

```
docs/
├── releases/
│   ├── v0.1/
│   │   ├── requirements.md
│   │   ├── hardware.json
│   │   ├── software_design.md
│   │   ├── cubemx_build.md
│   │   └── notes.md
│   └── v1.0/
│       ├── requirements.md
│       ├── hardware.json
│       ├── software_design.md
│       ├── cubemx_build.md
│       └── notes.md
├── modules/
│   └── <module-name>/
│       ├── manual.md
│       └── source files such as PDFs or images
└── mcu/
    └── pin-definition source files and converted markdown
```

When no version is specified, skills use the newest semantic version under `docs/releases`; if none exists, they create `docs/releases/v0.1`.

## Installation

Add this plugin to your Claude Code project by placing the `mcu_software_build` folder under your workspace, or install via:

```bash
claude plugin add /path/to/mcu_software_build
```

## Project Structure

```
mcu_software_build/
├── plugin.json                          # Plugin manifest
├── README.md
├── requirements-doc-filling/            # Skill 1: Requirements gathering
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   └── references/
├── hardware-interface-writer/           # Skill 2: Hardware interface analysis
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/
│   └── scripts/pdf_to_md.py
├── software-design-doc-writer/          # Skill 3: Software design document
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   └── references/
├── cubemx-framework-guide/              # Skill 4: CubeMX setup guide
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   └── references/
├── cubemx-code-implementation/          # Skill 5: Code implementation
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   └── references/
└── embedded-gdb-openocd-debug/          # Skill 6: GDB/OpenOCD debug
    ├── SKILL.md
    ├── agents/openai.yaml
    └── references/
```

## Requirements

- Python 3 (for `pdf_to_md.py` in hardware-interface-writer)
- ARM GCC toolchain (`arm-none-eabi-gcc`) for build verification
- OpenOCD + ST-Link for on-target debugging
- STM32CubeMX for framework generation

## License

Proprietary. All rights reserved.
