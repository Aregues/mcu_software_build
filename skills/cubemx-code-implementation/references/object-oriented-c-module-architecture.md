# Object-Oriented C Module Architecture

Use this reference when designing, implementing, or reviewing embedded modules on top of a CubeMX-generated project. The goal is to apply encapsulation, inheritance, polymorphism, and dependency inversion in plain C without adding a complex framework.

## Layer Model

Design each module with four explicit layers:

1. Capability interface layer:
   - defines the stable abstract interface, base struct, ops function-pointer table, public wrapper functions, status enums, and capability flags when needed
   - contains no HAL, register, CubeMX-generated, board, or concrete-driver dependency
   - exposes names such as `led_base_t`, `led_ops_t`, `led_on()`, `led_off()`, `led_set_brightness()`
   - preferably lives in `Common/*_if.h` and optional `Common/*_if.c`; if the existing project already has a different interface location, keep the same dependency boundary
2. Concrete driver layer:
   - defines derived structs and concrete initialization functions such as `led_gpio_t`, `led_gpio_init()`, `led_pwm_t`, `led_pwm_init()`
   - embeds the base struct as the first member of each derived struct so a `derived *` can be used through `base *`
   - binds a `static const xxx_ops_t` table to the base object during init
   - may include HAL/CubeMX headers and hardware-resource types
3. Board binding layer:
   - creates static or owned object instances, supplies GPIO ports, pins, timer channels, I2C/SPI/UART handles, DMA buffers, and configuration values
   - calls concrete init functions
   - returns or registers only abstract base pointers for the business layer
   - lives in a dedicated top-level directory such as `Board` or `board`, at the same level as `Common`, `app`, and `Module`
   - must not be placed inside concrete driver folders and must not be mixed into the business `app` directory
4. Business application layer:
   - stores and calls only abstract base pointers, such as `led_base_t *`
   - uses public wrapper functions and capability queries instead of `switch`/`if` checks on concrete type
   - never casts an abstract pointer to a concrete implementation type

## Recommended File Structure

Adapt names to the module domain but preserve the dependency boundaries:

```text
<CubeMX project>/
  Common/
    led_if.h             # capability interface
    led_if.c             # public wrapper functions and common validation, if needed
  Module/
    led/
      led_gpio.h         # GPIO-derived type and init declaration
      led_gpio.c         # GPIO concrete behavior and ops binding
      led_pwm.h          # PWM-derived type and init declaration, when needed
      led_pwm.c          # PWM concrete behavior and ops binding
  app/
    app.c                # business logic; includes led_if.h only
    app.h
  Board/
    board.h              # abstract board services exported to app
    board.c              # board binding; includes concrete driver headers
```

Keep CubeMX files such as `Core/Src/main.c`, `Core/Inc/main.h`, `Drivers`, startup files, and linker scripts in their generated locations. Use CubeMX user-code blocks only to call board/app initialization and scheduling entry points.

## File Responsibilities

- `Common/xxx_if.h`: abstract base type, ops table, error/status enum, capability flags, and public wrappers.
- `Common/xxx_if.c`: wrapper functions such as `xxx_start()`, `xxx_stop()`, `xxx_read()`, including null checks, unsupported-operation handling, and stable API behavior when wrappers need implementation.
- `xxx_gpio.h` / `xxx_pwm.h` / `xxx_i2c.h`: concrete derived type, hardware-resource config struct, and init declaration.
- `xxx_gpio.c` / `xxx_pwm.c` / `xxx_i2c.c`: concrete HAL/CubeMX behavior, private static ops functions, and ops-table binding.
- `Board/board.h`: abstract object accessors or board-level init API used by `app`; do not expose concrete driver types here unless the file is explicitly board-private.
- `Board/board.c`: static object allocation, concrete init calls, CubeMX handle injection, and abstract pointer registration.
- `app.c`: business state machine and policy using only abstract headers.

## Header Include Relationships

- `app.c` includes `app.h`, `board.h`, and capability interface headers such as `led_if.h`.
- `app.c` does not include `led_gpio.h`, `led_pwm.h`, `main.h`, `stm32xxxx_hal.h`, GPIO/PWM/I2C/SPI headers, or register headers.
- `Board/board.c` may include `main.h`, generated CubeMX handle declarations, and concrete driver headers such as `led_gpio.h`.
- concrete drivers include their own concrete header, the capability interface header, and required HAL/CubeMX headers.
- capability interface headers include only standard C headers needed for fixed-width types and booleans, such as `<stdint.h>`, `<stdbool.h>`, and `<stddef.h>`.

## Capability Struct Pattern

Use this C pattern for modules that need polymorphism. Place it in `Common/led_if.h` or the project's established capability-interface location:

