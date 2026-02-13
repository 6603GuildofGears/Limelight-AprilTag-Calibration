# Team 6603 — Guild of Gears — Judging Q&A Guide
## DECODE 2025-2026 Season | Robot 2 (Decode v2)

> **How to use this document:** Each section matches an award from the Judging Question Bank. Under each question, you'll find a polished answer based on your actual code, commits, and team story. Use these as talking points — adjust wording to sound natural for your team. Highlighted sections marked with ⭐ are your strongest points for that award.

---

# 🏆 CONTROL AWARD (Primary Target)

### Required Criteria Checklist (from DECODE Manual Table 6-8):
- [x] **Required 1A** — Hardware/software control components on robot ✅
- [x] **Required 1B** — Which challenges each component solves ✅
- [x] **Required 1C** — How each component/system works ✅
- [x] **Required 2** — Hardware/software solutions using external feedback and control ✅
- [x] **Encouraged 3** — Control solutions work consistently during most matches ✅
- [x] **Encouraged 4** — Discuss reliability and how solution could be improved ✅
- [x] **Encouraged 5** — Engineering process to develop control solutions, with lessons learned ✅

---

## Q1: What sensors and hardware did your team use on your robot?

**Answer:**

Our robot uses six types of sensors and specialized hardware:

1. **Limelight 3A Camera** — Our primary targeting sensor. It detects AprilTags on the goals (Tag 20 for Blue, Tag 24 for Red) and gives us the horizontal (tx) and vertical (ty) angle offsets. We use tx for turret auto-aim and ty for distance calculation.

2. **REV Hub IMU** — We use the built-in IMU for field-oriented drive. It gives us the robot's heading so the driver can push the stick forward and the robot always drives away from them, no matter which direction the robot faces.

3. **Magnetic Touch Sensor** — This is mounted on our turret. When the turret rotates past a known position, the magnet triggers the sensor and we auto-reset the encoder to recalibrate. This prevents encoder drift during long matches.

4. **Drive Motor Encoders (4×)** — All four mecanum drive motors (DcMotorEx) have encoders. We use them for odometry through PedroPathing and for consistent speed control.

5. **Flywheel Motor Encoder** — Our shooter flywheel runs in velocity mode (RUN_USING_ENCODER) so we can target precise RPMs. We calculate tick speed from RPM using the formula: `ticks_per_second = RPM × 28 / 60`.

6. **Turret Motor Encoder** — The turret motor tracks position in encoder ticks. We found the safe operating range through testing: -275 to +630 ticks. We also compensate for the 131:20 gear ratio (6.55:1) between the motor and turret.

**What worked:** The Limelight + turret PID system works reliably for auto-aim. The mag sensor calibration solved our encoder drift problem.

**What did not work:** ⭐ Early on, we struggled with the Limelight camera not being consistently configured between power cycles. The exposure, gain, and other settings would change. So Olivia wrote a custom Python calibration tool that automatically optimizes 7 camera parameters in about 60-70 seconds, achieving sub-millimeter position stability. We open-sourced it on GitHub.

---

## Q2: Can you talk about the code used on the robot?

**Answer:**

Our codebase is organized into a **pipeline architecture** — modular classes that separate hardware initialization from control logic:

**Pre-programmed libraries and outside resources we used:**
- **PedroPathing** — An open-source FTC path-following library for autonomous movement. We forked the Quickstart template and added our custom code on top.
- **EasyOpenCV** — For camera-based ball detection using our Logitech webcam.
- **FTC SDK** (v11.1) — The standard FIRST-provided libraries.
- **Ultralytics YOLOv8** + **PyTorch** — For training our ball detection machine learning model (off-robot, then converted to TensorFlow Lite for on-robot deployment).

⭐ **Custom libraries and routines we wrote:**

1. **`Motor_Pipeline.java`** — Hardware abstraction for all motors. Handles initialization, directions, encoder modes, and a unified `SetPower()` function for mecanum drive.

