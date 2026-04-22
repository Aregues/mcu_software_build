# 仿生鱼控制系统 - STM32CubeMX 程序框架生成指引

## 1. 项目标识

- 项目名称：仿生鱼控制系统
- 软件设计文档：`docs/software_design/仿生鱼控制系统-26-04-11.md`
- 硬件连接图：`docs/Hardware/仿生鱼控制系统-26-04-11.json`
- 需求文档：`docs/Requirements/仿生鱼控制系统-26-04-11.md`
- 目标 MCU：STM32F407VET6
- 目标封装：LQFP100

### 1.1 本指引的用途

本文档用于指导在 STM32CubeMX 中生成后续软件开发所需的基础工程框架。目标是先把 MCU、时钟、引脚、定时器、串口、DMA、中断和代码生成选项配置正确，使后续可以继续实现：

- 无线控制链路
- IMU 姿态采集链路
- INA219 功率采集链路
- 尾鳍舵机 PWM 输出
- 10ms 控制周期调度

### 1.2 文档事实与推导说明

- 文档明确给出的事实：
  - MCU 为 `STM32F407VET6`
  - 外部晶振为 `8MHz`
  - `USART3` 用于 E62-433T20D 无线模块
  - `USART6` 用于 JY61
  - `TIM5_CH2` 用于尾鳍舵机 PWM
  - `TIM6` 用于 10ms 周期控制
  - INA219 当前按“软件 I2C”使用，连接到 `PB8/PB9`
- 依据文档推导的设置：
  - 使用 STM32CubeMX 生成 HAL 工程骨架，后续在此基础上接入现有分层代码
  - `PB8/PB9` 先配置为普通 GPIO，用于后续软件 I2C
  - `USART3_RX`、`USART6_RX` 配置 DMA 接收，并配合空闲中断处理
  - `PA13/PA14` 保留 SWD 调试

---

## 2. CubeMX 新建工程

### 2.1 新建方式

1. 打开 STM32CubeMX。
2. 选择 `MCU/MPU Selector`。
3. 搜索并选择 `STM32F407VETx`。
4. 确认封装为 `LQFP100`。
5. 新建工程。

### 2.2 Project Manager 基本信息

- Project Name：`BionicFishCtrl` 或你希望使用的工程名
- Project Location：放到你的实际代码工作目录
- Toolchain / IDE：按你的开发环境选择，建议优先选择后续实际使用的 IDE
- Firmware Package：使用与本机 CubeMX 可用版本一致的 STM32F4 HAL 包

### 2.3 代码生成方式

在 `Project Manager -> Code Generator` 中建议设置：

- 勾选 `Generate peripheral initialization as a pair of '.c/.h' files per peripheral`
- 勾选 `Keep User Code when re-generating`
- 不勾选会强行重写用户区以外大量文件的选项

目的：

- 方便后续把 `BSP / Devices / Apps / User` 结构接进来
- 减少后续反复生成时对用户代码的破坏

---

## 3. Pinout 配置

### 3.1 必须配置的引脚

| 引脚 | CubeMX 功能 | 连接模块/信号 | 配置要求 | 说明 |
| --- | --- | --- | --- | --- |
| `PA1` | `TIM5_CH2` | `Savox_SW-1210SG:SIG` | PWM 输出 | 尾鳍舵机控制输出 |
| `PB10` | `USART3_TX` | `E62-433T20D:RXD` | 串口发送 | 无线下行/上行链路 |
| `PB11` | `USART3_RX` | `E62-433T20D:TXD` | 串口接收 | 需配合 DMA RX |
| `PC6` | `USART6_TX` | `JY61:RX` | 串口发送 | IMU 配置或保留发送 |
| `PC7` | `USART6_RX` | `JY61:TX` | 串口接收 | 需配合 DMA RX |
| `PB8` | `GPIO_Output` | `INA219:SCL` | 普通 GPIO 输出 | 软件 I2C SCL，不开硬件 I2C |
| `PB9` | `GPIO_Output` | `INA219:SDA` | 普通 GPIO 输出 | 软件 I2C SDA，不开硬件 I2C |
| `PA13` | `SYS_SWDIO` | 调试接口 | 保留 | SWD 调试必须保留 |
| `PA14` | `SYS_SWCLK` | 调试接口 | 保留 | SWD 调试必须保留 |
| `PH0` | `RCC_OSC_IN` | HSE 输入 | 外部晶振 | 8MHz HSE |
| `PH1` | `RCC_OSC_OUT` | HSE 输出 | 外部晶振 | 8MHz HSE |

