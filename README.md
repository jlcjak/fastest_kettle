<div align="center">

# The Fastest Kettle

### 1 litre of water. 29.5 seconds. Four junkyard car batteries and a PCB.

![boil](https://img.shields.io/badge/1%20L%20boiled%20in-29.5%20s-eb6834?style=for-the-badge)
![power](https://img.shields.io/badge/power-~15%20kW-2a78d6?style=for-the-badge)
![current](https://img.shields.io/badge/current-400%20A-52514e?style=for-the-badge)
![voltage](https://img.shields.io/badge/pack-48%20V-52514e?style=for-the-badge)

**[▶ Watch the build (YouTube)](https://www.youtube.com/watch?v=0xC_Ypls5T8)** · **[𝕏 thread](https://x.com/jlcjak/status/2119211496416907727)**

<img src="img/boil_29s.gif" width="420" alt="The real boil: the floor goes white instantly, boiling at 29.5 s">

*The real thing, sped up 4×: 1050 ml of 12 °C water, contactor closes, the whole floor goes white within half a second,
and it's boiling at **29.5 s**.*

</div>

---

## The idea in 20 seconds

A kitchen kettle is about 2 kW, so a litre takes ~3 minutes. The Impulse Labs battery cooktop does ~10 kW and boils
a litre in ~40 s. We wanted to beat it for a few hundred euros.

1. **Get ~15 kW.** Four used car batteries in series (48 V) happily dump 400 A for half a minute. That's literally what their
   "cold cranking amps" rating tests.
2. **Turn it into heat without melting anything.** One long copper track on an **aluminium-core PCB**: 18 mm wide,
   2.7 m long, **65 mΩ**. The copper faces down (dry), the bare aluminium faces up (wet), and a 3 kV dielectric sits between them.
3. **Make the board the pot.** A stainless cake ring siliconed on top. That's it. That's the kettle.

<img src="img/pair_heater.jpg" width="100%" alt="CAD render of the heater board next to the real boards, copper side and aluminium side">

## From CAD to the real thing

<img src="img/pair_kettle.jpg" width="100%" alt="CAD of the kettle next to the real kettle tied to a steel frame">
<img src="img/pair_jig.jpg" width="100%" alt="Printed centering blocks in CAD and holding the ring in real life">
<img src="img/pair_terminal.jpg" width="100%" alt="Lug bolted straight onto the heater pad, CAD and real">

*Top: the kettle. In real life we skipped the printed feet and lashed it to a steel frame. Middle: 4 push-fit printed
blocks hold the cake ring centred while the silicone cures. Bottom: the 35 mm² cable lug bolts straight onto the
heater pad. No busbars.*

## Results (Nov 7 2026, outdoors, 12 °C)

<img src="img/result_boil_times.png" width="100%" alt="Bar chart of boil times">

| | |
|---|---|
| Water | **1050 ml**, weighed, starting at ~12 °C |
| Time to first boil | **29.5 s** |
| Average power into the water | **~13.1 kW** (387 kJ / 29.5 s) |
| Peak measured power | **14.8 kW** (38 V × 389 A) |
| Simulated, same water and batteries | 28.1 s, close enough to be happy |
| Simulated, good batteries, 1 L from 15 °C | 24 s |

Then we tried a second run straight away, with a voltmeter on the pack and a clamp meter on the cable. It never boiled.

<table>
<tr>
<td width="50%"><img src="img/real_meters.jpg" alt="Second run with voltmeter and clamp meter in view"></td>
<td width="50%"><img src="img/real_attempt2_steam.jpg" alt="Lots of steam, no rolling boil"></td>
</tr>
</table>

<img src="img/result_pack_collapse.png" width="100%" alt="Power, voltage and current falling over 60 s on the second run">

At switch-on the pack's own resistance was already ~31 mΩ (four healthy batteries are ~20 mΩ), and it kept climbing as
they ran down. After a minute it was making 4 kW. **The kettle was fine; the batteries were the bottleneck.** A fresher bank (or a
12S2P LiPo pack) is the obvious next step.

## How it went

<table>
<tr>
<td width="50%"><img src="img/real_parts.jpg" alt="Four car batteries, two heater boards and 35 mm² cable"><br>
<sub><b>The whole bill of materials.</b> Four used car batteries, the heater boards (white = copper side, grey = water side), 3 m of welding cable.</sub></td>
<td width="50%"><img src="img/real_sanded.jpg" alt="Sanded aluminium side"><br>
<sub><b>Sanded for bubbles.</b> Someone who knows boiling warned us about a steam layer cooking the board. Roughening the surface gives bubbles more places to start and buys ~10-30 % extra margin.</sub></td>
</tr>
<tr>
<td><img src="img/real_silicone.jpg" alt="Silicone bead laid on the board"><br>
<sub><b>Silicone bead</b>, ring down onto the printed blocks, then a second pass on the inside seam.</sub></td>
<td><img src="img/real_cure_printer.jpg" alt="Kettle curing inside a 3D printer chamber"><br>
<sub><b>Cured overnight hanging inside a 3D printer</b>, because silicone cures faster warm. 20 → 29 °C.</sub></td>
</tr>
<tr>
<td><img src="img/real_contactors.jpg" alt="Two EV200 contactors"><br>
<sub><b>Two EV contactors in series</b> on a hand-held button. If one welds shut, the other still opens.</sub></td>
<td><img src="img/real_batteries.jpg" alt="Batteries wired in series with quick-release clamps"><br>
<sub><b>48 V of car batteries</b> from four different brands, quick-release clamps, ~400 A.</sub></td>
</tr>
<tr>
<td><img src="img/real_test_site.jpg" alt="Test site with the kettle on a steel frame"><br>
<sub><b>Test day.</b> Outside, on a steel frame, away from anything that burns.</sub></td>
<td><img src="img/real_food.jpg" alt="Souvlaki and eggs cooking on the kettle"><br>
<sub><b>Afterwards: a 12 kW frying pan.</b> Souvlaki, eggs, and yes, spaghetti. Lots of steam, very fast.</sub></td>
</tr>
<tr>
<td><img src="img/real_dry_run.jpg" alt="Board flipped and powered dry"><br>
<sub><b>Then we ran it dry on purpose.</b> The white soldermask goes yellow, then brown…</sub></td>
<td><img src="img/real_burnt.jpg" alt="Burnt copper spiral"><br>
<sub><b>…and the copper lets go.</b> With an already tired pack it took longer than expected, but the silkscreen says <i>NEVER POWER WITHOUT WATER</i> for a reason.</sub></td>
</tr>
</table>

## Why the board survives 15 kW (with water in it)

- **Boiling is an absurdly good coolant.** 28 W/cm² leaves the aluminium with only ~13 °C of superheat (~113 °C). The copper
  on the dry side runs ~145 °C.
- **The real enemy is the boiling crisis.** Past ~111-144 W/cm², the bubbles merge into a steam blanket and the floor runs
  away. We sit at 28 W/cm² on average and ~50 W/cm² at the worst spots, about **2× margin**. Sanding adds a bit more.
- **Hot spots were simulated on the real copper and fixed.** A 2D current-flow solve found 5× hot spots at sharp corners.
  Rev 2.2 rounds them off.

Full write-up with the plots: **[docs/heater_physics.md](docs/heater_physics.md)**.

## Build your own

- **Everything you need, with links and prices: [docs/BUILD.md](docs/BUILD.md)**
- **Total:** about €300, including the batteries and a 5-board PCB order.

The short version:
1. Order the heater (gerbers are in [`heater/`](heater)).
2. Sand the wet side.
3. Silicone on a Ø28 cm cake ring, using the printed jig. **Use aquarium silicone**: it handles the heat better and is the
   food-safe choice. We used a generic one and it's rated only to 120 °C.
4. Bolt the lugs straight onto the pads. Printed feet are included, but the 35 mm² cables are stiff and can drag or tip the
   kettle, so you may still need to tie it down. We skipped the feet and lashed the board to a steel frame.
5. Wire 4 car batteries through **two EV200 contactors in series** on a hold-to-run button.

## What's in here

```
heater/       KiCad board + Python generator (the spiral is code, not hand-drawn) + JLCPCB gerbers
cad/step/     STEP models: assembly, exploded view, heater, ring, feet, jig, lug, terminal
cad/stl/      print-ready: feet (PC) and centering-jig blocks (PLA/PETG)
cad/freecad/  parametric FreeCAD scripts that build all of the above
sim/          boil-time model, layer temperatures, 2D current-flow / hot-spot solver, result plots
docs/         build guide + parts list, heater physics
```

The heater is fully parametric: change the track width, resistance target or diameter in `heater/gen_heater.py`, then run
`python3 heater/gen_heater.py` (it needs KiCad's `pcbnew` Python module).

## ⚠️ Safety

This is not a product. It's a 48 V, 400 A, 15 kW experiment.

- **Never power it without water.** At full power a dry board is ruined within seconds, and there's **no thermal
  cut-off** in this version. Your thumb on the button is the only off switch.
- **Fit a fuse** (500 A, rated ≥ 80 V DC) at the battery. A short on four car batteries is 2,000-3,000 A, and the heater
  current never gets high enough to blow it, so it's only there for wiring faults.
- **Two contactors in series**, so one welded contact can't leave it stuck on. Hold-to-run only.
- Stand back, wear eye protection, and keep it outdoors or well ventilated. Lead-acid batteries vent hydrogen.
- Never pour water onto a hot, dry plate (Leidenfrost: it can stay in film boiling and keep heating).
- Tie it down, and lift it by the board, never by the siliconed ring.

## Credits

Built by [@jlcjak](https://x.com/jlcjak). Designed with the help of an AI hardware agent
(Backplane): sizing, heater layout, the boiling and current-flow sims, and the CAD.

Released under the [MIT License](LICENSE). Build it, break it, beat the time.