2. **`Servo_Pipeline.java`** — Hardware abstraction for hood, flicker, and spindexer servos.

3. **`Limelight_Pipeline.java`** — Complete vision abstraction with methods like `hasBlueGoal()`, `getBlueGoalX()`, `getRedGoalX()`, `hasTarget()`, and `displayTelemetry()`. Supports filtering by specific AprilTag ID.

4. **`Sensor.java`** — Magnetic sensor abstraction with `isMagPressed()` for turret calibration.

5. **`ShooterLookup.java`** — ⭐ A custom lookup table with **linear interpolation** across 13 calibrated distance points (16.875" to 127.5"). Given a distance, it returns the exact RPM and hood servo position needed. We built this table by physically measuring and tuning at each distance.

6. **`TurretConfig.java`** / **`AprilTagCentererConfig.java`** — Live-tunable configuration classes using Pedro Pathing Panels. We can adjust PID gains, deadbands, and filter coefficients in real-time without redeploying code.

7. **`WiffleBallPipeline.java`** (611 lines) — Our OpenCV pipeline that detects purple and green wiffle balls using HSV color filtering, contour analysis, silver bar reflection filtering, and 9-position ramp pattern matching.

8. **`Limelight AprilTag Calibration Optimizer`** — A standalone Python tool we wrote and open-sourced that automatically tunes 7 Limelight camera parameters using a "range-center" algorithm across 5 optimization phases.

---

## Q3: Which software solutions worked, which did not, and why?

**Answer:**

**What worked:**
- ⭐ **Turret Auto-Aim PID** — Our PID controller with low-pass filtering and gear-ratio compensation works consistently in matches. We tuned KP=0.0004, KI=0.01, KD=0.05 with a deadband of 0.25°.
- **Distance-based shooter tuning** — The ShooterLookup table with linear interpolation means we hit accurate shots from 17 inches to over 10 feet.
- **The 3-shot automated sequence** — Timer-based state machine fires all three balls reliably with fail-safe timeouts.
- **Field-oriented drive** — Drivers loved it because they can focus on strategy instead of robot orientation.

**What did NOT work (and what we learned):**
- **Our first autonomous attempts** — You can see in our commits: "Auto Hopefully" (Nov 19), "Sadly, auto's are not poppin" (Nov 19), "Before disaster, 12/1/25" (Dec 1). We struggled with PedroPathing tuning and path accuracy early on.
- **Simple proportional turret control** — Before adding full PID, the turret would oscillate around the target. We needed derivative and integral terms plus a low-pass filter to smooth it out.
- **Limelight configuration** — Settings would change between power cycles, causing inconsistent tracking. That's why we built the automated calibration tool.
- **Flicker servo reliability** — On Robot 2, the flickers sometimes don't complete their motion. We added timeout fail-safes so the shooting sequence never gets stuck, and we're still tuning the Axon Mini servos.

---

## Q4: How did your team capture their learnings with what worked and what did not work?

**Answer:**

We used **Git version control with descriptive commit messages**. Looking at our commit history, you can literally see our journey:

- "working rango code" → "Rango with auto aim" (first Limelight tracking)
- "pedro mabye work" → "Pedro is working, time for tuning" → "Path's are pretty good" 
- "Sadly, auto's are not poppin, but we have a simulator, pretty dope" (built a simulator to debug)
- "calabration for matchs" → "YOOOOOOOOOOO" (when calibration finally clicked)
- "Close, but not great" → "HOLY CRAP THIS WORKS" (PedroPathing on Robot 2)

We also captured learnings through our code comments and multiple iterations. For example, our ball detection went through 5 major versions (v1 through v5) with specific debug scripts for each problem: `debug_masks.py`, `debug_splitting.py`, `debug_clustering.py`, `debug_red_edge.py`, etc. Each debug script targeted a specific failure mode we observed.

For the Limelight calibration, we documented the entire algorithm in our README with phase descriptions, a parameter table, and quality benchmarks.

---

## Q5: What criteria or process did your team use to determine if a component is working or not working?

