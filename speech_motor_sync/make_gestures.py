"""Generate flat vector hand-gesture icons for the numerals 1-10.

The icons depict the common Chinese single-hand number gestures
(:_`一`=1 finger ... :_`十`=fist). They are drawn with pygame primitives
(round-capsule fingers over a rounded palm), supersampled 2x for smooth
edges, auto-centered, and saved with a transparent background as
``gestures/01.png``..``gestures/10.png``.

Run any time to (re)generate the icons::

    python make_gestures.py

Not fullscreen; safe to run in any environment. The paradigm loads these
files as-is -- replace them with real gesture photos (same names) if desired.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paradigm import DEFAULT_CHARACTERS, load_cjk_font  # noqa: E402

# --------------------------------------------------------------------------
# Canvas / style
# --------------------------------------------------------------------------
SUPER = 1600            # supersampled drawing resolution
FINAL = 800             # output resolution
OUT_DIR = Path(__file__).resolve().parent / "gestures"

MAIN = (244, 192, 155)   # hand / extended fingers
DARK = (202, 140, 105)   # folded fingers / shading

# Palm + wrist geometry (in SUPER coordinates). Compact palm, long fingers,
# with clear gaps between fingers so each digit reads as separate.
PALM = dict(x=525, y=820, w=550, h=400, r=150)   # center x = 800, top = 820
WRIST = dict(x=625, y=1170, w=350, h=260, r=130)

# Finger layout (left -> right): index, middle, ring, pinky. Wide spacing +
# thin fingers give visible negative-space gaps between digits.
FINGER_CX = {"index": 590, "middle": 730, "ring": 870, "pinky": 1010}
FINGER_LEN = {"index": 560, "middle": 580, "ring": 540, "pinky": 470}
FW = 82                  # finger width (gap between fingers = spacing - FW)
TW = 96                  # thumb width
BASE_Y = 870             # finger base (just inside palm top) so it merges
THUMB_PIVOT = (560, 1010)  # thumb root on the lower-left of the palm


# --------------------------------------------------------------------------
# Primitives
# --------------------------------------------------------------------------
def capsule(surf, color, p1, p2, width):
    """Draw a round-capped thick segment between two points."""
    pygame.draw.line(surf, color, p1, p2, width)
    radius = width // 2
    pygame.draw.circle(surf, color, (int(p1[0]), int(p1[1])), radius)
    pygame.draw.circle(surf, color, (int(p2[0]), int(p2[1])), radius)


def rrect(surf, color, x, y, w, h, r):
    """Draw a filled rounded rectangle."""
    pygame.draw.rect(surf, color, (x, y, w, h), border_radius=int(r))


def tilted_tip(cx, base_y, length, deg):
    """Tip point of a finger leaning `deg` degrees off vertical."""
    rad = math.radians(deg)
    return (cx + length * math.sin(rad), base_y - length * math.cos(rad))


# --------------------------------------------------------------------------
# Hand parts
# --------------------------------------------------------------------------
def draw_palm(surf):
    rrect(surf, MAIN, **PALM)
    rrect(surf, MAIN, **WRIST)


def finger_up(surf, name, deg=0.0):
    cx = FINGER_CX[name]
    length = FINGER_LEN[name]
    tip = tilted_tip(cx, BASE_Y, length, deg)
    capsule(surf, MAIN, (cx, BASE_Y), tip, FW)


def finger_folded(surf, name):
    cx = FINGER_CX[name]
    rrect(surf, DARK, cx - FW * 0.58, PALM["y"] - 34, FW * 1.16, FW * 0.92, FW * 0.45)


def thumb_up(surf):
    length = 360
    deg = 48.0  # lean to the left
    rad = math.radians(deg)
    tip = (THUMB_PIVOT[0] - length * math.sin(rad),
           THUMB_PIVOT[1] - length * math.cos(rad))
    capsule(surf, MAIN, THUMB_PIVOT, tip, TW)


def thumb_folded(surf):
    rrect(surf, DARK, PALM["x"] - 8, PALM["y"] + 165, 230, 98, 48)


def finger_hooked(surf, name):
    """Index finger curled into a hook (for the numeral 9)."""
    cx = FINGER_CX[name]
    knee = (cx, BASE_Y - 300)
    capsule(surf, MAIN, (cx, BASE_Y), knee, FW)            # lower segment
    curl = (cx + 160, BASE_Y - 300)
    capsule(surf, MAIN, knee, curl, FW)                    # curled top


def draw_fist(surf):
    """Closed fist: folded knuckles + thumb folded across."""
    for name in ("index", "middle", "ring", "pinky"):
        finger_folded(surf, name)
    # thumb lying across the knuckles
    rrect(surf, MAIN, PALM["x"] + 40, PALM["y"] + 20, 360, 104, 50)


# --------------------------------------------------------------------------
# Per-numeral configuration
# --------------------------------------------------------------------------
# Each entry: (thumb, {finger: "up"|"fold"}, special)
CONFIG = {
    1: ("fold", {"index": "up", "middle": "fold", "ring": "fold", "pinky": "fold"}, None),
    2: ("fold", {"index": "up", "middle": "up", "ring": "fold", "pinky": "fold"}, None),
    3: ("fold", {"index": "up", "middle": "up", "ring": "up", "pinky": "fold"}, None),
    4: ("fold", {"index": "up", "middle": "up", "ring": "up", "pinky": "up"}, None),
    5: ("up",   {"index": "up", "middle": "up", "ring": "up", "pinky": "up"}, None),
    6: ("up",   {"index": "fold", "middle": "fold", "ring": "fold", "pinky": "up"}, None),
    7: ("up",   {"index": "up", "middle": "up", "ring": "fold", "pinky": "fold"}, None),  # pinch
    8: ("up",   {"index": "up", "middle": "fold", "ring": "fold", "pinky": "fold"}, None),  # L / gun
    9: ("fold", {"index": "hook", "middle": "fold", "ring": "fold", "pinky": "fold"}, None),
    10: ("fold", {"index": "fold", "middle": "fold", "ring": "fold", "pinky": "fold"}, "fist"),
}


def draw_hand(surf, number):
    """Draw the hand silhouette for a given 1-based numeral."""
    thumb, fingers, special = CONFIG[number]
    draw_palm(surf)

    if special == "fist":
        draw_fist(surf)
    else:
        for name, state in fingers.items():
            if state == "up":
                if number == 7 and name in ("index", "middle"):
                    # lean index right, middle left -> converge into a pinch
                    finger_up(surf, name, deg=(14 if name == "index" else -14))
                elif number == 9 and name == "index":
                    finger_hooked(surf, name)
                else:
                    finger_up(surf, name)
            elif state == "fold":
                finger_folded(surf, name)
        if thumb == "up":
            thumb_up(surf)
        else:
            thumb_folded(surf)


# --------------------------------------------------------------------------
# Center + scale + save
# --------------------------------------------------------------------------
def content_bbox(surf):
    """Bounding box of all non-transparent pixels."""
    mask = pygame.mask.from_surface(surf)
    rects = mask.get_bounding_rects()
    if not rects:
        return None
    x0 = min(r.x for r in rects)
    y0 = min(r.y for r in rects)
    x1 = max(r.x + r.w for r in rects)
    y1 = max(r.y + r.h for r in rects)
    return x0, y0, x1, y1


def finalize(surf, out_path):
    """Translate content to center, then smoothscale to FINAL."""
    bbox = content_bbox(surf)
    if bbox is None:
        raise RuntimeError("Empty gesture surface")
    cx = (bbox[0] + bbox[2]) // 2
    cy = (bbox[1] + bbox[3]) // 2
    size = surf.get_width()
    canvas = pygame.Surface((size, size), pygame.SRCALPHA)
    canvas.blit(surf, (size // 2 - cx, size // 2 - cy))
    final = pygame.transform.smoothscale(canvas, (FINAL, FINAL))
    pygame.image.save(final, str(out_path))


def make_contact_sheet(paths, out_path):
    """Composite all icons into a labelled 5x2 grid for quick review."""
    cols, rows = 5, 2
    cell = FINAL + 40
    label_font = load_cjk_font(56, announce=False)
    sheet = pygame.Surface((cols * cell, rows * cell))
    sheet.fill((245, 245, 248))
    for i, path in enumerate(paths):
        icon = pygame.image.load(str(path)).convert_alpha()
        col = i % cols
        row = i // cols
        x = col * cell + 20
        y = row * cell
        sheet.blit(icon, (x, y))
        label = label_font.render(DEFAULT_CHARACTERS[i], True, (40, 50, 70))
        sheet.blit(label, (x + FINAL - label.get_width() - 10,
                           y + FINAL - label.get_height() - 8))
    pygame.image.save(sheet, str(out_path))


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    paths = []
    for number in range(1, len(DEFAULT_CHARACTERS) + 1):
        surf = pygame.Surface((SUPER, SUPER), pygame.SRCALPHA)
        draw_hand(surf, number)
        path = OUT_DIR / f"{number:02d}.png"
        finalize(surf, path)
        paths.append(path)
        print(f"Saved {path}")

    preview = Path(__file__).resolve().parent / "_preview_contact_sheet.png"
    make_contact_sheet(paths, preview)
    print(f"Preview contact sheet: {preview}")
    pygame.quit()


if __name__ == "__main__":
    main()
