# 🎯 Limelight AprilTag Calibration Optimizer

An automated calibration tool for optimizing AprilTag detection stability on Limelight 3A cameras. Starts from Limelight's official recommended settings and systematically dials them in for your specific setup.

## Overview

This tool automatically tunes Limelight camera parameters to minimize position jitter when detecting AprilTags. It begins with Limelight's documented best practices (black_level=0, high gain, low exposure) and uses a 6-phase optimization process with a "range-center" algorithm to find robust settings.

**Developed for FRC Team 6603 — Guild of Gears, 2025-2026 season.**

## Files

| File | Description |
|------|-------------|
| `optimize.py` | **Main optimizer** — starts from official recommended settings |
| `old_final_optimize.py` | Legacy optimizer (old approach: high exposure, low gain) — kept for reference |

## Features

- ⚡ **~2.5 minute optimization** — complete 6-phase calibration
- 🎯 **3-5mm position stability** — Z-depth standard deviation
- 🔄 **Auto-detection** — finds Limelight via ping (172.28.0.1 / 172.29.0.1)
- 🧠 **Range-center algorithm** — picks the middle of good plateaus, not noisy single bests
- 📋 **Official baseline** — starts from Limelight's documented recommendations
- 📈 **Verbose mode** — optional detailed output for every test point

## Requirements

- Python 3.x
- `requests` library (`pip install requests`)
- Limelight 3A connected via USB (auto-detected via ping)
- AprilTag visible to camera (Tags 20 or 24, family 36h11, 165.1mm)

## Usage

### Basic Usage
```bash
python optimize.py
```

### Verbose Mode (see every test point)
```bash
python optimize.py -v
```

## How It Works

The optimizer runs through 6 phases:

### Phase 1: Apply Recommended Baseline & Detect Tag
- Applies Limelight's official recommended settings (gain=15, black_level=0, moderate exposure)
- Auto-detects which AprilTag is visible (Tag 20 or 24)
- Measures baseline stability

### Phase 2: Find Minimum Usable Exposure
- Coarse sweep: 400–2800 in steps of 400
- Finds the lowest exposure with >80% detection, then picks best stability
- Fine sweep: ±300 around winner in steps of 100
- Uses range-center selection for robustness

### Phase 3: Optimize Sensor Gain
- Coarse sweep: 5, 10, 15, 20, 25, 30
- Fine sweep: ±3 around winner in steps of 1
- Range-center selection

### Phase 4: Tune Secondary Parameters
Tests each independently while keeping others fixed:
1. **Refine Method** — None, Subpixel, Decode, Pose (picks lowest jitter)
2. **Black Level** — 0, 5, 10, 15 (range-center)
3. **Sharpening** — 0, 0.05, 0.1, 0.15, 0.2 (range-center)

### Phase 5: Joint Exposure + Gain Refinement
- Tests a 3×3 grid around current best (±200 exposure, ±2 gain)
- Catches interactions between the two most impactful parameters

### Phase 6: Verification
- 3 rounds of 100 samples each
- Reports average stability and detection rate
- Leaves optimal settings applied to camera

## Configuration

Edit these values at the top of `optimize.py`:

```python
# IPs to try (auto-detected via ping)
CANDIDATE_IPS = ['172.28.0.1', '172.29.0.1']

# AprilTags to look for
TARGET_TAGS = [20, 24]

# Official recommended starting point
RECOMMENDED_BASELINE = {
    'black_level': 0,
    'sensor_gain': 15,
    'exposure': 1200,
    'fiducial_refine_method': 1,  # Subpixel
    'sharpening': 0,
    'red_balance': 1200,
    'blue_balance': 1600,
}
```

## Output Parameters

| Parameter | Description | Typical Optimized Range |
|-----------|-------------|------------------------|
| `exposure` | Camera exposure time | 2000–2800 |
| `sensor_gain` | Sensor amplification | 15–25 |
| `black_level` | Black level offset | 0–10 |
| `fiducial_refine_method` | Corner refinement (0=None, 1=Subpixel, 2=Decode, 3=Pose) | 0–1 |
| `sharpening` | Image sharpening | 0.05–0.15 |
| `red_balance` | White balance — red channel | 1200 (untouched) |
| `blue_balance` | White balance — blue channel | 1600 (untouched) |

## Stability Measurement

Stability is measured as the **standard deviation of Z-axis depth** (in millimeters) from `t6t_cs` over multiple samples. Lower = more stable.

| Stability | Quality |
|-----------|---------|
| < 1mm | Excellent ⭐ |
| 1–2mm | Very Good |
| 2–3mm | Good |
| 3–5mm | Acceptable |
| > 5mm | Needs improvement |

## Example Output

```
============================================================
🎯 LIMELIGHT 3A OPTIMIZER — Official Recommended Start
============================================================
   Strategy: black_level=0, high gain, lowest usable exposure

📡 PHASE 1: Applying recommended baseline & detecting tag...
   ✅ Detected Tag 20
   📊 Recommended baseline: 5.35mm stability (100% detection)

🔦 PHASE 2: Finding minimum usable exposure (gain=15, black=0)...
   📉 Lowest reliable exposure: 400
   🏆 Best stability exposure:  2400 (4.0mm)
   ✅ Exposure: 2400  (4.0mm)

📈 PHASE 3: Optimizing sensor gain...
   ✅ Gain: 20  (4.0mm)

🎛️  PHASE 4: Tuning secondary parameters...
   ✅ Refine method: None
   ✅ Black level: 10
   ✅ Sharpening: 0.15

🔄 PHASE 5: Joint exposure + gain refinement...
   ⭐ Improved! exp=2400 gain=22 → 3.8mm

✅ PHASE 6: Verification (3 rounds of 100 samples)...
   Round 1: 4.63mm (100%)
   Round 2: 4.06mm (100%)
   Round 3: 4.36mm (100%)

============================================================
🏆 OPTIMIZATION COMPLETE
============================================================

⏱️  Time: 148.9s
🏷️  Tag:  20

📊 Baseline (recommended):  5.35mm
📊 Final stability:         4.35mm  (100% detection)
📈 Improvement:             1.00mm better (19%)

⚙️  Optimal Settings:
   exposure:               2400
   sensor_gain:            22
   black_level:            10
   fiducial_refine_method: 0 (None)
   sharpening:             0.15
   red_balance:            1200
   blue_balance:           1600

✅ Settings applied to camera!
============================================================
```

## Algorithm: Range-Center Selection

Instead of picking the single best value (which may be noisy), the optimizer uses a "range-center" approach:

1. Test all values for a parameter
2. Find the best stability result
3. Identify all values within 1.5× of the best (the "plateau")
4. Pick the **center** of that plateau

This produces more robust settings that are less sensitive to measurement noise, lighting changes, or distance variations. Across multiple runs, this consistently lands on similar values.

## Tips for Best Results

1. **Stable mounting** — ensure the camera is rigidly mounted during calibration
2. **Consistent lighting** — avoid flickering lights or changing sunlight
3. **Tag visibility** — tag should be clearly visible, not at extreme angles
4. **Run multiple times** — settings should converge across runs; average the results
5. **Lower resolution** — can improve pipeline latency with minimal stability impact

## API Reference

The tool communicates with Limelight via HTTP REST API on port 5807:

- **Apply settings**: `POST http://<IP>:5807/update-pipeline` with JSON body
- **Read results**: `GET http://<IP>:5807/results` returns detection data including `t6t_cs` (target pose in camera space)

## License

MIT License — feel free to use and modify for your team!

## Credits

Developed by FRC Team 6603 — Guild of Gears

---

*Built with ❤️ for the FIRST robotics community*