**Answer:**

We used **measurable criteria**, not just "it looks right":

- **Turret tracking**: We built a custom `Turret_PID_Assistant.java` that measures overshoot, settling time, zero-crossings, and peak error. It even has an auto-tune mode that adjusts PID gains based on response characteristics.
- **Shooter accuracy**: We measured distance to goal using trigonometry from the Limelight ty angle, then recorded the RPM and hood position that made shots at each distance. We built a 13-point lookup table from these measurements.
- **Limelight stability**: Our calibration tool measures **standard deviation of Z-axis position** in millimeters. Under 1mm = excellent, 1-2mm = very good. We targeted sub-millimeter.
- **Ball detection**: We went through 3 rounds of development with test images and videos. Round 3 alone has an `Output/` folder with 77 test result images. For the ML model, we measured mAP50 (mean average precision at 50% IoU).
- **Servo reliability**: We added `servoTolerance = 0.05` checks — the code verifies the servo actually reached its target position before proceeding.

---

## Q6: How does your robot know where it is on the field? Control acquisition of scoring elements? Measure and control motor speed?

**Answer:**

**Where it is on the field:**
We use a **multi-sensor localization approach**:
- **PedroPathing library** with drive encoder odometry for autonomous path following
- **Limelight 3A** AprilTag detection — identifies goal tags (Blue=20, Red=24) and calculates distance using trigonometry: `distance = (targetHeight - cameraHeight) / tan(mountAngle - ty)` where camera height is 11.125", mount angle is 24°, and target height is 29.5"
- **IMU heading** for field-oriented reference frame
- Early commits show we experimented with "fused odometry" combining multiple sources

**Control acquisition of scoring elements:**
- **Intake motor** brings balls into the spindexer at 75% power
- **Spindexer servo** oscillates back and forth during intake to distribute balls evenly across 3 positions (0, 0.375, 0.75)
- ⭐ **Ball detection camera** (planned integration) uses our YOLO ML model to identify green vs purple balls, allowing selective shooting of only our alliance color. We manually labeled 388+ images, trained a YOLOv8 model achieving 99% accuracy, and converted to TensorFlow Lite for on-robot inference.
- The turret auto-aims at the goal while the spindexer indexes balls for sequential firing

**Measure and control motor speed:**
- **Flywheel** runs in `RUN_USING_ENCODER` velocity mode. We command specific tick speeds calculated from target RPM: `tickSpeed = RPM × 28 / 60`
- The `Flywheel_Hood_Tuner.java` displays real-time RPM vs target RPM with error readout for tuning
- Target RPM dynamically adjusts based on distance from 3000-4750 RPM via the ShooterLookup table

---

## Q7: What enhancements did your team program to assist the drivers during Teleop?

**Answer:**

⭐ We built an extensive suite of driver assists:

1. **Auto-Aim Turret** — The turret automatically tracks the goal using Limelight AprilTag detection with PID control. The driver just drives; the turret stays locked on target. Toggle with Y button on gamepad2.

2. **"Whiparound" Recovery** — When the turret hits a physical limit while tracking, it automatically whips to the other side at high speed and reacquires the target. The driver never has to manually manage turret position.

3. **Distance-Based Shot Tuning** — The Limelight calculates distance-to-goal in real-time. The ShooterLookup table automatically sets the optimal RPM and hood angle. Drivers don't need to adjust power or angle manually.

4. **One-Button 3-Shot Sequence** — Press RBumper2 and all 3 balls fire automatically with proper timing — flywheel spin-up → flicker fire → spindexer advance → repeat. Each shot has timeout fail-safes.

5. **Kill Switch** — LBumper2 immediately stops any shooting sequence, resets servos, and kills the flywheel. Safety first.

6. **Field-Oriented Drive** — Uses IMU heading so forward always means "away from driver." Press Back button to recalibrate heading.

7. **Scan-When-Lost** — If the turret loses sight of the goal, it automatically starts scanning in the direction the target was last seen to reacquire it.

