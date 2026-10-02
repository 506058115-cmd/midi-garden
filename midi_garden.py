#!/usr/bin/env python3
"""Compose a small, reproducible MIDI loop without external packages."""

import argparse
import random
import secrets
import struct
from pathlib import Path


KEYS = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5,
        "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}
SCALES = {"major": (0, 2, 4, 5, 7, 9, 11), "minor": (0, 2, 3, 5, 7, 8, 10)}
PROGRESSIONS = {"major": (0, 4, 5, 3), "minor": (5, 3, 0, 4)}
MELODY_PATTERNS = ((0, 2, 3, 5, 7), (0, 1, 3, 4, 6, 7), (0, 2, 4, 5, 6), (0, 1, 2, 4, 6))
TICKS_PER_BEAT = 480


def vlq(value):
    if not 0 <= value <= 0x0FFFFFFF:
        raise ValueError("MIDI delta is outside the four-byte range")
    encoded = [value & 0x7F]
    while value > 0x7F:
        value >>= 7
        encoded.append((value & 0x7F) | 0x80)
    return bytes(reversed(encoded))


def meta(kind, data):
    return b"\xff" + bytes((kind,)) + vlq(len(data)) + data


def note(events, start, end, pitch, velocity):
    events.append((start, 3, bytes((0x90, pitch, velocity))))
    events.append((end, 2, bytes((0x80, pitch, 0))))


def compose(seed, key, mode, tempo, bars):
    rng = random.Random(seed)
    root = KEYS[key]
    scale = SCALES[mode]
    bar_ticks = TICKS_PER_BEAT * 4
    eighth = TICKS_PER_BEAT // 2
    progression = PROGRESSIONS[mode]
    events = [
        (0, 0, meta(0x03, f"MIDI Garden seed {seed}".encode("ascii"))),
        (0, 0, meta(0x51, (60_000_000 // tempo).to_bytes(3, "big"))),
        (0, 0, meta(0x58, bytes((4, 2, 24, 8)))),
        (0, 1, bytes((0xC0, 0))),
    ]
    melody_notes = [60 + root + offset + octave * 12 for octave in range(2) for offset in scale]
    previous = 60 + root

    for bar in range(bars):
        start = bar * bar_ticks
        degree = progression[bar % len(progression)]
        chord = [60 + root + scale[(degree + step) % 7] + 12 * ((degree + step) // 7) for step in (0, 2, 4)]
        for pitch in chord:
            note(events, start, start + bar_ticks - 24, pitch, 48)
        bass = 36 + root + scale[degree]
        note(events, start, start + TICKS_PER_BEAT * 2 - 24, bass, 68)
        note(events, start + TICKS_PER_BEAT * 2, start + bar_ticks - 24, bass, 60)

        pattern = MELODY_PATTERNS[int(rng.random() * len(MELODY_PATTERNS))]
        for slot in pattern:
            nearby = [pitch for pitch in melody_notes if abs(pitch - previous) <= 7]
            choices = nearby or melody_notes
            pitch = choices[int(rng.random() * len(choices))]
            previous = pitch
            hit = start + slot * eighth
            note(events, hit, hit + eighth * 3 // 4, pitch, 76 + int(rng.random() * 25))

    end_tick = bars * bar_ticks
    events.append((end_tick, 4, meta(0x2F, b"")))
    events.sort(key=lambda item: (item[0], item[1]))
    track = bytearray()
    last_tick = 0
    for tick, _, data in events:
        track.extend(vlq(tick - last_tick))
        track.extend(data)
        last_tick = tick
    return b"MThd" + struct.pack(">IHHH", 6, 0, 1, TICKS_PER_BEAT) + b"MTrk" + struct.pack(">I", len(track)) + track


def main():
    parser = argparse.ArgumentParser(description="Compose a seedable short MIDI loop with melody, chords, and bass.")
    parser.add_argument("--seed", type=int, help="recreate a loop with a seed from 0 to 4294967295")
    parser.add_argument("--key", choices=KEYS, default="C", help="root key (default: C)")
    parser.add_argument("--mode", choices=SCALES, default="major", help="major or natural minor")
    parser.add_argument("--tempo", type=int, default=96, help="tempo in quarter notes per minute (60–180)")
    parser.add_argument("--bars", type=int, default=8, help="loop length in bars (2–16)")
    parser.add_argument("--output", type=Path, help="MIDI filename (default: midi-garden-SEED.mid)")
    args = parser.parse_args()
    if not 60 <= args.tempo <= 180:
        parser.error("--tempo must be between 60 and 180")
    if not 2 <= args.bars <= 16:
        parser.error("--bars must be between 2 and 16")
    if args.seed is not None and not 0 <= args.seed <= 0xFFFFFFFF:
        parser.error("--seed must be between 0 and 4294967295")

    seed = args.seed if args.seed is not None else secrets.randbits(32)
    output = args.output or Path(f"midi-garden-{seed}.mid")
    data = compose(seed, args.key, args.mode, args.tempo, args.bars)
    try:
        with output.open("xb") as midi_file:
            midi_file.write(data)
    except FileExistsError:
        parser.exit(2, f"midi-garden: refusing to overwrite {output}\n")
    except OSError as error:
        parser.exit(2, f"midi-garden: {error}\n")
    print(f"Wrote {output} ({args.key} {args.mode}, {args.tempo} BPM, seed {seed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
