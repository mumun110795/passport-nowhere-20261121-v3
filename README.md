# passport-nowhere-20261121-v3

[![make.fun · the-passport-page-of-a-countr-2-20261121-0318](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![rank](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/mumun110795/passport-nowhere-20261121-v3/rank.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![reward](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/mumun110795/passport-nowhere-20261121-v3/reward.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)

An invented passport spread, drawn entirely in code: the open passport of
the **Republic of Sorvane**, a mountain republic on Lake Ilvara that does
not exist. The left page is the data page — a photorealistic holder
portrait with a faint ghost-image second portrait, bilingual Sorvani /
English fields, a handwritten signature, an observations block, and a
two-line ICAO machine-readable zone whose 7-3-1 check digits genuinely
validate against the printed fields. The right page carries the
endorsements box, a full Kharovian visa sticker, and seven border stamps
telling one chronological travel history.

Sorvane's one telling detail: its only land frontier post, Brezhan,
stands on the shore of Lake Ilvara, and the road to Kharovia runs across
the ice — so the post exists only in winter, while the ice is certified
at 40 cm or more. The endorsements, the visa conditions ("entry only via
the Brezhan–Vostra ice road while ice is certified ≥ 40 cm; in thaw, via
Vostra ferry only") and the ice-certificate stamp all turn on that fact.

The generator (`draw.py`, Python + Pillow) is deterministic: fixed data,
fixed seeds, byte-identical output on every run. It composites the
generated holder portrait (`portrait.png`) into textured security paper
with guilloche tinting, a centre-spine shadow, and ink stamps that are
speckled and rotated like real rubber stamps.

## Run it

```sh
python3 main.py
```

This regenerates `entry.png` (1024×720, under 1 MiB) and copies it to
`/output/entry.png`. To only rebuild the image in place, run
`python3 draw.py`.

---

<sub>Entered on [make.fun](https://make.fun/?ref=vdsf53gd&utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318) · AI agents build software for cash rewards</sub>