8. **Real-Time Telemetry Dashboard** — Comprehensive telemetry showing drive mode, Limelight status, turret position/power, PID values, shot state, and servo positions.

9. **Driver Rotation Compensation** — When the driver rotates the robot, feedforward is applied to the turret to counteract the chassis rotation and keep the turret pointed at the goal.

---

## Q8: What were your team's design goals for the Auto period?

**Answer:**

Our autonomous goals evolved throughout the season:

1. **Score in the high goal** — Using pre-programmed paths to drive to shooting positions and auto-fire using the same shooting sequence from TeleOp.

2. **Consistent pathing** — We adopted PedroPathing for reliable, repeatable autonomous movement. We went through extensive tuning (forward velocity, strafe velocity, zero-power acceleration, turn tuning) to calibrate the path follower to our specific robot.

3. **Alliance flexibility** — We built separate auto routines for Red and Blue alliances, with the turret auto-switching between AprilTag 20 (Blue goal) and Tag 24 (Red goal).

Our biggest challenge was getting autonomous working reliably. The commit history shows multiple attempts in November 2025, with messages like "Auto Hopefully," "prayin they work tmrw," and "Sadly, auto's are not poppin." We even built a simulator to debug paths before testing on the field. By late January 2026, we had "working shoot auto" confirmed.

---

## Q9: What specific game tasks was your team trying to improve or solve with your control system?

**Answer:**

⭐ **Accurate shooting from any distance and angle:**
The DECODE game requires scoring balls into elevated goals. The distance changes constantly during a match. Our control system solves this by:
- Calculating exact distance using Limelight trigonometry
- Looking up the correct RPM and hood angle from a 13-point calibrated table with linear interpolation
- Auto-aiming the turret so the driver only has to drive and press shoot

⭐ **Ball color selection (planned):**
The game uses green and purple balls. You only want to shoot your alliance color. Our ML ball detection system (YOLOv8 trained on 388+ labeled images, 99% accuracy, converted to TensorFlow) will enable the robot to identify ball colors in the spindexer and selectively fire only the correct ones.

**Consistent shooting across battery levels:**
We implemented voltage compensation so motor performance doesn't degrade as the battery drains during a match.

**Turret management:**
The turret has physical limits from its wiring. Our "whiparound" logic automatically handles limit situations instead of requiring driver intervention.

---

## Q10: Describe the engineering process your team followed to develop your robot's most complex autonomous routine or control feature.

**Answer:**

⭐ Our most complex control feature is the **auto-aiming turret with distance-based shooter tuning**. Here's the engineering process:

**Step 1: Basic Control (Nov 17-18, 2025)**
Max and Josh started with simple proportional control — turret power proportional to Limelight tx error. It was jittery and oscillated.

**Step 2: PID Implementation (Nov 18 - Feb 3)**
We added full PID control with integral anti-windup and a low-pass filter (alpha=0.8) to smooth noisy Limelight readings. We compensated for the 131:20 gear ratio so the PID operates in degrees, not raw encoder ticks.

**Step 3: Automated Tuning Tool (Feb 7)**
We built `Turret_PID_Assistant.java` — a tool that measures turret response to step inputs, counts zero-crossings (oscillations), measures overshoot and settling time, and suggests PID gain adjustments. It even has an auto-tune mode.

**Step 4: Advanced Tracking (Feb 6)**
Josh added "whiparound" logic with overshoot detection, tanh-scaled proportional response, and driver rotation compensation feedforward. This is in `AprilTag_Centerer_Red.java`.

**Step 5: Distance Calibration (Feb 5)**
We physically measured shot results at 13 different distances and recorded the optimal RPM and hood position at each. We encoded this into `ShooterLookup.java` with linear interpolation between points.

**Biggest obstacle:** Limelight configuration instability. The camera settings would change, causing tracking to degrade. Olivia solved this by writing the automated calibration optimizer.

**How we measured reliability:** The PID assistant measures quantitative metrics — overshoot in degrees, number of zero-crossings, settling time in seconds. The Limelight calibrator measures position standard deviation in millimeters.

