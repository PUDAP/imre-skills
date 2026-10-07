# Staged robot workflows with camera checkpoints

Use this pattern when a physical workflow must pause for an image, inspection, or operator decision before moving labware again.

## Design

1. Query every live machine registry first. Do not invent a `capture` PUDA command when no camera edge is registered.
2. Split the workflow at the physical checkpoint:
   - **Stage 1:** move/process the item, clear other equipment from the shared workspace, release clamps as required, and place the robot at the requested camera-safe observation pose. Leave the item at a known station.
   - **Checkpoint:** capture and verify the image, or obtain explicit operator approval.
   - **Stage 2:** retrieve the item and complete the return/next transfer.
3. Keep each PUDA stage independently valid and resumable. Record the expected item, cap/gripper, robot, and gantry state at the boundary.
4. Use an orchestrator with `set -euo pipefail` when automatic continuation is wanted. The capture command must occur between stage runs. If image capture fails or produces no valid file, the script must exit before Stage 2, leaving the item at the documented checkpoint rather than moving it without evidence.
5. When the user asks to create but not execute, run only static validation (`puda protocol validate`, `bash -n`) and explicitly report that neither stage, camera capture, nor machine motion ran.

## Capturing from a camera already in use

A USB camera may be intentionally held by a long-running FFmpeg publisher. Do not stop that publisher merely to open `/dev/video0` again. Identify the existing stream and extract a frame from its media server instead.

For a MediaMTX RTSP stream:

```bash
mkdir -p /home/puda/captures
ffmpeg -hide_banner -loglevel error \
  -rtsp_transport tcp \
  -i rtsp://127.0.0.1:8554/ipcam \
  -frames:v 1 \
  -y "/home/puda/captures/checkpoint_$(date -u +%Y-%m-%d_%H%M%S).jpg"
```

Verify that the output exists and is a valid image before Stage 2. Prefer a timestamped filename that states the item, checkpoint, and that capture occurred before return. FFmpeg can emit H.264 missing-reference/decode warnings yet still exit successfully and write a usable JPEG, so do not decide from stderr alone: require a non-empty file and validate its image stream with `ffprobe`. For transient stream-start corruption, retry capture to a temporary file and atomically rename only after validation. Use [../scripts/capture_rtsp_frame.sh](../scripts/capture_rtsp_frame.sh) for this checked, three-attempt pattern.

## Telegram approval gate

For an image checkpoint delivered through Telegram:

1. Stage 1 may finish by moving the robot to a documented observation pose above the station, while the processed item remains at the station.
2. Capture and validate the frame, then deliver it with `MEDIA:/absolute/path.jpg` in the same message that states the measured robot/capper positions and asks approval.
3. The Stage 1 wrapper may print the `MEDIA:` path and an approval warning, but it must exit without invoking Stage 2.
4. Do not treat script completion, image delivery, or a quoted prior message as approval. Run Stage 2 only after a new explicit user response such as `approve`.
5. After approval, run only the return suffix and independently verify the destination pose/state.

## Visual state classification

When the checkpoint asks whether a tube is capped or uncapped, assess the captured pixels separately from command execution:

1. Load the exact captured frame with an image-analysis tool; do not classify from the Stage 1 log, `decap`/`cap` success response, filename, or expected workflow state.
2. Use a three-way result:
   - **UNCAPPED** — the tube mouth/opening is clearly visible and no cap covers it.
   - **CAPPED** — a cap is clearly visible covering/seated on the tube opening.
   - **UNCERTAIN** — the opening is occluded, too small, blurred, badly lit, outside frame, or visually ambiguous.
3. State the concrete visible cue and confidence limitation in one or two sentences. Never upgrade `UNCERTAIN` using protocol completion as supporting visual evidence.
4. Deliver the image and classification before asking for return approval. Approval authorizes only Stage 2; it does not retroactively validate the visual classification.
5. If the user requests visual proof but the current observation pose or camera angle cannot show the tube mouth, leave the tube at the checkpoint and report `UNCERTAIN`; do not move it merely to manufacture a confident answer unless the user authorizes a revised inspection pose.

## Safety and evidence

- A successful Stage 1 response establishes the software boundary; independently query robot/gantry pose when the checkpoint pose matters.
- A camera frame proves only what is visibly discernible. Do not infer cap presence, clamp state, or tube identity when the image does not clearly show it.
- Record Stage 1 run ID, image path/timestamp, Stage 2 run ID, and final edge-mediated poses separately.
- For approval-gated workflows, never place Stage 2 in an automatically running wrapper.
