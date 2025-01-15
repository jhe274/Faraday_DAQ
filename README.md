
# FR_DAQ System

This repository contains a comprehensive Data Acquisition (DAQ) system designed for field experiments. 
It includes scripts, data, and libraries for the efficient operation of the system.

## Features

- Data collection using lock-in amplifiers.
- Integration with Thorlabs TC300 temperature controller.
- Test scripts for validating the DAQ functionalities.

## Repository Structure

```
FR_DAQ/
├── FieldCrumley/
│   ├── Data/
│   │   └── Lock-ins/             # Lock-in amplifier data and logs.
├── test scripts/
│   ├── test.py                   # A general-purpose test script for validation.
│   └── Wide_scan_test.py         # A test script for wide-scan measurements.
├── Thorlabs/
│   └── TC300/                    # Contains scripts and libraries for TC300 controller.
│       ├── TC300_COMMAND_LIB.py  # Library for controlling TC300.
│       ├── TC300_COMMAND_LIB_EXAMPLE.py # Example usage of TC300 library.
│       └── TC300COMMANDLIB_win64.dll # Windows DLL for TC300.
└── README.md                     # This documentation file.
```

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/FR_DAQ.git
   cd FR_DAQ
   ```
2. Ensure Python 3.10 or higher is installed.
3. Install dependencies (if any are listed in the specific script).

## Usage

### Running the Test Scripts
- To test the system, run:
  ```bash
  python test scripts/test.py
  ```

### Using the TC300 Library
- Navigate to the `Thorlabs/TC300/` directory.
- Refer to the `TC300_COMMAND_LIB_EXAMPLE.py` for detailed usage instructions.

### Data Analysis
- Lock-in amplifier data is stored in the `FieldCrumley/Data/Lock-ins/` directory.
- Process these data files using Python or dedicated data analysis software.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Author

Jiachen He  
University of Kentucky
