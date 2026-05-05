# TDD Slice Rules

Split work by behavior, not by file. A slice should prove one externally meaningful behavior or one narrow internal behavior that the software design makes necessary.

Each slice must define:

- Requirement: requirement or software-design section being implemented.
- Layer: `Common`, `Module`, `Board`, `app` or `APP`, `Config`, or cross-layer integration.
- Given/When/Then: observable test scenario.
- Hardware boundary: real dependency and chosen mock, fake, or stub.
- Files likely touched: expected test files and implementation files.
- Done condition: exact passing tests and integration checks.

Good slices:

- "Given a debounced button fake, when three stable press samples arrive, then the app emits one short-press event."
- "Given an I2C register fake returning WHO_AM_I, when the MPU6050 driver initializes, then it reports ready and records the expected register writes."
- "Given sensor data exceeds a configured threshold, when the control service ticks, then it enters fault state and requests LED warning mode."

Poor slices:

- "Implement all files in Module."
- "Write Board layer."
- "Add display support."
- "Finish software design."

Keep slices small enough that a failing test points to one behavior. If two slices must edit the same state machine, shared queue, callback dispatch, or public API, run them serially.
