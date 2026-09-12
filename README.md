# SentinelFace (hardened rewrite)

Continuous face-presence checking for a Windows laptop with a plain RGB
webcam (no IR sensor). Every N minutes it quietly checks that you're still
the one sitting there; if not, it locks the screen (Win+L). Every check is
logged to a local SQLite database.

This is a rewrite of a previous version of this project. See
"What was actually wrong before" below — it's important context if you were
told the earlier version was finished and production-ready.

## Setup (Windows)

1. Copy this whole folder anywhere on your machine (no drive-letter
   assumptions — it works from `C:\`, `D:\`, wherever).
2. Double-click **Setup.bat**. This creates a local `.venv` and installs
   dependencies (this step downloads TensorFlow via `tf-keras`/`deepface`,
   so it can take several minutes).
3. Double-click **EnrollFace.bat**. Look at the camera, press SPACE ~12-15
   times moving your head slightly between captures, ESC to cancel.
4. Double-click **OpenDashboard.bat** to confirm it works — try "Run Instant
   Verification" and watch it log a PASS.
5. Double-click **StartSentinelFace.bat** to run the background 15-minute
   monitor in your system tray.
6. Optional: **RegisterAutostart.bat** to have it start automatically at
   Windows logon (via Task Scheduler, no admin rights required).

Use `Set2MinTestMode.bat` / `Set15MinMode.bat` to switch the check interval
while testing.

## What was actually wrong before

Reading through the previous session's code line by line surfaced several
real problems — not style nitpicks, but things that mattered for whether
this tool actually does what it claims:

- **Fail-open on backend failure (the serious one).** The old recognizer
  wrapped face matching in a `try/except` that, on *any* error (missing
  library, model crash, whatever), fell back to "a face was detected in
  frame → treat it as a match." In a tool whose whole job is telling your
  face apart from someone else's, that's backwards: a dependency hiccup
  would let literally anyone's face pass. This rewrite raises a
  `RecognitionError` instead and the verification engine treats that as a
  **failed** check (and locks, if auto-lock is on).
- **Liveness score was computed but never checked.** The old `verifier.py`
  called the liveness analyzer, logged the number, and then ignored it when
  deciding pass/fail. So the "anti-photo-spoofing" feature did nothing. It's
  now actually part of the pass/fail decision (`liveness_required` in
  config.json).
- **A lenient "or" in the match logic.** The old code accepted a match if
  *either* your custom threshold OR DeepFace's own built-in (looser, ~0.68)
  threshold was satisfied — which quietly widened acceptance rather than
  tightening it. This version compares embeddings directly against your own
  threshold only, and requires at least `min_agreement` enrolled samples to
  agree, not just one.
- **DPAPI encryption existed but was never called.** `core/crypto.py` was
  written but nothing in the enrollment flow used it — raw, unencrypted face
  photos were being written to disk in two different folders while the
  writeup described the profile as "DPAPI encrypted." This version computes
  a face embedding at enrollment time, encrypts *that* with DPAPI, and never
  writes a raw face photo to disk at all.
- **Hardcoded `E:\` paths everywhere.** Config, database, and temp-file
  paths were hardcoded to `E:\SentinelFace\...`. Most laptops don't have an
  E: drive — this would simply crash for most people. Paths are now resolved
  relative to wherever you put the folder.
- **A dashboard that would crash on launch.** The Tkinter dashboard called
  `.pack(px=20, py=15)` and similar — `px`/`py` aren't real Tkinter options
  (`padx`/`pady` are), so this would raise a `TypeError` the first time
  anyone opened it. Fixed.
- **Two enrollment folders from an unrelated project.** The old
  `recognizer.py` looked in both `.sentinelface` and `.face-unlock`
  directories, and a batch file pointed at a Python venv living inside a
  *different* project folder (`E:\windows-face-unlock\.venv`). That's a sign
  two separate builds got tangled together. This version is self-contained.

I ran (not just wrote) targeted tests for the security-relevant logic in a
sandbox before handing this over: DPAPI round-trip, embedding save/load,
genuine-match-vs-impostor matching, a missing-backend failing closed instead
of open, and a static/no-motion frame sequence correctly failing the
liveness gate. I can't test against your actual webcam or Windows account
from here, so **please run EnrollFace.bat and a few instant-verify checks
yourself before turning on auto-lock and autostart**, and check
`sentinelface.log` / the dashboard's audit table if anything looks off.

## Honest limits of the liveness/anti-spoofing check

The original plan described five layers of anti-spoofing (blink detection,
head movement, micro-expression, monocular depth, challenge-response). None
of that was actually implemented in the code you were shown — only a raw
frame-difference number that, as noted above, wasn't even used. This rewrite
ships one real (but modest) liveness check: overall motion + eye-detection
flicker across the frame burst. It will stop a phone propped up showing a
single static photo. It will **not** reliably stop a video replay of your
face, or a photo moved slightly by hand. If you want a real trained
anti-spoofing model later, that's a well-scoped follow-up (e.g. a
passive-anti-spoofing ONNX model), but it's a separate piece of work from
what's here.

## Tuning

`config.json`:
- `confidence_threshold` — cosine distance cutoff, **lower = stricter**.
  Start at 0.60; if you get false rejects, loosen slightly (e.g. 0.65). If
  you're worried about false accepts, tighten (e.g. 0.50) and re-enroll with
  more varied angles/lighting.
- `min_agreement` — how many of your enrolled samples must independently
  match. 2 is a reasonable floor; raise it if you enrolled 15+ samples and
  want to be stricter.
- `liveness_required` / `liveness_min_score` — toggle/tune the liveness gate.
- `verify_required` — how many of the `verify_frames` frames must match to
  pass (majority voting).

## What this does *not* do: replace the Windows lock screen itself

This whole app runs **after** you're already logged in — it locks the
screen when you're not there, it doesn't unlock it. Read on for why the
pre-login "look at the lock screen and it logs you in" piece is a much
bigger, different project than what's above.