```c
typedef struct led_base led_base_t;

typedef enum {
    LED_OK = 0,
    LED_ERR_ARG,
    LED_ERR_UNSUPPORTED,
    LED_ERR_HW
} led_status_t;

typedef struct {
    led_status_t (*on)(led_base_t *self);
    led_status_t (*off)(led_base_t *self);
    led_status_t (*set_brightness)(led_base_t *self, uint8_t percent);
    uint32_t (*capabilities)(const led_base_t *self);
} led_ops_t;

struct led_base {
    const led_ops_t *ops;
};

led_status_t led_on(led_base_t *self);
led_status_t led_off(led_base_t *self);
led_status_t led_set_brightness(led_base_t *self, uint8_t percent);
uint32_t led_capabilities(const led_base_t *self);
```

Derived types must place the base object first:

```c
typedef struct {
    led_base_t base;
    GPIO_TypeDef *port;
    uint16_t pin;
    GPIO_PinState active_state;
} led_gpio_t;

led_status_t led_gpio_init(led_gpio_t *self,
                           GPIO_TypeDef *port,
                           uint16_t pin,
                           GPIO_PinState active_state);
```

The concrete driver binds behavior through `ops`, not through business-layer branching:

```c
static led_status_t led_gpio_on(led_base_t *base)
{
    led_gpio_t *self = (led_gpio_t *)base;
    HAL_GPIO_WritePin(self->port, self->pin, self->active_state);
    return LED_OK;
}

static const led_ops_t led_gpio_ops = {
    .on = led_gpio_on,
    .off = led_gpio_off,
    .set_brightness = NULL,
    .capabilities = led_gpio_capabilities,
};

led_status_t led_gpio_init(led_gpio_t *self,
                           GPIO_TypeDef *port,
                           uint16_t pin,
                           GPIO_PinState active_state)
{
    if (self == NULL || port == NULL) {
        return LED_ERR_ARG;
    }

    self->base.ops = &led_gpio_ops;
    self->port = port;
    self->pin = pin;
    self->active_state = active_state;
    return LED_OK;
}
```

Wrapper functions check arguments and unsupported operations:

```c
led_status_t led_set_brightness(led_base_t *self, uint8_t percent)
{
    if (self == NULL || self->ops == NULL) {
        return LED_ERR_ARG;
    }
    if (self->ops->set_brightness == NULL) {
        return LED_ERR_UNSUPPORTED;
    }
    return self->ops->set_brightness(self, percent);
}
```

## Initialization and Board Binding Flow

Use a simple, explicit sequence:

1. CubeMX initializes clocks, GPIO, DMA, timers, buses, middleware, and generated handles.
2. `board_init()` initializes concrete objects with CubeMX resources.
3. `app_init()` receives only abstract pointers or obtains them through `board_get_xxx()` accessors.
4. main loop, RTOS task, timer callback, or generated HAL callback calls `app_process()` or a narrow app event API.

Example:

```c
/* Board/board.c */
static led_gpio_t status_led_gpio;
static led_base_t *status_led;

void board_init(void)
{
    (void)led_gpio_init(&status_led_gpio, STATUS_LED_GPIO_Port, STATUS_LED_Pin, GPIO_PIN_SET);
    status_led = &status_led_gpio.base;
}

led_base_t *board_get_status_led(void)
{
    return status_led;
}
```

```c
/* app.c */
static led_base_t *app_status_led;

void app_init(led_base_t *status_led)
{
    app_status_led = status_led;
}

void app_process(void)
{
    (void)led_on(app_status_led);
}
```

```c
/* main.c USER CODE block */
board_init();
app_init(board_get_status_led());

while (1) {
    app_process();
}
```

## Required Architecture Output

When asked to design or implement a specified module, include or produce these items as applicable:

1. recommended file structure
2. responsibility of each file
3. header include relationships
4. capability struct and ops-table design
5. initialization and board-binding flow
6. business-layer call example in C
7. dependency-direction explanation
8. common wrong patterns and corrections

Keep the language concise, use C examples, avoid introducing a complex framework, and target bare-metal, RTOS, and MCU projects.

## Common Wrong Patterns

Reject or correct these patterns during design and review:

- business code includes `stm32xxxx_hal.h`, `main.h`, `gpio.h`, `tim.h`, `i2c.h`, `spi.h`, `usart.h`, or concrete headers such as `led_gpio.h`
- business code switches on concrete device type or casts `led_base_t *` to `led_gpio_t *`
- capability interface headers include HAL/CubeMX headers or mention GPIO ports, timer handles, I2C/SPI handles, DMA handles, or chip registers
- concrete drivers call business-layer functions or depend on `app` state machines
- board binding exposes concrete objects to application code when an abstract pointer is sufficient
- optional features are forced into every implementation instead of using capability queries or extension interfaces
- the abstract interface grows every time one concrete device needs a special feature
- initialization duplicates CubeMX peripheral setup instead of using generated handles and user-code extension points
