# Wayne Kerr 4235 LCR Meter - RS232 Automation
**Author:** Bien Pham

## Overview
This project provides an automated data acquisition solution for interfacing with the **Wayne Kerr 4235 LCR Meter** via RS232 serial communication. It is designed to streamline the process of measuring, extracting, and logging RLC (Resistance, Inductance, Capacitance) parameters, eliminating the need for manual data entry and significantly improving measurement efficiency in manufacturing.

## Key Features
- **Serial Communication:** Establishes a stable RS232 connection to send commands and receive data from the Wayne Kerr 4235.
- **Automated Parameter Extraction:** Queries the instrument and accurately parses raw measurement strings (e.g., R, L, C, Z, D, Q).
- **Tool Improvement:** Replaces manual reading processes, reducing human error and saving time during repetitive testing cycles.
- **Data Logging Ready:** Parses the output into structured formats that can be easily integrated into databases.

## Tech Stack
- **Language:** Python 3.x
- **Communication:** `pyserial` library

## Hardware Required
- **Instrument:** Wayne Kerr 4235 LCR Meter
- **Connection:** RS232 cable / RS232-to-USB converter
- **PC:** Windows / Linux
