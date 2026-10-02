# midi-garden

Plant a seed and get a short MIDI loop with a melody, chord bed, and bass. It is written with Python's standard library, so no synth or music package is needed to create the file. Import the `.mid` into a DAW or notation app to hear and edit it.

## Use

Requires Python 3.8+.

```sh
python midi_garden.py --seed 42
python midi_garden.py --key Eb --mode minor --tempo 82 --bars 8 --output dusk.mid
```

The default is an eight-bar, 4/4 loop at 96 BPM in C major. Keys are C, C#, D, Eb, E, F, F#, G, Ab, A, Bb, and B. Tempo is 60–180 BPM; length is 2–16 bars. The same settings and seed recreate the same MIDI data. Without `--output`, the file is named `midi-garden-SEED.mid`; existing files are never overwritten. Playback sound depends on the instrument in your music software.

## License

MIT