### 3.2 不要误配的点

- `PB8/PB9` 不要配置为 `I2C1_SCL/I2C1_SDA`
  - 原因：软件设计文档明确 BSP 层使用“软件 I2C”
- `PA13/PA14` 不要挪作普通 GPIO
  - 原因：需要保留 SWD 下载和调试
- `TIM6` 是内部基础定时器，不占外部引脚

### 3.3 GPIO 详细建议

#### `PB8` - 软件 I2C SCL

- Mode：`Output Open Drain`
- Pull：`No Pull`
- Speed：`Low` 或 `Medium`

说明：

- 推荐开漏输出，符合 I2C 总线习惯
- `INA219` 模块板通常带上拉，但当前文档没有把外部上拉网络写成硬件强约束，所以这里不在 CubeMX 内部开启上拉
- 如果后续实物验证发现总线电平恢复慢，再检查模块板是否自带上拉电阻

#### `PB9` - 软件 I2C SDA

- Mode：`Output Open Drain`
- Pull：`No Pull`
- Speed：`Low` 或 `Medium`

#### 其他 GPIO

- 若 CubeMX 为复用功能自动生成对应 GPIO，不需要再单独重复手动改配
- 当前文档未要求配置本地按键、指示灯、AUX、LOCK、M0 控制脚，因此第一版工程先不要额外占用 GPIO

---

## 4. RCC 与时钟树配置

### 4.1 RCC 基础设置

在 `System Core -> RCC` 中配置：

- `High Speed Clock (HSE)`：`Crystal/Ceramic Resonator`
- `Low Speed Clock (LSE)`：保持默认未启用

### 4.2 时钟目标

根据需求文档，目标系统主频为 `168MHz`，外部晶振为 `8MHz`。

在 `Clock Configuration` 页中，配置为常见 STM32F407 168MHz 方案：

- HSE：`8MHz`
- SYSCLK：`168MHz`
- AHB：`168MHz`
- APB1：`42MHz`
- APB2：`84MHz`

### 4.3 说明

上述设置的目的是满足：

- `TIM5` 计数时钟可得到 `84MHz`
- `TIM6` 计数时钟可得到 `84MHz`
- 通过 `Prescaler = 83` 将计数频率降为 `1MHz`

这与软件设计文档中的以下要求一致：

- `TIM5` 输出 50Hz PWM
- `TIM6` 产生 10ms 周期中断

### 4.4 若 CubeMX 报告时钟冲突

优先保证：

1. `SYSCLK = 168MHz`
2. `APB1 Timer Clock = 84MHz`
3. `USART3`、`USART6` 能稳定生成 `115200`

---

## 5. SYS 配置

在 `System Core -> SYS` 中配置：

- Debug：`Serial Wire`
- Timebase Source：保持默认即可

说明：

- 当前控制周期由 `TIM6` 提供，不依赖 SysTick 作为业务调度源
- 但 HAL 仍可保留默认系统节拍

---

## 6. USART3 配置（无线模块 E62-433T20D）

### 6.1 串口模式

在 `Connectivity -> USART3` 中配置：

- Mode：`Asynchronous`
- Baud Rate：`115200`
- Word Length：`8 Bits`
- Parity：`None`
- Stop Bits：`1`
- Hardware Flow Control：`Disable`
- Over Sampling：`16 Samples`

### 6.2 DMA 配置

为 `USART3_RX` 增加 DMA：

- 方向：`Peripheral to Memory`
- 模式：`Normal`
- 外设地址递增：关闭
- 存储器地址递增：开启
- 数据宽度：`Byte`

说明：

- 软件设计文档要求“DMA 接收 + 空闲中断 + 重新装载 DMA”
- 这一模式更贴近后续 `接收一帧 -> IDLE 触发 -> 锁存长度 -> 重装 DMA` 的处理流程

### 6.3 NVIC 配置

需要启用：

- `USART3 global interrupt`
- `USART3 RX DMA interrupt`

### 6.4 相关硬件说明

- 当前连接图中 `M0` 已按硬件假设下拉到 GND，使模块工作在传输模式
- `AUX`、`LOCK` 未接入 MCU，因此第一版框架不为其分配 GPIO
- 后续若需要更可靠地判断模块状态，可再扩展 GPIO

---

## 7. USART6 配置（JY61 姿态模块）

### 7.1 串口模式

在 `Connectivity -> USART6` 中配置：

