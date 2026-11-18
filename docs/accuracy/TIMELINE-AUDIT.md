# Timeline, acts, and comparison audit

Reviewed 17 November 2026 against the downloaded TG 22.3 report and its enclosures. This records evidence and recommended corrections to the pre-review build; implementation choices may retain explicitly labeled compression. No changes to `index.html` were made by this audit worker.

## Sources and conventions

- [TG 22.3 main report](../sources/tg-22-3/U-505TG22.3Report.htm), printed pp. 3–7.
- [Enclosure A1, Commander Escort Division Four](../sources/tg-22-3/U-505ComCortDiv4Report.htm), pp. 2–3, especially paragraph 3.
- [Enclosure A2, Chatelain](../sources/tg-22-3/U-505ChatelainReport.htm), narrative paragraphs 2–8; opening declares all times GCT.
- [Enclosure A3, Pillsbury](../sources/tg-22-3/U-505Pillsbury%20Report.htm), pp. 2–3 and paragraph 3.
- [Enclosure A8, Lange's statement](../sources/tg-22-3/U-505LangeStatement.htm), pp. 1–2.
- [Enclosure B, chronology](../sources/tg-22-3/U-505Chronology.htm), pp. 1–2.
- [Enclosure D, communications log](../sources/tg-22-3/U-505CommunicationsLog.htm), timestamped transmissions.
- [Enclosure F, boarding lists](../sources/tg-22-3/U-505BoardingParties.htm), pp. 1–3 and 7–10.
- [Enclosure I, cruise report](../sources/tg-22-3/U-505ASCruise.htm), operations appendix printed pp. 30–40 and 51. This document has its own internal enclosures; its operations pages are labeled “ENCLOSURE B,” which must not be confused with the capture report's separate two-page Enclosure B above.

The 4 June action can be labeled GCT/Zulu: Chatelain explicitly says GCT, the main report identifies the official surrender as 1127Z, and the cruise operations sheets for 4–5 June give zone description 0:00. The statement that the time basis is wholly unknown is obsolete. Do not extend one zone label automatically across the epilogue: later cruise sheets change zone description, and 19 June is Z.D. 4:00. Lange's translated recollection begins “about 1200”; it is a personal approximate time, not grounds to move the task-group action to noon.

## Action timeline and Act 1

| Existing claim / data path | Evidence | Recommended treatment |
| --- | --- | --- |
| `timeline.time_basis` unknown | A2 opening: all times GCT; main p. 6: official surrender 1127Z; I operations pp. 30–33: Z.D. 0:00 | Use GCT/Zulu for the 4 June action; acknowledge differing reported event minutes. |
| 11:09 contact, about 800 yards | A2 para. 2; B p. 1, 1109 | Supported. Main p. 3 gives 1110 for the report of contact, a different event. |
| 11:16 hedgehogs and aircraft marking | Main p. 3 gives hedgehogs 1116, aircraft marking 1116½; B pp. 1–2 and D give subsequent marking transmissions around 1117–18 | Supported as a compressed sequence. Do not imply all happened at one exact instant. |
| 11:21 depth charges; aft flooding and jammed rudder | Main p. 3; A8 p. 1 reports water ingress, loss of lights/electrical machinery, and jammed rudders after the attack | Attack and damage are supported. Precise compartment leaks and fixed damage dimensions remain model assumptions. |
| Surfacing at 11:22:30, 700–800 yards away | Main p. 3: 800 yards from Chatelain; A2 para. 6: about 700 yards from Chatelain | Say **from Chatelain**. These distances are not the view distance from Pillsbury. A3 p. 2 gives a much longer distance from Pillsbury and a different minute. |
| 11:25 Chatelain torpedo, passing ahead | A2 para. 7; B p. 2, 1125 | Supported. |
| 11:27 general cease-fire | Main p. 4; B p. 2; D 1127 | Supported as the task-group order. Individual firing logs differ; A3 records final cease-fire at 1128. |
| 11:35 Pillsbury sends boarders | Main p. 4 summarizes this at 1135; A3 p. 2 and B p. 2 give boat cast-off at 1138; A1 para. 3 says boat put in water 1140 | Distinguish the order/preparation from the launch and boarding. An 11:35 caption may say the boarding party is ordered away/preparing, with source disagreement disclosed. |
| `act1.note` and rendering comment say radio log unread/pending | Enclosure D is now downloaded and readable | Remove the stale access claim. Captions without spoken reconstruction remain a valid presentation choice. Do not invent dialogue merely because the log is now available. |

Lange's rank in A8's signature is Oberleutnant zur See d.Res. Calling him the U-boat's commanding officer is supported; “Commander Harald Lange” should not be used as an English naval rank.

## Boarding and salvage on 4 June

| Existing claim / data path | Evidence | Recommended treatment |
| --- | --- | --- |
| `scenario.boarding_at`, `act2.start`, intro: player below at 11:40; codex says reports only say shortly after 11:35 | A3 p. 2: party aboard and in possession at 1146; A1 para. 3: first man aboard 1146; B p. 2: aboard at 1143; D 1142: boat alongside | 11:40 is earlier than the documented boarding estimates, not simply an unknown minute that the sources fail to mention. Prefer the corroborated 11:46 as the playable start and disclose the B 11:43 alternative. If retaining 11:40, label it explicit staging/compression. The exact minute of descent below is not separately recorded. |
| 7-knot circling in Act 2 intro | Main p. 4 and B p. 2 report about 7 knots; A1 para. 3 gives 3–4; A3 p. 2 later gives 4½ | Use “circling to starboard” or “reported at about seven knots”; do not present a reconciled measurement. |
| `act2.heard` at 12:03 says Pillsbury has already been holed | Main p. 4's 1203 is the **carrier returning toward the scene**, not the collision. A3 p. 2 first collision at 1245; p. 3 second at 1310. I operations p. 31 reports damage at 1338–42 | Remove the false 12:03 inference. A supported replacement is a report during Act 3 after the 1310 second collision, describing the bow-plane damage and flooded engineering compartment. A staged message time should be identified as such rather than a literal transcript. |
| “The real day” premise: boat stopped at about noon, dead in water until 14:23 | A3 p. 3 logs power cut and stop at approximately 1318; I operations p. 31 reports dead in water at 1338; D also reports it in this later period | This old calibration premise is false as an established source claim. Preserve a useful numerical calibration scenario as an explicitly hypothetical model check; do not call its noon engine-stop schedule the real day. Stopping earlier is a player's counterfactual choice. |
| Act 2 orders: stop ingress, stop propulsion, collect papers, counter scuttling | Main pp. 4–5; A3 p. 3, para. 3 | Supported objectives. One invented sailor doing these jobs serially is gameplay compression. The real party split tasks. |
| Two charges; number “not in sources read” | A3 p. 3, para. 3 says wires pulled from “6 or 8” preset demolition bombs; main p. 5 describes further disconnection | The exact count remains unresolved, but there is an approximate contemporary count. Keep two explicitly as a gameplay placeholder, acknowledge the A3 estimate, and retain location/procedure uncertainties. |
| `act2.end` / `act3.start`: 12:40 salvage party | Main p. 5: **about** 1240, under Trosino **and Hampton**. F p. 3 lists Hampton's initial trip at 1258; A3 para. 3 places carrier parties between its first and second lines | Retain about 12:40 as the selected main-report convention and label the transition approximate. Do not make all carrier parties arrive together at a proven exact minute. Include Hampton where attribution is useful. |
| Act 3 shuts three specific aft hatches | Main p. 5 supports closing watertight doors generally; main p. 6 says the aft access door had not been opened since capture | The number, exact lineup, and universal initially open doors are modeling choices. Do not claim a sourced procedure requiring precisely those three open hatches to be shut. |
| Act 3 gasoline handy-billies | Main p. 5 explicitly supports gasoline-driven handy-billy pumps | Type supported; count, mass, location, and rate require separate evidence and remain flagged. |
| `act3.end_text`: “takes U-505 in tow by the stern” | Main p. 5: **Guadalcanal's stern alongside U-505's bow**, wire secured at 1423 | Correct the direction: “Guadalcanal takes U-505 in tow from the carrier's stern,” or explicitly stern-to-bow. The U-boat was not towed stern-first. Existing comparison row “from Guadalcanal's stern” is correct. |
| 19:16 parties return with documents | Main p. 5; I operations p. 33 | Supported. |

## Epilogue

| Existing claim / data path | Evidence | Recommended treatment |
| --- | --- | --- |
| Midnight tow wire parts | Main p. 6 rounds to midnight 4–5 June; I operations p. 33 logs 2353 on 4 June | “Around midnight” reconciles the narrative and detailed log. Exact 23:53 may be cited as the log's time. |
| Gallery boards “at dawn” and moves rudder alone | Main p. 6: dawn retowing comes first, then rudder still hard right, then Gallery goes aboard with a selected party, closes obstructing fuse-box cover, opens dog/door, and **we** go aft to put rudder amidships by hand. F p. 7 and I operations pp. 34–35 place Gallery's inspection at 1745–1920 on 5 June | Label scene “5 June” or “Later on 5 June,” not dawn. Attribute the discovery to Gallery and the manual work to Gallery and his party; do not turn it into a player puzzle. |
| 7 June scene clock 08:00 | Main p. 7 tow handover 1015; I operations p. 37 gives 1018 and salvage party sent at 1035; F p. 8 also gives 1035 | 08:00 is unsupported. A near-handover start can use the selected 10:15 main-report convention, disclosed as staged; a player's arrival with the salvage party is more naturally after the documented 10:35 departure. The 3-minute transfer discrepancy remains explicit. |
| 7 June three handy-billy pumps only | Main p. 7: **electric submersible pumps powered by leads from Abnaki**, removal of loose gear/weights, blowing tanks, and continued headway from Abnaki. F p. 10 additionally records one handy-billy and hose sent at 1250 | Make the main represented pump type electric submersible with external Abnaki power. A handy-billy was also sent later, so it is not categorically absent; the historical recovery cannot be described as three gasoline pumps alone. Counts, rate, carry task, fixed water loads, and loss deadline are game assumptions. |
| Full surfaced trim after several simulated hours on 7 June | Main p. 7: by 2000 on 7 June boat back to initial-boarding level; fully surfaced trim by evening **8 June** | Treat the game's 95 t target as an invented recovery target/compression, not a dated historical full-trim claim. In the comparison, retain the historical June 8 result. |
| `awashWon()` says elapsed hours “after the pumps went in” | Code computes `sim.s.t / 3600`, elapsed since scene start | Correct to “hours into the scene” unless first-pump time is separately tracked. Do not report the wrong reference point. |
| Bermuda arrival 19 June | I operations p. 51, 19 June (Z.D. 4:00): prize crew sent to U-505; task group enters swept channel for Naval Operating Base, Bermuda | Arrival date supported in the downloaded cruise report. Link to it rather than leaving arrival supported only by secondary sources. |
| Camp Ruston, Kriegsmarine declaration of death, repatriation in 1947, codebreaking motive, Medal of Honor, 1954 museum transfer, indoor display since 2005 | These specific later claims are not established by the two downloaded reports; A3 recommends David for Navy Cross, which is not evidence against a later Medal of Honor award | Keep unresolved source status explicit or remove unverified details from factual narration until direct evidence is read. Absence in the capture report is not disproof. Avoid leaving an entire mixed card/entry marked fully verified on the strength of the capture report alone. |

## Comparison text supported by these reports

- At 12:40: “Afloat when the carrier's salvage parties began arriving, about 12:40 in the main report.”
- Strainer: “The Pillsbury party replaced a strainer cover through which the main report describes a six-inch stream.”
- Propulsion: “The boarding party stopped the boat; Pillsbury logs power cut at about 13:18.”
- Papers and machines: “Confidential publications, charts, documents and instruments were brought off; the main report also describes coding machines.” Specific Enigma configuration/current rotors and particular radio equipment need their own sources.
- At 14:23: “Guadalcanal took U-505 in tow with the carrier's stern toward the submarine's bow.”
- Hatches and pumps: “The salvage parties closed watertight doors and rigged gasoline-driven pumps.” Keep exact game counts out of the historical column.
- Charges: “Pillsbury's report estimates six or eight charges had their wires pulled; the main report describes disconnection by the carrier's parties.” Locations and the game's two-step sequence remain unresolved.
- 7–8 June: “Recovery combined external-powered electric pumping, blowing tanks, removing weight and continued tow headway; full surfaced trim by the evening of 8 June.”

The reports contain estimates and conflicting minutes. Preserve those distinctions rather than synthesizing a precision none of the witnesses supplied. Passing the simulation checks verifies behavior under the chosen model, not the historical timing, dimensions, or counterfactual survival margin.