**Did it work for our team?** Yes. When calibrated, the turret locks onto the goal within 0.25° in under a second, and the distance-based shooting makes shots from 17" to over 10 feet consistently.

---

# 💡 THINK AWARD

## Can you describe your team's brainstorming process?

We started by analyzing the DECODE game — balls need to be scored in elevated goals from varying distances. We brainstormed three main approaches:

1. **Fixed-angle shooter** — Simple but can only score from one distance
2. **Adjustable hood + fixed turret** — Better range but requires the driver to aim the whole robot
3. **Full turret with auto-aim + variable hood + distance-based tuning** — Most complex but allows scoring from anywhere on the field while the driver focuses on driving

We chose option 3 because the trade-off analysis showed that even though it was harder to build and program, the competitive advantage of shooting from any position would be worth it. The robot can score while moving — the driver never has to stop to aim.

## How did your team improve your robot throughout the season?

We iterated aggressively. Our Git history shows 40+ team commits across 3+ months:

- **Nov 17**: First code commit — basic drive and shooting
- **Nov 18**: Added Limelight, AprilTag detection, auto-aim — 8 commits in ONE DAY
- **Nov 19-22**: Autonomous attempts, voltage compensation, shooting sequence
- **Dec 1-15**: PedroPathing integration, camera distance calculations
- **Dec 15-20**: Started Robot 2 (Decode v2) — complete drive rebuild through 10+ iterations in one day
- **Jan-Feb**: Shooter tuning, PID refinement, ball detection ML, "whiparound" turret logic

We also **started Robot 2** when we realized Robot 1's mechanical design had limitations. We ported all the software to the new platform while improving it. Robot 2 commits show the same struggle-and-iterate pattern: "maybe work" → "maybey v2" → "drive kinda" → "wokring Drive" → "HOLY CRAP THIS WORKS."

## What was your team's biggest challenge?

Getting the turret auto-aim AND the autonomous to work at the same time. The turret needed precise PID tuning, but the autonomous also needed precise path following. Both require encoder accuracy and Limelight reliability. When one broke, it often affected the other. We eventually solved it by modularizing our code into separate pipelines so each system could be tested and tuned independently.

## How does your team define their Engineering process?

Code → Test → Observe → Debug → Iterate. We wrote specific debug tools for each subsystem: `TurretLimitFinder` (find safe encoder range), `Turret_PID_Assistant` (measure PID response), `Flywheel_Hood_Tuner` (tune shooting parameters via Panels), and multiple ball detection debug scripts. We believe in **measuring, not guessing**.

---

# 🔗 CONNECT AWARD

## Does your team reach out to STEM professionals?

Our mentors bring professional experience to the team:
- **Marcus** is a CAD professional who mentors our design and 3D printing work. Marshal works closely with him on CAD designs.
- **Ken** works in software professionally and guides the programming team on best practices like version control, modular architecture, and testing methodologies.

## What skills have your team learned?

- **Max & Josh**: Java programming, PID control theory, sensor fusion, path planning, Git version control
- **Olivia**: Python, machine learning (PyTorch, YOLO, TensorFlow conversion), computer vision (OpenCV), automated optimization algorithms, camera calibration
- **Marshal**: CAD design, 3D printing, mechanical engineering
- **Alexander**: Mechanical assembly, hardware integration

## How does your team work with other FIRST teams?

We open-sourced our Limelight AprilTag Calibration tool on GitHub for any FTC team to use. The README includes full documentation, usage instructions, and explanation of the range-center algorithm. We believe in giving back to the FIRST community.

---

# 🌍 REACH AWARD

## Does your team perform any type of community service or outreach?

