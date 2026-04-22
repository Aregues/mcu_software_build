**整体结构**

1. 顶层是一个对象，包含这些主要字段：
2. project：项目名（字符串）
3. schema：格式类型（当前是 pin_to_pin_connections）
4. naming_rule：命名规则说明（当前是 设备名:引脚名）
5. devices：设备列表（字符串数组）
6. connections：信号连接（按模块分组）
7. power_connections：电源连接（电源轨）
8. notes：备注说明（字符串数组）

**connections 字段格式**

1. connections 是数组，每个元素表示一个模块：
2. module：模块名（必须在 devices 中出现）
3. links：该模块的连接列表
4. links 中每一项包含：
5. signal：信号名（如 TEMP_1WIRE、LCD_RS）
6. from_pin：当前 module 的引脚名
7. to：目标端，格式为 设备名:引脚名（遵循 naming_rule）

**power_connections 字段格式**

1. 每一项描述一条电源线：
2. rail：电源轨名（如 5V、3.3V、12V、GND）
3. from：源端，格式 设备名:引脚名
4. to：目标端，格式 设备名:引脚名

**编写时的关键约束**

1. 所有设备名应先在 devices 中声明，再在连接里使用。
2. to、from 字段统一使用 设备名:引脚名 格式。
3. 同一信号建议在双方模块都各写一条，形成“对称描述”。
4. signal 命名保持全局一致，避免同义不同名。
5. 引脚名保持芯片手册风格一致（如 PB12、PC0）。
6. 电源与信号分开写：信号放 connections，供电放 power_connections。
7. 特殊电气要求写在 notes（如上拉电阻、分压器）。

**建议的自检清单**

1. devices 中是否包含所有被引用设备。
2. 是否存在拼写不一致的设备名或引脚名。
3. 每条连接的 to 是否可被反向条目对应。
4. 电源轨是否覆盖所有需要供电和接地的模块。
5. notes 是否记录了非默认硬件条件。

**example**:

```json
{
  "project": "最小硬件接口示例",
  "schema": "pin_to_pin_connections",
  "naming_rule": "设备名:引脚名",
  "devices": ["STM32F103C8T6", "DS18B20 温度传感器", "电源管理系统"],
  "connections": [
    {
      "module": "STM32F103C8T6",
      "links": [
        {
          "signal": "TEMP_1WIRE",
          "from_pin": "PB12",
          "to": "DS18B20 温度传感器:DQ"
        }
      ]
    },
    {
      "module": "DS18B20 温度传感器",
      "links": [
        {
          "signal": "TEMP_1WIRE",
          "from_pin": "DQ",
          "to": "STM32F103C8T6:PB12"
        }
      ]
    }
  ],
  "power_connections": [
    {
      "rail": "3.3V",
      "from": "电源管理系统:3V3_OUT",
      "to": "STM32F103C8T6:VCC"
    },
    {
      "rail": "3.3V",
      "from": "电源管理系统:3V3_OUT",
      "to": "DS18B20 温度传感器:VCC"
    },
    {
      "rail": "GND",
      "from": "电源管理系统:GND",
      "to": "STM32F103C8T6:GND"
    },
    {
      "rail": "GND",
      "from": "电源管理系统:GND",
      "to": "DS18B20 温度传感器:GND"
    }
  ],
  "notes": ["DS18B20 DQ需要4.7kΩ上拉至3.3V"]
}
```
