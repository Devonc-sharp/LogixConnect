# Splash concepts kept for later

Three animated splash concepts (each an 8-second loop, 1280 × 720), kept to build into the app's splash after v2.0.
They are design-canvas files (`.dc.html`): the markup and the CSS keyframes are plain HTML/SVG/CSS and carry straight
over to the splash; only the `<x-dc>` wrapper and the `support.js` line belong to the canvas.

1. **Inspection pass** (`1-inspection-pass.dc.html`): a bottle with the Logix Connect label rides the conveyor under an
   In-Sight-style camera; the strobe fires, a green PatMax-style box locks onto the label, PASS (score 98.6, label OK,
   fill 98 %) comes up, the bottle moves on and the wordmark appears.
2. **Controller power-up** (`2-controller-power-up.dc.html`): a CompactLogix 1769-L33ER front panel boots. OK flashes
   red then green, I/O amber then green, the four-character display runs TEST, I/O, PROG, RUN, the key turns PROG → RUN,
   RUN lights, and the wordmark slides in.
3. **Scan sweep** (`3-scan-sweep.dc.html`): a full startup routine of five rungs (Power_OK → Controller_OK → IO_Ready →
   Load_TMR → App_Ready); a green scan bar sweeps top to bottom, each rung energises as it passes, App_Ready lights, the
   ladder dims and the wordmark takes the screen.

Colours: ink #1d2733, paper #e9ebee, dark #101418 / #14181d, green #2f8f4e (day) and #3ddc5a (dark). Type: Inter (the
app's Segoe UI on Windows) and JetBrains Mono.
