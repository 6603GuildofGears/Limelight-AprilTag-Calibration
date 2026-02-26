#!/usr/bin/env python3
"""
🎯 LIMELIGHT 3A OPTIMIZER — Starting from Official Recommended Settings
Starts with Limelight's documented best practices (black_level=0, high gain,
low exposure) and dials in from there.

Strategy:
  1. Apply official recommended baseline (gain=15, black_level=0)
  2. Find the minimum exposure that still detects reliably
  3. Sweep gain around that point for best stability
  4. Fine-tune secondary params (refine method, sharpening)
  5. Final tight pass on exposure+gain together
  6. Verify

Usage:
    python optimize_from_recommended.py           # Normal output
    python optimize_from_recommended.py -v        # Verbose output
"""

import requests
import time
import statistics
import sys

# ============================================================
# CONFIGURATION
# ============================================================
CANDIDATE_IPS = ['172.28.0.1', '172.29.0.1']

def find_limelight():
    """Ping candidate IPs and return the first one that responds."""
    import subprocess
    for ip in CANDIDATE_IPS:
        try:
            result = subprocess.run(
                ['ping', '-n', '1', '-w', '1000', ip],
                capture_output=True, timeout=3
            )
            if result.returncode == 0:
                print(f'   ✅ Found Limelight at {ip}')
                return ip
        except Exception:
            pass
    return None

LIMELIGHT_IP = find_limelight()
if LIMELIGHT_IP is None:
    print(f'   ❌ No Limelight found! Tried: {", ".join(CANDIDATE_IPS)}')
    print('   Make sure the Limelight is connected via USB.')
    sys.exit(1)

BASE = f'http://{LIMELIGHT_IP}:5807'

# Tags to look for (will auto-detect)
TARGET_TAGS = [20, 24]

# Official Limelight recommended starting point for AprilTags
# Source: https://docs.limelightvision.io/docs/docs-limelight/pipeline-apriltag/apriltags
#   - "Set Black Level to zero"
#   - "Set Gain to 15"
#   - "Reduce exposure to reduce tracking loss while in motion due to motion blur"
#   - "We recommend leaving [red/blue balance] untouched"
RECOMMENDED_BASELINE = {
    'black_level': 0,
    'sensor_gain': 15,
    'exposure': 1200,            # moderate starting point — will search lower
    'fiducial_refine_method': 1, # Subpixel (good default for accuracy)
    'sharpening': 0,
    'red_balance': 1200,         # factory-ish defaults
    'blue_balance': 1600,        # factory-ish defaults
}

VERBOSE = '-v' in sys.argv or '--verbose' in sys.argv

# ============================================================
# HELPERS
# ============================================================
def log(msg, force=False):
    if force or VERBOSE:
        print(msg)

def apply(settings):
    """Push settings to the Limelight pipeline."""
    try:
        requests.post(f'{BASE}/update-pipeline', json=settings, timeout=2)
        time.sleep(0.1)
        return True
    except Exception:
        return False

def measure(samples=40, target_tag=None):
    """
    Collect Z-depth readings and return (z_std_mm, detection_rate%, tag_id).
    Lower z_std = more stable pose.
    """
    z_vals = []
    detected_tag = None

    for _ in range(samples):
        try:
            r = requests.get(f'{BASE}/results', timeout=1)
            data = r.json()
            for fid in data.get('Fiducial', []):
                fid_id = fid.get('fID')
                if target_tag and fid_id != target_tag:
                    continue
                if not target_tag and fid_id not in TARGET_TAGS:
                    continue
                t6t = fid.get('t6t_cs', [])
                if t6t and len(t6t) >= 3:
                    z_vals.append(t6t[2])
                    detected_tag = fid_id
                    break
        except Exception:
            pass
        time.sleep(0.02)

    if len(z_vals) < 5:
        return 999, 0, detected_tag
    return statistics.stdev(z_vals) * 1000, len(z_vals) / samples * 100, detected_tag


def sweep(param, values, base, tag_id, samples=30):
    """
    Test each value for a parameter. Returns list of (value, z_std, det%).
    """
    results = []
    for val in values:
        s = base.copy()
        s[param] = val
        apply(s)
        z, det, _ = measure(samples, tag_id)
        results.append((val, z, det))
        log(f'      {param}={val}: {z:.1f}mm ({det:.0f}%)')
    return results


def pick_best(results, min_det=70):
    """
    From sweep results, pick the value with the lowest Z-std
    that still has acceptable detection rate.
    Falls back to min_det=40 if nothing above 70%.
    """
    good = [(v, z, d) for v, z, d in results if d >= min_det]
    if not good:
        good = [(v, z, d) for v, z, d in results if d >= 40]
    if not good:
        return None, 999
    best = min(good, key=lambda x: x[1])
    return best[0], best[1]