- Mode：`Asynchronous`
- Baud Rate：`115200`
- Word Length：`8 Bits`
- Parity：`None`
- Stop Bits：`1`
- Hardware Flow Control：`Disable`
- Over Sampling：`16 Samples`

说明：

- JY61 手册默认波特率为 `115200`
- 在 `115200` 下姿态输出频率可达 `100Hz`
- 这与系统 10ms 控制节拍相匹配

### 7.2 DMA 配置

为 `USART6_RX` 增加 DMA：

- 方向：`Peripheral to Memory`
- 模式：`Normal`
- 外设地址递增：关闭
- 存储器地址递增：开启
- 数据宽度：`Byte`

### 7.3 NVIC 配置

需要启用：

- `USART6 global interrupt`
- `USART6 RX DMA interrupt`

---

## 8. TIM5 配置（尾鳍舵机 PWM）

### 8.1 基本模式

在 `Timers -> TIM5` 中配置：

- Clock Source：`Internal Clock`
- Channel 2：`PWM Generation CH2`

### 8.2 参数设置

在 `Parameter Settings` 中设置：

- Prescaler：`83`
- Counter Period：`19999`
- Counter Mode：`Up`
- Auto-reload preload：建议开启

### 8.3 PWM 通道参数

针对 `CH2`：

- Pulse：先填 `1615`
- PWM mode：`PWM mode 1`
- Polarity：`High`
- Fast Mode：`Disable`

### 8.4 说明

当 `TIM5` 计数时钟为 `84MHz` 时：

- `84MHz / (83 + 1) = 1MHz`
- `1MHz / (19999 + 1) = 50Hz`

即得到：

- PWM 周期：`20ms`
- 初始脉宽计数值：`1615`

这与设计文档中的默认舵机中位值一致。

### 8.5 后续软件边界

后续软件中要保持：

- 中位：`1615`
- 最小：`1156`
- 最大：`2074`

这些限幅不是 CubeMX 参数，而是后续控制模块逻辑约束。

---

## 9. TIM6 配置（10ms 控制周期）

### 9.1 基本模式

在 `Timers -> TIM6` 中配置：

- Activated：启用
- Clock Source：`Internal Clock`

### 9.2 参数设置

在 `Parameter Settings` 中设置：

- Prescaler：`83`
- Counter Period：`9999`
- Auto-reload preload：建议开启

### 9.3 NVIC 配置

启用：

- `TIM6 global interrupt`

### 9.4 说明

当 `TIM6` 计数时钟为 `84MHz` 时：

- `84MHz / (83 + 1) = 1MHz`
- `1MHz / (9999 + 1) = 100Hz`

即每 `10ms` 触发一次更新事件，满足控制主调度要求。

---

## 10. DMA 总体要求

### 10.1 必须存在的 DMA 通道

至少要有：

- `USART3_RX` 对应 DMA
- `USART6_RX` 对应 DMA

### 10.2 配置原则

- 以 `RX DMA` 为核心，`TX DMA` 第一版先不强制
- 优先保证无线接收和 IMU 接收链路
- 若 CubeMX 自动分配的 DMA Stream/Channel 与其他外设冲突，优先保留两路串口 RX

### 10.3 中断优先级建议

第一版可以先使用 CubeMX 默认优先级；若手动调整，建议遵循：

- `TIM6` 不低于普通后台中断
- `USART3`、`USART6` 和对应 DMA 中断保持可及时响应
- 不在第一版中引入过度复杂的优先级设计

当前软件设计文档没有给出必须固定的 NVIC 数值优先级，因此这里不强制写死具体数字。

---

## 11. 中间件与 RTOS

### 11.1 配置要求

- 不启用 FreeRTOS
- 不启用 USB
- 不启用 FATFS
- 不启用 LWIP
- 不启用其他中间件

### 11.2 原因

软件设计文档明确要求：

- 裸机 + 中断驱动
- 主循环空转 + 外设中断 + `TIM6` 周期调度

因此第一版 CubeMX 工程应保持最小骨架，不要引入 RTOS 或额外中间件。

---

## 12. 生成后需要具备的基础初始化能力

生成后的工程至少应能提供以下初始化入口：

- GPIO 初始化
- DMA 初始化
- USART3 初始化
- USART6 初始化
- TIM5 初始化
- TIM6 初始化
- 时钟初始化

后续软件开发时，通常还需要在用户代码中补充：

