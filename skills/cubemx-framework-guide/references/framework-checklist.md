# Framework Review Checklist

Use this checklist when reviewing the CubeMX-generated project.

## 1. Artifact Discovery

Check for the newest relevant files:
- `.ioc`
- `Core/Inc/*.h`
- `Core/Src/*.c`
- `Drivers/`
- startup file
- IDE or build-system project files

## 2. MCU and Base System

- MCU part number matches the hardware document.
- Debug interface is enabled as required.
- Clock source configuration is plausible for the target board.
- Core and bus clocks align with the design assumptions.

## 3. GPIO and External Wiring

- Every documented external signal has a mapped GPIO.
- Pin modes match the role: input, output, alternate function, analog, or EXTI.
- Pull-up, pull-down, output level, and speed are not obviously inconsistent with the hardware connection.
- Reserved pins are not assigned to unrelated functions.

## 4. Peripheral Coverage

For each software module, confirm the required peripheral foundation exists:
- UART / USART
- I2C
- SPI
- ADC
- TIM / PWM / encoder
- CAN
- USB
- RTC
- Watchdog
- DMA

Mark each as `Present`, `Missing`, or `Unclear`.

## 5. Interrupt and DMA Readiness

- Required IRQ lines are enabled.
- Priorities are not obviously conflicting with documented timing needs.
- DMA channels/streams exist where the design requires them.

## 6. Generated Framework Readiness

- The generated project contains enough HAL startup code for later module implementation.
- Header and source structure exist for adding application code.
- No required module is blocked by missing low-level initialization.

## 7. Attribution Rules

Treat an issue as `Guide gap` when:
- the guide omitted a required setting
- the guide used ambiguous wording
- the guide specified a wrong CubeMX choice

Treat an issue as `User configuration issue` when:
- the guide clearly named the required setting
- the generated project differs from that instruction

## 8. Review Output Format

Report with three sections:

### Passed
- concrete items that match the documents

### Issues
- issue
- evidence from generated project
- required correction
- attribution: `Guide gap` or `User configuration issue`

### Conclusion
- `Pass` if the framework supports later software development
- otherwise `Needs correction`