def pick_center_of_good(results, min_det=70):
    """
    Find the "plateau" of values within 1.5x of best z_std,
    then pick the center of that range for robustness.
    """
    good = [(v, z, d) for v, z, d in results if d >= min_det]
    if not good:
        good = [(v, z, d) for v, z, d in results if d >= 40]
    if not good:
        return None, 999

    best_z = min(z for _, z, _ in good)
    plateau = [v for v, z, d in good if z <= best_z * 1.5]
    if plateau:
        center = plateau[len(plateau) // 2]
        center_z = next(z for v, z, _ in results if v == center)
        return center, center_z
    else:
        best_val = min(good, key=lambda x: x[1])[0]
        return best_val, best_z


# ============================================================
# MAIN
# ============================================================
def main():
    REFINE_NAMES = {0: 'None', 1: 'Subpixel', 2: 'Decode', 3: 'Pose'}
    start_time = time.time()

    print('=' * 60)
    print('🎯 LIMELIGHT 3A OPTIMIZER — Official Recommended Start')
    print('=' * 60)
    print('   Strategy: black_level=0, high gain, lowest usable exposure')

    # ==========================================================
    # PHASE 1 — Apply recommended baseline & detect a tag
    # ==========================================================
    print('\n📡 PHASE 1: Applying recommended baseline & detecting tag...')
    apply(RECOMMENDED_BASELINE)
    z, det, tag_id = measure(80)

    # If nothing detected, try boosting exposure temporarily
    if det < 30:
        print(f'   ⚠️  Low detection ({det:.0f}%) — raising exposure to find a tag...')
        for try_exp in [2000, 3000, 4000]:
            alt = RECOMMENDED_BASELINE.copy()
            alt['exposure'] = try_exp
            apply(alt)
            z, det, tag_id = measure(60)
            if det >= 30:
                break

    if det < 30 or tag_id is None:
        print('   ❌ Cannot detect any target tag! Check camera view and TARGET_TAGS list.')
        return

    baseline_z = z
    print(f'   ✅ Detected Tag {tag_id}')
    print(f'   📊 Recommended baseline: {z:.2f}mm stability ({det:.0f}% detection)')

    best = RECOMMENDED_BASELINE.copy()
    best_z = z

    # ==========================================================
    # PHASE 2 — Find the minimum usable exposure
    # ==========================================================
    # Official advice: "Reduce exposure … stop once tracking reliability decreases."
    # We search from low to high and find the sweet spot.
    print('\n🔦 PHASE 2: Finding minimum usable exposure (gain=15, black=0)...')

    # Coarse sweep: 400 → 2800 in steps of 400
    exp_coarse = list(range(400, 3000, 400))
    results = sweep('exposure', exp_coarse, best, tag_id, samples=60)

    # Find the lowest exposure that still detects >80%
    reliable = [(v, z, d) for v, z, d in results if d >= 80]
    if reliable:
        # Among reliable, pick the one with best stability
        min_exp_val, min_exp_z = pick_best(reliable)
        # But also note the absolute minimum exposure that works
        lowest_working = min(v for v, z, d in reliable)
        print(f'   📉 Lowest reliable exposure: {lowest_working}')
        print(f'   🏆 Best stability exposure:  {min_exp_val} ({min_exp_z:.1f}mm)')
    else:
        # Fall back — use whatever detects
        min_exp_val, min_exp_z = pick_best(results, min_det=40)
        print(f'   ⚠️  No exposure had >80% detection. Best effort: {min_exp_val}')

    best['exposure'] = min_exp_val
    if min_exp_z < best_z:
        best_z = min_exp_z

    # Fine sweep around the winner
    exp_fine_center = best['exposure']
    exp_fine = sorted(set(
        e for e in range(max(100, exp_fine_center - 300),
                         exp_fine_center + 350, 100)
        if 100 <= e <= 5000
    ))
    print(f'   🔬 Fine-tuning exposure around {exp_fine_center}...')
    results = sweep('exposure', exp_fine, best, tag_id, samples=70)
    val, z = pick_center_of_good(results)
    if val is not None:
        best['exposure'] = val
        if z < best_z:
            best_z = z
    print(f'   ✅ Exposure: {best["exposure"]}  ({best_z:.1f}mm)')

    # ==========================================================
    # PHASE 3 — Sweep gain at the chosen exposure
    # ==========================================================
    print('\n📈 PHASE 3: Optimizing sensor gain...')

    # Coarse gain sweep: 5 → 30
    gain_coarse = [5, 10, 15, 20, 25, 30]
    results = sweep('sensor_gain', gain_coarse, best, tag_id, samples=60)
    val, z = pick_center_of_good(results)
    if val is not None:
        best['sensor_gain'] = val
        if z < best_z:
            best_z = z

    # Fine sweep around winner
    g = best['sensor_gain']
    gain_fine = sorted(set(
        round(x, 1) for x in
        [g - 3, g - 2, g - 1, g, g + 1, g + 2, g + 3]
        if 3 <= x <= 40
    ))
    print(f'   🔬 Fine-tuning gain around {g}...')
    results = sweep('sensor_gain', gain_fine, best, tag_id, samples=70)
    val, z = pick_center_of_good(results)
    if val is not None:
        best['sensor_gain'] = val
        if z < best_z:
            best_z = z
    print(f'   ✅ Gain: {best["sensor_gain"]}  ({best_z:.1f}mm)')

    # ==========================================================
    # PHASE 4 — Secondary parameters
    # ==========================================================
    print('\n🎛️  PHASE 4: Tuning secondary parameters...')

    # --- Refine method ---
    log('   Testing refine methods...')
    results = sweep('fiducial_refine_method', [0, 1, 2, 3], best, tag_id, samples=70)
    val, z = pick_best(results)
    if val is not None:
        best['fiducial_refine_method'] = val
        if z < best_z:
            best_z = z
    print(f'   ✅ Refine method: {REFINE_NAMES.get(best["fiducial_refine_method"], "?")}')

    # --- Black level (docs say 0, but let's verify a tiny bump doesn't help) ---
    log('   Testing black levels...')
    results = sweep('black_level', [0, 5, 10, 15], best, tag_id, samples=70)
    val, z = pick_center_of_good(results)
    if val is not None:
        best['black_level'] = val
        if z < best_z:
            best_z = z
    print(f'   ✅ Black level: {best["black_level"]}')

    # --- Sharpening ---
    log('   Testing sharpening...')
    results = sweep('sharpening', [0, 0.05, 0.1, 0.15, 0.2], best, tag_id, samples=70)
    val, z = pick_center_of_good(results)
    if val is not None:
        best['sharpening'] = val
        if z < best_z:
            best_z = z
    print(f'   ✅ Sharpening: {best["sharpening"]}')

    # ==========================================================
    # PHASE 5 — Joint exposure+gain refinement
    # ==========================================================
    print('\n🔄 PHASE 5: Joint exposure + gain refinement...')

    e = best['exposure']
    g = best['sensor_gain']

    exp_range = sorted(set(
        x for x in [e - 200, e, e + 200]
        if 100 <= x <= 5000
    ))
    gain_range = sorted(set(
        round(x, 1) for x in [g - 2, g, g + 2]
        if 3 <= x <= 40
    ))

    joint_results = []
    total = len(exp_range) * len(gain_range)
    count = 0
    for exp in exp_range:
        for gain in gain_range:
            count += 1
            s = best.copy()
            s['exposure'] = exp
            s['sensor_gain'] = gain
            apply(s)
            z, det, _ = measure(70, tag_id)
            joint_results.append((exp, gain, z, det))
            marker = '⭐' if det >= 80 and z < best_z else ''
            log(f'   [{count:2d}/{total}] exp={exp} gain={gain}: {z:.1f}mm ({det:.0f}%) {marker}')

    # Pick best combo
    good = [(e, g, z, d) for e, g, z, d in joint_results if d >= 80]
    if not good:
        good = [(e, g, z, d) for e, g, z, d in joint_results if d >= 50]
    if good:
        winner = min(good, key=lambda x: x[2])
        if winner[2] < best_z:
            best['exposure'] = winner[0]
            best['sensor_gain'] = winner[1]
            best_z = winner[2]
            print(f'   ⭐ Improved! exp={winner[0]} gain={winner[1]} → {winner[2]:.1f}mm')
        else:
            print(f'   ✅ No improvement found — keeping exp={best["exposure"]} gain={best["sensor_gain"]}')
    else:
        print(f'   ⚠️  Joint search had low detection — skipping')

    # ==========================================================
    # PHASE 6 — Verification
    # ==========================================================
    print('\n✅ PHASE 6: Verification (3 rounds of 100 samples)...')
    apply(best)
    time.sleep(0.3)

    verify = []
    for i in range(3):
        z, det, _ = measure(100, tag_id)
        verify.append((z, det))
        print(f'   Round {i+1}: {z:.2f}mm ({det:.0f}%)')

    final_z = statistics.mean([z for z, _ in verify])
    final_det = statistics.mean([d for _, d in verify])
    elapsed = time.time() - start_time

    # ==========================================================
    # REPORT
    # ==========================================================
    print('\n' + '=' * 60)
    print('🏆 OPTIMIZATION COMPLETE')
    print('=' * 60)
    print(f'\n⏱️  Time: {elapsed:.1f}s')
    print(f'🏷️  Tag:  {tag_id}')
    print(f'\n📊 Baseline (recommended):  {baseline_z:.2f}mm')
    print(f'📊 Final stability:         {final_z:.2f}mm  ({final_det:.0f}% detection)')
    improvement = baseline_z - final_z
    if improvement > 0:
        print(f'📈 Improvement:             {improvement:.2f}mm better ({improvement/baseline_z*100:.0f}%)')
    print(f'\n⚙️  Optimal Settings:')
    print(f'   exposure:               {best["exposure"]}')
    print(f'   sensor_gain:            {best["sensor_gain"]}')
    print(f'   black_level:            {best["black_level"]}')
    print(f'   fiducial_refine_method: {best["fiducial_refine_method"]} ({REFINE_NAMES.get(best["fiducial_refine_method"], "?")})')
    print(f'   sharpening:             {best["sharpening"]}')
    print(f'   red_balance:            {best["red_balance"]}')
    print(f'   blue_balance:           {best["blue_balance"]}')
    print(f'\n✅ Settings applied to camera!')
    print('=' * 60)


if __name__ == '__main__':
    main()
