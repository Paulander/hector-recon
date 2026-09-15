# Recorded network demonstration

Read-only presentation tooling, separate from the learner. The user-facing
deliverable is `Hector-Network-Demo.html`, with two silent 2560×1440, 24 fps MP4s.
The single HTML file embeds its data, rendering code and presenter notes and
does not need a server or network connection.

## Content and boundaries

The growth movie depicts seed 7's **saved continuation from 1,280 to 4,096
decisions**, not a freshly initialized actor. It shows 240 condition definitions
over that interval, with 64 live at the start. Birth/retirement times are derived
from condition histories; their live sets match all 27 archived checkpoints.
Shared definitions are folded across move bindings, and the center represents
the repeated action-support computation. Display coordinates and transition
fades are aesthetic, not recorded physical quantities. Endpoint weights are
not animated as if intermediate weights were available.

The execution movie shows development row 2, king separation (file,rank)=(2,1),
with the final saved actor choosing b2h2 (Rh2#). This example was chosen by
geometry from the already viewed development split. A normal and instrumented
frozen execution agree on action and resulting board and preserve learned state.
The trace includes every legal option and the selected option's descendants;
other option subtrees are omitted. Inspection of the eventual selected binding
is a presentation choice and does not enter action selection.

There are 28 recorded two-phase formal ticks. Moving dots interpolate actual
edge messages, not new microticks. The output terminal calls the environment
during the update of tick **25**, before confirming at tick 26. The runtime
requests the catalog, action choice and execution roots in order; no graph edge
or learned controller is invented between those roots. A green node is not an
assertion of checkmate or of positive reward. Node state gates whether a Boolean
condition with numeric activation 1 can contribute.

The depicted chess actor has randomly proposed shallow conditions and supplied
learning/pruning rules. It does not demonstrate graph-controlled development,
the separate recursive Boolean prototype, general chess mastery or a learned
hierarchy of goals. No new training or original checkpoint modification occurs.

## Reproduce

Use the historical dependencies and `PYTHONHASHSEED=0`. The exporter currently
uses explicit local paths to the archived seed, development pool and output
folder; adjust those paths when moving machines. Only load these trusted
project-generated checkpoints, never arbitrary pickle files.

1. `python scripts/demo/export_recorded_demo.py` — 120-second export limit.
2. `python scripts/demo/build_viewer.py` — builds the self-contained HTML.
3. `node scripts/demo/render_media.js --stills` — SVG stills and render checks.
4. `python scripts/demo/render_video.py growth`
5. `python scripts/demo/render_video.py trace`

Video export uses the same SVG scene renderer as the viewer. A restricted
Pillow renderer handles its line/circle/diamond/rectangle/text vocabulary and
streams frames to ffmpeg, preserving the scene coordinates and trace timing.
Each export has a 240-second limit, a two-core CPU affinity and two encoder
threads. Frames are not accumulated on disk or in memory. The SVG rasterizer's
automatic high-resolution resize proved slow; video uses the bounded Pillow
path instead. Static SVG and video stills were visually inspected.

Validation includes checkpoint transport/source checks, live-condition sets,
frozen action/learned-state equivalence, every displayed trace edge being a real
edge, finite renderer positions, script parsing and simulated-DOM checks of
mode switching, playback, seeking, inspection and keyboard controls. Browser
installation was unavailable, so a real browser interaction test was not run.
The videos provide a presentation fallback independent of browser scripting.
