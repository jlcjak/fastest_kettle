# Build guide

> ⚠️ **This is 48 V at 400 A with no thermal cut-off.** Read [Safety](../README.md#-safety) first. You build and use this
> entirely at your own risk.

## Parts list (what we actually bought, Nov 2026)

### The kettle
| Part | Qty | Notes | ~Cost |
|---|---|---|---|
| **Heater PCB** | 1 (5 min) | [`heater/heater_gerbers_jlcpcb.zip`](../heater/heater_gerbers_jlcpcb.zip). JLCPCB: **Aluminum**, 1 layer, 320 × 320 mm, 1.6 mm, 1 oz, 1 W/mK, HASL, **white mask / black silk**. "Confirm production file: yes". If they ask about "single net / no e-test", it's intentional. | $80 + ~$40 DHL |
| **Stainless cake ring Ø28 cm × 5 cm, fixed size** (not adjustable) | 1 | the pot wall, from a baking shop ([what we used](https://www.skroutz.gr/s/60244405/36140026-tserki-zacharoplastikis-%C3%B828x-y-5ek-anoxeidoto-strogylo.html)) | €8 |
| **Silicone sealant** | 1 tube | We used Den Braven 1001U (universal acetoxy, rated to only +120 °C). **Use aquarium silicone instead**, e.g. Den Braven/Zwaluw *Aqua-Silicone* (+180 °C, no fungicide). It survives the heat better and is the food-safer choice. **Never** use anti-mould / bathroom silicone. | €3-8 |
| Feet, printed in **PC** | 4 | [`cad/stl/foot_PC_print_x4.stl`](../cad/stl/foot_PC_print_x4.stl). They touch the ~100 °C rim, so no PLA/PETG/TPU. | filament |
| M5×12 bolts + washers + M5 heat-set inserts | 4 | feet | €2 |
| Centering jig blocks, printed (PLA/PETG) | 4 | [`cad/stl/centering_jig_block_print_x4.stl`](../cad/stl/centering_jig_block_print_x4.stl). Crush-rib pins push into the board holes, no bolts. | filament |

### Each heater terminal (×2)
| Part | Notes |
|---|---|
| 35 mm² copper tube lug, M8 hole | crimped on the cable |
| M6×25 A2-70 bolt, nut, plain washer | 8 N·m |
| Ø18 M6 washer (DIN 9021) | under the bolt head |
| **M6 nylon/PTFE shoulder washer, sleeve OD ≤ 8 mm** | **mandatory**: keeps the bolt from bridging the live lug to the aluminium core |
| Steel plate 30 × 14 × 5 mm, Ø6.5 hole | on the water side, spreads the clamp load |
| Kapton tape | over the board edge where the lug crosses it |

### Power
| Part | Qty | Notes | ~Cost |
|---|---|---|---|
| **Used 12 V car batteries** | 4 | Ours: Arrow 60 Ah 500 A, Mercedes-Benz OEM, ad F370 EFB 70 Ah 760 A, Recor Master 60 Ah 510 CCA. Test each one: **≤ 6 mΩ** internal resistance is great, > 10 mΩ is a weak link. | ~€20 each |
| 35 mm² welding cable (fine strand) | ~3 m | any electrical wholesaler | ~€9/m |
| 35 mm² M8 tube lugs | 8 | 2 per contactor + 2 at the kettle + spares | €0.34 each |
| 35 mm² lug crimper (lever or hydraulic hex) | 1 | | €23-56 |
| Adhesive heat-shrink Ø16, red + black | 1 m | | €2 |
| Screw-clamp battery terminals | 4 pairs | the bare cable end clamps straight in ([what we used](https://www.skroutz.gr/s/45316798/Poloi-Mpatarias-Aytokinitou-CTC-585.html)) | ~€6/pair |
| **TE EV200 contactor** (EV200AAANA, 500 A, 12-24 V coil) | **2, in series** | If one welds shut, the other still opens. Make current is ≤ 650 A. Cheap ones on AliExpress are probably clones. | €26-50 each |
| Momentary push button + long 2-core lead | 1 | coil supply from battery #1 (+12 V); hold to heat | €1 |
| Hacksaw | 1 | cuts the 35 mm² cable cleanly (tape the cut first) | €5 |
| *Recommended:* 500 A ANL fuse rated **≥ 80 V DC** + holder, at the + post | 1 | a dead short on 4 car batteries is 2,000-3,000 A | €23 |

**Rough total:** ~€300 including the batteries and the PCB order (you get 4 spare heaters).

## Wiring
```
 B1+ ─ B2−    B2+ ─ B3−    B3+ ─ B4−                    (short jumpers, bare ends in the post clamps)
 B4+ ─[fuse]─ EV200 #1 ─ EV200 #2 ─────────────► lug A ┐
                                                      │  heater spiral (65 mΩ)
 B1− ◄────────────────────────────────────────── lug B ┘
 coil loop: B1+ (12 V) ─ push button ─┬─ EV200 #1 coil ─┬─ B1−
                                      └─ EV200 #2 coil ─┘
```

## Assembly
1. **Sand the water side** of the heater (120-240 grit, random circles), then wash with soap and wipe with IPA. Water should
   sheet across it without beading.
2. **Press the 4 jig blocks** into their holes (15/30°, 105/120°, 195/210°, 285/300°).
3. **Silicone:** scuff the bottom 10 mm of the ring, then lay a 3-4 mm bead in a circle. Lower the ring in against all 4
   blocks and run a fillet inside and outside. Cure warm (we hung it in a heated printer chamber at 20 → 29 °C overnight).
   Wait **24 h before a cold leak test** and **~48 h before boiling**. Pull the jig blocks straight up.
4. **Feet:** set the M5 inserts into the PC feet, then bolt them through the 45/135/225/315° holes.
5. **Terminals:** Scotch-Brite the lug palm and the pad until bright, no grease. Build the stack: M6 bolt, Ø18 washer,
   shoulder washer (sleeve inside the lug hole), lug, board, steel plate, washer, nut. Torque to 8 N·m.
   Check: lug to aluminium reads **open**, and lug to pad is **< 1 mV at 20 A**.
6. **Cables:** hacksaw, strip 20 mm, crimp, heat-shrink. Wire as above, with both contactors' **+** terminal toward battery +.
7. **First runs:** use 1-1.5 L of water. Step up from 2 batteries to 3, then 4. Stand back, hold the button, and let go at
   a rolling boil. Dump the first couple of litres.
