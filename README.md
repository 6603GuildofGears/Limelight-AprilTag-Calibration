# 🎯 Limelight AprilTag Calibration Optimizer

A fast, automated calibration tool for optimizing AprilTag detection stability on Limelight cameras. Achieves sub-millimeter position stability in approximately 60-70 seconds.

## Overview

This tool automatically tunes Limelight camera parameters to minimize position jitter when detecting AprilTags. Instead of manually adjusting settings, the optimizer systematically tests parameter combinations and uses a "range-center" algorithm to find robust settings that work across varying conditions.

**Developed for FTC "Decode" 2025-2026 season.**

## Features

- ⚡ **Fast optimization** - Complete calibration in ~60-70 seconds
- 🎯 **Sub-millimeter accuracy** - Achieves 0.5-2mm position stability
- 🔄 **Auto-detection** - Automatically detects AprilTags 20 or 24
- �� **Range-center algorithm** - Finds robust settings, not just single best points
- 🛡️ **Safe defaults** - Starts from proven working settings
- 📈 **Verbose mode** - Optional detailed output for debugging

## Requirements

- Python 3.x
- `requests` library (`pip install requests`)
- Limelight camera on network (default: `172.29.0.1`)
- AprilTag visible to camera (Tags 20 or 24)

## Usage

### Basic Usage (Normal Output)
```bash
python3 final_optimize.py
```

### Verbose Mode (Detailed Output)
```bash
python3 final_optimize.py -v
# or
python3 final_optimize.py --verbose
```

## How It Works

The optimizer runs through 5 phases:

### Phase 1: Detection & Baseline
- Applies safe baseline settings to the camera
- Detects which AprilTag is visible (Tag 20 or 24)
- Measures initial stability as a baseline

### Phase 2: Coarse Parameter Search
- Tests a 5×5 grid of exposure and gain combinations
- **Exposure range**: 2400, 2800, 3200, 3600, 4000
- **Gain range**: 6, 7, 8, 9, 10
- Tracks which combinations improve on baseline
- Uses "range-center" logic to pick the middle of good values (more robust than single best)

### Phase 3: Fine-Tune Secondary Parameters
Tests and optimizes these parameters in sequence:
1. **Fiducial Refine Method** (None, Subpixel, Decode, Pose)
2. **Black Level** (15, 18, 20, 22, 25)
3. **Sharpening** (0, 0.05, 0.1, 0.15)
4. **Red Balance** (1180, 1230, 1280, 1330, 1380)
5. **Blue Balance** (1400, 1450, 1500, 1550, 1600)

Each parameter is tested independently while keeping others fixed. The algorithm finds values within 1.5× of the best result and picks the center of that range.

### Phase 4: Cycling Refinement
- Fine-tunes exposure and gain with tighter ranges (±200 for exposure, ±1 for gain)
- Allows parameters to re-adjust based on changes from Phase 3

### Phase 5: Verification
- Applies final settings
- Runs 3 verification rounds
- Reports average stability and detection rate
- Leaves optimal settings applied to camera

## Configuration

Edit these values at the top of `final_optimize.py`:

```python
# Camera IP address
LIMELIGHT_IP = '172.29.0.1'

# AprilTags to look for
TARGET_TAGS = [20, 24]

# Starting baseline settings
SAFE_SETTINGS = {
    'exposure': 3200,
    'sensor_gain': 8.2,
    'fiducial_refine_method': 1,
    'black_level': 20,
    'sharpening': 0,
    'red_balance': 1280,
    'blue_balance': 1500,
}
```

## Output Parameters

The optimizer tunes these Limelight parameters:

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| `exposure` | Camera exposure time (×0.01ms) | 2400-4000 |
| `sensor_gain` | Sensor amplification | 6-10 |
| `fiducial_refine_method` | AprilTag corner refinement algorithm | 0-3 |
| `black_level` | Black level offset | 15-25 |
| `sharpening` | Image sharpening amount | 0-0.15 |
| `red_balance` | White balance - red channel | 1180-1380 |
| `blue_balance` | White balance - blue channel | 1400-1600 |

## Stability Measurement

Stability is measured as the **standard deviation of Z-axis position** (in millimeters) over multiple samples. Lower values = more stable readings.

| Stability | Quality |
|-----------|---------|
| < 1mm | Excellent ⭐ |
| 1-2mm | Very Good |
| 2-3mm | Good |
| 3-5mm | Acceptable |
| > 5mm | Needs improvement |

## Example Output

```
============================================================
🎯 LIMELIGHT QUICK OPTIMIZER
============================================================

📡 PHASE 1: Detecting tag and baseline...
   ✅ Detected Tag 24
   📊 Baseline: 0.79mm stability (100% detection)

🔍 PHASE 2: Coarse parameter search...
   ✅ Best so far: exp=3200 gain=9 (0.58mm)

🎛️  PHASE 3: Fine-tuning secondary parameters...
   ✅ Refine method: Decode
   ✅ Black level: 20
   ✅ Sharpening: 0.15
   ✅ Red balance: 1280
   ✅ Blue balance: 1500

🔄 PHASE 4: Cycling refinement...
   ✅ Refined: exp=3000 gain=9

✅ PHASE 5: Verification...
   Round 1: 0.76mm (100%)
   Round 2: 0.72mm (100%)
   Round 3: 0.87mm (100%)

============================================================
🏆 OPTIMIZATION COMPLETE
============================================================

⏱️  Time: 69.5 seconds
🏷️  Tag: 24

📊 Final Stability: 0.78mm (100% detection)

⚙️  Optimal Settings:
   exposure: 3000
   sensor_gain: 9
   fiducial_refine_method: 2 (Decode)
   black_level: 20
   sharpening: 0.15
   red_balance: 1280
   blue_balance: 1500

✅ Settings applied to camera!
============================================================
```

## Algorithm: Range-Center Selection

Instead of simply picking the single best value for each parameter, the optimizer uses a "range-center" approach:

1. Test all values for a parameter
2. Find the best result
3. Identify all values within 1.5× of the best (the "good range")
4. Pick the **center** of that range

This produces more robust settings that are less sensitive to minor variations in lighting, distance, or angle.

## Tips for Best Results

1. **Stable mounting** - Ensure the camera is rigidly mounted
2. **Good lighting** - Consistent ambient lighting helps
3. **Tag visibility** - Tag should be clearly visible, not at extreme angles
4. **Run multiple positions** - Test at different distances/angles to find universal settings
5. **Start with safe settings** - If detection fails, increase exposure in SAFE_SETTINGS

## API Reference

The tool communicates with Limelight via HTTP REST API:

- **Settings**: `POST http://<IP>:5807/update-pipeline` with JSON body
- **Results**: `GET http://<IP>:5807/results` returns detection data

## License

MIT License - Feel free to use and modify for your FTC team!

## Credits

Developed by FRC Team 6603 - Guild of Gears

---

*Built with ❤️ for the FIRST robotics community*
