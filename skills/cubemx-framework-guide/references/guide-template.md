# CubeMX Guide Template

Use this template when writing `docs/releases/<version>/cubemx_build.md`.

## 1. Project Identification

- Project name:
- Software design document:
- Hardware connection diagram:
- MCU model:
- Inference notes:

## 2. CubeMX Project Creation

- MCU/Board selector:
- Project name:
- Toolchain/IDE:
- Project location:
- Firmware package assumptions:

## 3. Pinout Configuration

Create one row per used pin.

| Pin | CubeMX function | Connected module/signal | Mode or role | Key notes |
| --- | --- | --- | --- | --- |
| PAx | USARTx_TX | Wireless module TX input | Alternate Function Push-Pull | High speed, no pull |

Also list reserved or forbidden pins when the hardware document makes that necessary.

## 4. Peripheral Configuration

Create one subsection per required peripheral.

### 4.x `GPIO`
- Required groups:
- Output default levels:
- Input pull configuration:
- External interrupt lines:

### 4.x `[Peripheral name]`
- Enable:
- Mode:
- Key parameters:
- DMA:
- NVIC:
- Notes:

## 5. Clock and System Settings

- RCC / clock source:
- SYS debug:
- Core frequency target:
- Bus frequency targets:
- Timer clock assumptions:
- Watchdog or backup domain notes:

## 6. Middleware and Project Manager

- RTOS:
- File generation mode:
- HAL/LL choice:
- Separate per-peripheral files:
- Generated function call preferences:
- Additional code generator notes:

## 7. Mapping to Software Modules

Map documented software modules to the CubeMX-enabling settings they depend on.

| Software module | Depends on CubeMX items | Ready after generation | Notes |
| --- | --- | --- | --- |
| Attitude acquisition | I2C1, EXTI line, GPIO pins | Yes/No | JY61 interface |

## 8. Pre-Generation Checklist

- [ ] MCU model and package match the hardware document.
- [ ] All documented external modules have pins assigned.
- [ ] All required peripherals are enabled.
- [ ] Clock tree satisfies documented timing assumptions.
- [ ] Interrupt and DMA settings required by the design are enabled.
- [ ] Debug interface is preserved.
- [ ] Reserved pins are not reused.

## 9. Generation Result Expected Structure

- Expected project files:
- Expected generated folders:
- Files the user should keep unchanged before software coding:

## 10. User Action

Tell the user to generate the project in CubeMX and return after completion.