- 启动 `TIM5 PWM`
- 启动 `TIM6 Base + Interrupt`
- 启动 `USART3 RX DMA`
- 启动 `USART6 RX DMA`
- 使能串口空闲中断
- 软件 I2C 的 GPIO 初始化细化

注意：

- CubeMX 只负责生成基础框架
- “空闲中断回调 + DMA 重装 + 帧解析” 逻辑属于后续软件实现部分

---

## 13. 软件模块到 CubeMX 配置的映射

| 软件模块 | 依赖的 CubeMX 配置 | 生成后是否具备基础条件 | 说明 |
| --- | --- | --- | --- |
| 系统初始化模块 | RCC、SYS、GPIO、DMA | 是 | 提供基础硬件初始化入口 |
| 无线接收解析模块 | USART3、DMA、USART3 IRQ | 是 | 还需后续补空闲中断处理逻辑 |
| IMU 采集模块 | USART6、DMA、USART6 IRQ | 是 | 还需后续补 JY61 帧解析 |
| 尾鳍控制模块 | TIM5_CH2 PWM | 是 | 还需后续补占空比换算和限幅 |
| 调度与运行状态模块 | TIM6 IRQ | 是 | 还需后续补 10ms 控制任务 |
| 功率采集模块 | PB8/PB9 GPIO | 部分具备 | 只完成软件 I2C 引脚基础准备 |
| 遥测发送模块 | USART3 TX | 是 | 还需后续补协议封装和发送逻辑 |
| 异常检测与保护模块 | TIM6、USART IRQ 基础设施 | 部分具备 | 逻辑需后续软件实现 |

---

## 14. 生成前检查清单

在点击 `GENERATE CODE` 前，逐项确认：

- [ ] MCU 已选择 `STM32F407VETx`
- [ ] 封装确认为 `LQFP100`
- [ ] `HSE = Crystal/Ceramic Resonator`
- [ ] `SYSCLK = 168MHz`
- [ ] `PB10/PB11` 已配置为 `USART3_TX/RX`
- [ ] `PC6/PC7` 已配置为 `USART6_TX/RX`
- [ ] `PA1` 已配置为 `TIM5_CH2`
- [ ] `PB8/PB9` 已配置为普通 `GPIO Output Open Drain`
- [ ] `TIM5` 参数为 `PSC=83`、`ARR=19999`
- [ ] `TIM5 CH2 Pulse` 初值为 `1615`
- [ ] `TIM6` 参数为 `PSC=83`、`ARR=9999`
- [ ] `USART3` 波特率为 `115200 8N1`
- [ ] `USART6` 波特率为 `115200 8N1`
- [ ] `USART3_RX` 已配置 DMA
- [ ] `USART6_RX` 已配置 DMA
- [ ] `USART3 global interrupt` 已启用
- [ ] `USART6 global interrupt` 已启用
- [ ] `TIM6 global interrupt` 已启用
- [ ] `SYS Debug` 已选择 `Serial Wire`
- [ ] 未启用 FreeRTOS 和其他无关中间件

---

## 15. 生成后预期工程结构

生成完成后，至少应看到以下内容中的大部分：

- `.ioc` 工程配置文件
- `Core/Inc`
- `Core/Src`
- `Drivers/STM32F4xx_HAL_Driver`
- `Drivers/CMSIS`
- 对应 IDE 的工程文件

并且应能在代码中看到以下初始化函数：

- `MX_GPIO_Init()`
- `MX_DMA_Init()`
- `MX_USART3_UART_Init()`
- `MX_USART6_UART_Init()`
- `MX_TIM5_Init()`
- `MX_TIM6_Init()`
- `SystemClock_Config()`

---

## 16. 当前版本不纳入 CubeMX 的内容

以下内容不是本次 CubeMX 点选阶段必须完成的内容，不要因为它们还没实现就继续往 CubeMX 里堆设置：

- 无线 ASCII 协议解析
- `TA{value}E` / `TAOFFE` 业务逻辑
- JY61 帧校验与角度解算
- INA219 寄存器读写逻辑
- 遥测打包协议
- 舵机角度到比较值换算
- 安全限幅与状态机

这些都属于后续具体软件编写阶段。

---

## 17. 用户操作

请按本文档完成 CubeMX 配置并生成工程。

生成完成后，把生成出来的项目框架放到你的工作目录中，然后直接告诉我“已完成生成”。下一步我会检查：

- `.ioc` 是否符合本指引
- 初始化框架是否已具备各模块落地条件
- 若不符合，是本文档缺项，还是 CubeMX 配置执行偏差