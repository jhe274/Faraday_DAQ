# Polarization Modulation Ellipsometer Measurement System

## Overview
This repository provides a **comprehensive and modular control system** for conducting **polarization modulation ellipsometry (PME) measurements** using a variety of scientific instruments, including:
- **Bristol 871A Wavelength Meter** (first complete Python control package available online)
- **Signal Recovery DSP 7265 Lock-in Amplifiers** (using `pymeasure.instruments.signalrecovery.DSP7265`)
- **TOPTICA DLC Pro Tunable Diode Laser**
- **National Instruments cDAQ-9172 Data Acquisition System**
- **Lakeshore 475 Gaussmeter**
- **Thorlabs TC300 Temperature Controller**

The code is structured to facilitate **expandability**, allowing users to integrate additional devices and measurement routines as needed.

---
## Features
✅ **Full control** over the Bristol 871A wavelength meter (Telnet & Serial communication)  
✅ **Modular instrument control** for multiple DSP 7265 lock-in amplifiers using `pymeasure`  
✅ **Automated wide-scan and locked-laser measurement routines**  
✅ **Support for synchronous data acquisition and timestamped data logging**  
✅ **Industry-standard Python implementation** for laboratory automation  

---
## Folder Structure
```plaintext
📂 Faraday_Rotation_Measurement_System/
├── 📂 Bristol871/
│   ├── Bristol_871A.py        # Full Python driver for Bristol 871A Wavelength Meter
│   ├── __init__.py            # Module initialization
│
├── 📂 pymeasure/
├──── 📂 instruments/
├────── 📂 signalrecovery/
│       ├── dsp7265.py         # Module initialization (Note: Using `pymeasure` for lock-in control)
│       ├── dsp_base.py
│       ├── __init__.py        # Module initialization
│
├── 📂 TopticaDLCpro/
│   ├── Laser.py               # Control script for TOPTICA DLC Pro Tunable Diode Laser
│   ├── __init__.py            # Module initialization
│
├── 📂 instruments/
│   ├── lakeshore.py           # Control script for Lakeshore 475 Gaussmeter
│   ├── TC300_COMMAND_LIB.py   # Control script for Thorlabs TC300 Temperature Controller
│
├── WideScan_Measure.py        # Script for wide-scan Faraday rotation measurements
├── LockedLaser_Measure.py     # Script for locked-laser Faraday rotation measurements
├── README.md                  # This file
└── requirements.txt           # List of required Python dependencies
```

---
## Installation
### 1️⃣ Clone the repository
```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/Faraday_Rotation_Measurement_System.git
cd Faraday_Rotation_Measurement_System
```

### 2️⃣ Install dependencies
Ensure you have Python **3.8+** installed, then install required packages:
```bash
pip install -r requirements.txt
```

---
## Usage
### 🔹 Wide-Scan Measurement
Run **WideScan_Measure.py** for scanning a broad range of wavelengths:
```bash
python WideScan_Measure.py
```
This script controls:
- **Bristol 871A** for wavelength measurements
- **DSP 7265 lock-in amplifiers** (using `pymeasure.instruments.signalrecovery.DSP7265`)
- **TOPTICA DLC Pro** for laser control
- **NI-cDAQ-9172** for triggering

### 🔹 Locked-Laser Measurement
For locked laser experiments, run **LockedLaser_Measure.py**:
```bash
python LockedLaser_Measure.py
```
This script controls:
- **Bristol 871A** for wavelength measurements
- **DSP 7265 lock-in amplifiers** (using `pymeasure.instruments.signalrecovery.DSP7265`)
- **Wavetek 50 MHz Function generator, model 80** for voltage controlled magnetic field modulation
- **NI-cDAQ-9172** for triggering

These scripts are optimized for:
- **Voltage controlled magnetic field modulation**
- **Synchronous data acquisition**
- **Automated timestamp logging**
- **Support both triggered/gated mode for triggering Bristol wavelengthm meter during meausurement**
- **Automated data saving process**

---
## Instrument Control Modules
### 📡 **Bristol 871A Wavelength Meter**
- The **first complete Python control package** for the Bristol 871A.
- Supports **Telnet and Serial communication**.
- Handles **buffer retrieval, calibration, and data logging**.

### 🎛 **Signal Recovery DSP 7265 Lock-in Amplifiers**
- Uses **`pymeasure.instruments.signalrecovery.DSP7265`**.
- Allows **harmonic, phase, and sensitivity settings**.
- Supports **data buffer retrieval** for real-time measurements.

### 🔬 **TOPTICA DLC Pro Tunable Diode Laser**
- **Full integration** with the TOPTICA SDK.
- Supports **wide-scan control, triggering, and post measurement data acquisition**.

### 🏷 **National Instruments cDAQ-9172**
- Used for **synchronized triggering** of all devices.
- Configured to interface with **NI DAQmx drivers**.

---
## Data Logging & Output Format
Data is **automatically saved** in organized directories under `Faraday rotation measurements/`.

**Example Data Structure:**
```plaintext
📂 PME_measurements/
├── 📂 Vapor_cell/
│   ├── 📂 Holding_field_data/
│   │   ├── 📂 XX-XX-20XX
│   │       ├── Gaussmeter_20XX-XX-XX.csv
│   │
│   ├── 📂 Bristol_data/
│   │   ├── 📂 XX-XX-20XX
│   │       ├── Bristol_20XX-XX-XX.csv
│   │
│   ├── 📂 Lockins_data/
│   │   ├── 📂 XX-XX-20XX
│   │       ├── Faraday_lockins_20XX-XX-XX.lvm
│   │
│   ├── 📂 TC300_data/
│   │   ├── 📂 XX-XX-20XX
│   │       ├── Faraday_lockins_20XX-XX-XX.csv
│   │
│   ├── 📂 TopticaDLCpro_data/
│   │   ├── 📂 XX-XX-20XX
│   │       ├── Faraday_lockins_20XX-XX-XX.csv
```

### 📑 Example CSV Format for Bristol Data
```csv
Timestamp,Wavelength (nm),Power (mW)
2024-01-30T12:30:01.123,770.123456,0.512
2024-01-30T12:30:02.456,770.124678,0.510
```

### 📑 Example LVM Format for Lock-In Data
```csv
#1f Time Constant [s]: 0.1
#1f Sensitivity [V]: 0.01
Timestamp,X_1f,Y_1f,X_2f,Y_2f,X_DC,Y_DC,X_Mod,Y_Mod
2024-01-30T12:30:01.123,0.0023,0.0004,0.0056,0.0011,0.0009,0.0002,0.0035,0.0021
```

---
## Future Enhancements 🚀
This repository is **modular and expandable**. Future plans include:
- 📊 **Machine learning models** for Faraday rotation analysis.
- 🔄 **Support for additional instruments (e.g., Keysight, LakeShore DSP 275 Gaussmeter)**.

---
## Contributions 🤝
We welcome **collaborations and improvements**! Feel free to open issues or submit pull requests.

---
## License 📜
This repository is licensed under the **MIT License**.

---
## Contact
🔬 **Maintainer:** Jiachen He  
📧 Email: jiachen.he@outlook.com  
🌐 Website: [https://jhe274.github.io/portfolio-bruce.github.io//]