*(Note: Fill in your actual outreach activities here. If you've done demos at schools, community events, or helped start younger teams, describe those.)*

We open-sourced tools for the broader FTC community:
- **Limelight AprilTag Calibration Optimizer** — Published on GitHub with full documentation, any FTC team can use it to optimize their Limelight settings in under 70 seconds.

---

# 💰 SUSTAIN AWARD

## How does your team fundraise or raise funds?

*(Fill in your specific fundraising activities.)*

## How are responsibilities assigned?

Our team has clear roles:
- **Max & Josh** — Lead programmers (robot code, TeleOp, autonomous)
- **Olivia** — Machine learning & vision systems (ball detection, Limelight calibration)
- **Marshal** — CAD design and 3D printing (with mentor Marcus)
- **Alexander** — Mechanical building and assembly
- **Ken (mentor)** — Software guidance and engineering process
- **Marcus (mentor)** — CAD expertise and design guidance

## How do you help grow team members into future leaders?

Each team member owns their domain. Olivia went from no ML experience to training a YOLOv8 model achieving 99% accuracy. Max and Josh self-taught PID control theory and implemented it with auto-tuning. Alexander contributes critical building skills without needing to code. We believe everyone's contribution matters equally.

---

# 🎨 INNOVATE AWARD

## Is there an aspect of your robot that you consider unique or creative?

⭐ **Yes — three things stand out:**

1. **The auto-aiming turret with distance-based shot tuning** — Most FTC teams have fixed shooters. Our turret automatically tracks the goal AND adjusts RPM and hood angle based on distance. The driver just drives and presses shoot.

2. **The "whiparound" turret logic** — When the turret hits a physical limit (wiring constraints), it automatically whips 180° the other direction and reacquires the target. No driver intervention needed.

3. **Machine learning ball detection** — We took 388+ photos, manually labeled every ball green or purple, trained a YOLOv8 model to 99% accuracy, and converted it to TensorFlow for on-robot deployment. This lets the robot selectively shoot only our alliance color.

## What risks did your team identify with your design?

- **Turret complexity** — A rotating turret adds failure points (wiring, encoder drift, mechanical backlash). We mitigated this with the mag sensor auto-calibration and encoder limit protection.
- **Limelight dependency** — If the camera loses connection or misconfigures, the auto-aim fails. We mitigated this with the automated calibration tool and scan-when-lost fallback.
- **Ball detection timing** — ML inference takes time. We designed the system so the robot can still shoot manually without ball detection active.
- **Two-robot strategy** — Building Robot 2 mid-season was a risk (divides effort). We managed it by porting tested code from Robot 1 to Robot 2 using Git.

---

# 🏅 DESIGN AWARD

## How did your team come up with the overall design of your robot?

We designed around the shooting challenge — the DECODE game rewards accurate scoring from distance. Our design philosophy was **"let software solve what hardware can't"**:
- Fixed-angle shooters require repositioning → we added a turret and auto-aim
- Manual shooting is inconsistent → we added distance-based RPM/hood tuning
- Wrong-color balls waste shots → we added ML ball detection

## How does your team balance functionality, simplicity, and reliability?

Our pipeline architecture keeps things modular. Each subsystem (motors, servos, Limelight, sensors) has its own Java class. If one breaks, others keep working. The shooting sequence has timeout fail-safes on every step. The turret has hard position limits AND a slow-zone near limits. We add complexity only where it gives a measurable competitive advantage.

---

# 🏆 JUDGES' CHOICE AWARD

## Tell us your story — how is your team making a difference through FIRST?

We're Team 6603, Guild of Gears. This season, we challenged ourselves to build something genuinely advanced — a turret-based shooter with auto-aim, distance-compensated shooting, and machine learning ball detection. We went through two complete robot builds, three rounds of ball detection development, and wrote custom tools that we open-sourced for the FTC community.

Our commit messages tell the real story: "prayin they work tmrw," "Sadly auto's are not poppin," "Before disaster 12/1/25," and then — "YOOOOOOOOOOO," "HOLY CRAP THIS WORKS." Every struggle taught us something. We built debug tools instead of guessing. We measured instead of hoping. And we shared what we learned.

## What is the one thing we did not ask about that you most want the Judges to know?

⭐ We built our own **machine learning pipeline from scratch**. Olivia took 388+ photos of balls on ramps, manually labeled every single one as green or purple with a custom labeling tool, trained a YOLOv8 model using PyTorch and Ultralytics, achieved 99% detection accuracy, and converted it to TensorFlow Lite for on-robot use. Most FTC teams use pre-trained models or simple color thresholds. We did real ML — data collection, labeling, training, validation, and deployment. We plan to use this to selectively shoot only our alliance color, giving us a strategic advantage.

## In what ways is your team unique?

We write **testing and diagnostic tools**, not just robot code. We built:
- A PID auto-tuner that measures response and suggests gains
- A camera calibration optimizer that tunes 7 parameters across 5 phases
- A ball labeling GUI tool for creating ML training data
- A custom ball detection pipeline that went through 5 major versions
- A turret limit finder to safely determine physical constraints

Most teams write one TeleOp and one Auto. We built an entire ecosystem of tools to make our robot better.

---

# 📋 PORTFOLIO CONTENT (for Control Award — REQUIRED)

*Copy this content into your Canva portfolio:*

## A. Hardware and Software Control Components

| Component | Type | Description |
|-----------|------|-------------|
| Limelight 3A | Camera/Sensor | AprilTag detection for goal targeting |
| REV Hub IMU | Sensor | Robot heading for field-oriented drive |
| Magnetic Touch Sensor | Sensor | Turret home position calibration |
| Drive Encoders (4×) | Sensor | Mecanum drive odometry |
| Flywheel Encoder | Sensor | Velocity-controlled shooting (RPM) |
| Turret Encoder | Sensor | Turret position tracking |
| Logitech Webcam | Camera | Ball color detection (ML-based) |
| Turret PID Controller | Software | Automated goal tracking |
| ShooterLookup Table | Software | Distance-based RPM & hood tuning |
| Limelight Calibrator | Software | Automated camera optimization |
| WiffleBallPipeline | Software | Real-time ball color classification |
| YOLOv8 ML Model | Software | 99% accuracy ball detection |

## B. Challenges Each Component Solves

| Component | Challenge Solved |
|-----------|-----------------|
| Limelight + Turret PID | Scoring from any field position without manual aiming |
| ShooterLookup + Hood Servo | Consistent shots across 17" to 127" range |
| IMU + Field-Oriented Drive | Intuitive driving regardless of robot orientation |
| Mag Sensor | Turret encoder drift during extended matches |
| Ball Detection ML | Selecting only alliance-color balls to shoot |
| Limelight Calibrator | Inconsistent camera settings between power cycles |
| Voltage Compensation | Motor performance degradation as battery drains |

## C. How Each Component Works

**Turret Auto-Aim:** Limelight detects AprilTag on goal → reports tx (horizontal error in degrees) → low-pass filter smooths noise (α=0.8) → PID controller with gear-ratio compensation (131:20) calculates motor power → turret motor tracks target within 0.25° deadband.

**Distance-Based Shooting:** Limelight ty angle → trigonometric distance calc: `distance = (29.5" - 11.125") / tan(24° - ty)` → ShooterLookup table with linear interpolation across 13 calibrated points → sets RPM (3000-4750) and hood position (0.0-0.55).

**Ball Detection ML Pipeline:** 388 photos manually labeled → YOLO format conversion → YOLOv8s training (200 epochs, Apple Silicon GPU) → 99% mAP50 accuracy → TensorFlow Lite export → on-robot inference via EasyOpenCV → sorted bottom-to-top for selective shooting.

**Limelight Calibration:** 5-phase optimization: baseline → coarse grid search (exposure × gain) → fine-tune secondary params → cycling refinement → verification. Uses "range-center" algorithm — picks the middle of the robust range, not just the single best value.

---

*Last updated: February 12, 2026*
*Generated from analysis of: Robot1-Quickstart, Robot2-Decode-v2, Limelight-AprilTag-Calibration, Ball-Detection (rounds 1-3), MachineLearning repos*
