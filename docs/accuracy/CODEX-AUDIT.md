# Codex accuracy audit — 17 November 2026

Scope: all 25 entries in `data-codex` as present at the start of this review. This is an evidence audit and proposed wording for the implementing worker; it does not modify the game. The downloaded TG 22.3 report and enclosures and Report 2G-9C were read locally. A short supplementary check of the museum's and NHHC's official pages follows below. Unverified does not mean false.

## Source keys

- **TG:** [TG 22.3 main report](../sources/tg-22-3/U-505TG22.3Report.htm), printed pp. 1–8.
- **A1:** [ComCortDiv4 report](../sources/tg-22-3/U-505ComCortDiv4Report.htm), paragraph 3, printed pp. 2–3.
- **A3:** [Pillsbury report](../sources/tg-22-3/U-505Pillsbury%20Report.htm), printed pp. 2–3 and narrative paragraphs 3–4.
- **A8:** [Lange statement](../sources/tg-22-3/U-505LangeStatement.htm), printed pp. 1–2.
- **B:** [Chronology](../sources/tg-22-3/U-505Chronology.htm), printed pp. 1–2.
- **D:** [Communications log](../sources/tg-22-3/U-505CommunicationsLog.htm), transmission timestamps.
- **E:** [Prisoner list](../sources/tg-22-3/U-505PrisonersList.htm), printed pp. 1–2.
- **F:** [Boarding parties](../sources/tg-22-3/U-505BoardingParties.htm), printed pp. 1–3.
- **I:** [Cruise report](../sources/tg-22-3/U-505ASCruise.htm), operations enclosure B, 19 June 1944, printed p. 51.
- **2G:** [Report 2G-9C](../sources/report-2g-9c/DesignStudiesTypeIXC.htm), section and printed section page as cited. Much baseline data is IXC40; do not silently substitute it for U-505.

## Entry-by-entry findings

### 1. `you` — You are invented

**Keep `invented`.** TG p. 4 identifies Lt.(jg) A. L. David as party commander; F p. 1 lists nine boarders including David, separately from three boat crew. The game-player disclaimer is a design statement and needs no historical proof. The full name is additionally supported by the museum's boarding-party page below. No factual correction required.

### 2. `assumptions` — What this game assumes

**Keep `simplified`, but audit the generator separately.** This is a description of implementation. It must include coefficients, initial conditions, item positions and all other unsourced numerical choices; a parent record marked `real` must not hide an assumed field. Prefer: “The list below is generated from data marked assumed or placeholder. These are game choices, not measured historical values.”

### 3. `u505` — U-505

**Partly supported; avoid marking the entire current paragraph `real`.** 2G introduction p. 3 explicitly lists U-505 as Type IXC. 2G S41-5 pp. 1–2 supports two nine-cylinder diesels; general design data and the museum collection support electric propulsion and four bow/two stern tubes. The downloaded reports do not verify the current exact 76.76 m, 1,120 t and 1,232 t figures. In particular, 2G's IXC40 stability data is not a warrant for those U-505 numbers. The museum and NHHC supplement support the complement and previous-command history (see below). Retain those with their own citations; omit precise displacement from this codex paragraph or explicitly identify it as an unverified model input.

### 4. `day` — 4 June 1944

**Correct chronology and time-basis language.** B p. 1 distinguishes initial contact 11:09 from its report 11:10. TG p. 3 has depth charges 11:21 and surfacing 11:22½; B p. 2 agrees. Boarding is not securely 11:35: TG p. 4 says the party was sent then, B p. 2 says cast off 11:38 and aboard 11:43, A3 p. 2 and A1 paragraph 3 say aboard 11:46. A3's gunfire times differ too. TG pp. 5–6 explicitly fixes surrender at 11:27Z and asks other narratives/charts be adjusted. Replace the vague assertion that the reports lack a time basis with a clear game convention: “The clock uses GCT (UTC), selecting the task-group chronology where accounts differ. First sonar contact was 11:09; the report followed at 11:10. The party boarded about 11:43–11:46. The gameplay start and compressed sequence are disclosed separately.” Keep 12:40 and 14:23 as TG's selected account, not universally unanimous minutes.

### 5. `radio` — What the radio said

**Stale source-access claim.** D is now readable and identifies VHF, TBS and TBY communications. Suggested body: “Enclosure D preserves the task group's communications log. This version presents events as captions rather than recreating the voices of real people. No invented radio dialogue is used.” Do not imply that lack of access still blocks this decision.

### 6. `insignia` — No swastikas

**Keep as a disclosed presentation choice; remove the blanket legal assertion.** TG p. 5 records US colours with the German flag below. The game can simply state: “Flags and political insignia are omitted by design. This is a presentation choice, not a claim that the historical boat carried no ensign.” No German-law conclusion is necessary or established by these reports.

### 7. `crew` — The crew of U-505

**Core events supported; first-name check resolved by supplementary museum source.** A8 p. 1 records Lange's abandon-and-sink order; TG p. 4 and A3 paragraph 3 record one dead sailor on deck. E has 58 named prisoners (five officers and 53 crew); it does not name Fischer and is not a death roster. Remove “first name is still being checked against the prisoner list.” The museum explicitly names Gottfried Fischer. Keep the humane framing and no gameplay around his death.

### 8. `compressed` — One sailor, many jobs

**Correct the stated reason for 11:40.** “Reports say only shortly after 11:35” is false: B and A3 supply actual boarding times later than 11:40. Suggested body: “The real boarders divided the work. One player combines several men's jobs. The reports put the party aboard around 11:43–11:46; this game's boarding clock and route are a compressed reconstruction.” If the implementing worker moves the game start, revise this disclosure accordingly.

### 9. `strainer` — The sea strainer

**Core supported; separate stream dimension from hardware diameter.** TG p. 4 describes a six-inch stream and replacement of the strainer cover. It does not assign the action to a named man or give cover weight, pipe diameter, exact location, or a hydraulic discharge coefficient. The museum supplements Lukosius's identification. Keep the game opening/flow assumption explicit; do not use `real` on a record to imply that Cd 0.38 or an effective opening is measured. The 31.4 lb collection claim and 8-/11-inch comparisons need their specific sources, not TG. Prefer omitting unresolved dimensions from the player paragraph until independently checked.

### 10. `flooding` — How the flooding works

**Keep `simplified`; qualify 112 t as a model budget.** Neither report establishes that a difference between these particular displacement figures is the reserve actually available in U-505's damaged condition. TG pp. 6–7 supports the significance of headway to the observed waterline; it does not prove the game's lift law. Suggested correction: “The simulation starts with a simplified 112 t buoyancy budget. Flooding, trim and headway are modelled and tuned; the coefficients and initial amounts are game assumptions, not measurements from the capture.” Formula description can remain as a model explanation.

### 11. `ballast` — Vents and blows

**Mechanism supported, numerical implementation still assumed.** 2G S29, especially printed pp. 10–11 and comment, describes flood/vent areas, vent grouping and blowing; S49 describes compressed-air and exhaust-gas arrangements. S29 specifically says all vents can be operated with three cocks; this does not validate the game's three tank masses/locations, free air, pressure or flood rate. Cite 2G rather than only unread Skizzenbuch. Keep the one-minute loss explicitly a game result.

### 12. `german` — Reading German

**Keep `invented`; soften blanket language.** 2G S28 pp. 4–5 describes engraved equipment labels and sketch-book cross references. It does not confirm every game translation as the “usual Kriegsmarine words,” or the boarders' reading fluency. Suggested wording: “The glossary is a game mechanic. German labels are working translations unless individually sourced. The boat's exact label wording and the game's pipe colours remain unverified.”

### 13. `rudder` — Hard right rudder

**Core supported; distinguish observations from assumed propulsion model.** A8 p. 1 reports jammed rudders; TG p. 4 records circling about seven knots and pp. 6–7 the eventual hand-steering correction. A3 p. 3 says power was cut at about 13:18, conflicting with A1's approximately thirty-minute account. The downloaded reports do not securely establish the game's noon engine-stop minute. NHHC's official summary additionally says diesel engines were shut down (cached text, direct-open failed). Prefer: “With propulsion still driving her and the rudder hard right, U-505 circled. The boarders stopped her. On 5 June Gallery and his party put the rudder amidships by hand.”

### 14. `charges` — Demolition charges

**Correct an important false absence claim.** A3 narrative paragraph 3 reports an approximate six or eight preset demolition bombs whose wires were pulled. TG p. 5 assigns further charge work to salvage parties. Exact count, locations, wiring, timing, and detonator procedure remain unsettled. Suggested body: “Pillsbury's report estimates six or eight preset demolition bombs and says their wires were pulled. The two represented here stand in for that work at invented locations. The game's two-step interaction and mishandling outcome are invented; the reports do not document that procedure.” Keep `invented` for the playable representation.

### 15. `scuttle` — Scuttling valves

**Keep `invented` for the specific prop.** A8 supplies the order, TG pp. 4–5 the closing of valves. This does not identify the game's particular motor-room valve, dimensions or arrangement. 2G can inform system design but does not establish capture-day lineup or this prop's location. Existing text can remain after “sources read” is updated to distinguish no located evidence from no access.

### 16. `booby` — Booby traps

**Retain fear, correct “report records none.”** TG p. 6 actually records the suspected trap: an open fuse-box cover obstructing a watertight-door dog, which Gallery judged accidental. Suggested body: “The boarders feared traps. On 5 June Gallery inspected a suspected trap and found an open fuse-box cover obstructing a door. The searchable objects in this game are invented; no trap is found in them.” The separate Lukosius recollection was not verified here and can be removed rather than attributed without a passage.

### 17. `enigma` — The Enigma machine

**Generic recovery supported; precision supported by supplementary NHHC indexed text.** TG p. 5 records coding machines and secret papers, not a particular rotor set. NHHC's official capture summary describes an Enigma cipher machine with up-to-date rotors and the codebreaking risk. Keep that claim with NHHC provenance. Remove “worth more than a sunk boat” as an unsourced absolute comparison; say the material had major intelligence value.

### 18. `papers` — Codebooks and papers

**Supported categories, route/positions are reconstructed.** TG p. 4 records papers passed up on deck; p. 5 records secret papers and coding machines; A3 14:25 lists confidential publications, charts, documents and instruments. D at 12:05 orders removal of codes/publications. Do not claim each separate radio item travelled through a specific hatch solely from this evidence. Keep positions estimated and cite the relevant radio-document catalog only for its actual holdings.

### 19. `ktb` — The war diary

**Correct a clear catalog error.** TG's enclosure list A–I contains no German KTB. The archive's U-505 index lists the KTB as a separate document after the report enclosures. Suggested body: “U-505's Kriegstagebuch is listed separately in the archive, not as an enclosure to this action report. The game's diary item represents the collection of documentary intelligence; its position is estimated.” Do not claim the separate KTB's contents were checked in this review.

### 20. `pillsbury` — Pillsbury holed

**Correct the early time.** “Before 12:03” contradicts A3: first puncture 12:45, further damage at 13:10, engine room flooded and withdrawal at 13:23. Suggested body: “Pillsbury was holed while trying to get alongside and secure lines. Her own report places the damaging attempts at 12:45 and 13:10; an engine room flooded to the waterline and she had to haul clear.” Remove the moralising final sentence or keep it as commentary, not a sourced event.

### 21. `salvage` — Trosino's salvage party

**Core supported; name both commanders.** TG p. 5 says about 12:40, Commander E. Trosino and Lt. D. E. Hampton, with charges, valves, watertight doors and gasoline handy-billies; tow 14:23. F distinguishes the salvage and boarding parties. Add Hampton rather than implying a single commander over all arrivals. Counts, capacities, positions and three named aft-hatch closures remain game assumptions. The museum supplements Trosino's first name.

### 22. `tow` — Fifteen days to Bermuda

**Core supported, expand recovery beyond “rig pumps.”** TG pp. 6–7: wire parted midnight 4–5 June; transfer to Abnaki 10:15 on 7 June; headway supported the stern; electric submersible pumps had leads from Abnaki; pumping, tank blowing and removing weight combined; by 20:00 the boat was at the first-boarded waterline; fully surfaced by evening 8 June. I p. 51 records approach to Naval Operating Base Bermuda on 19 June. Suggested body should explicitly call the three carried pumps and compressed single-player crisis a game reconstruction, not a complete account of the recovery.

### 23. `gallery` — Gallery and the fuse box

**Keep discovery his; refine timing and attribution.** TG p. 6 first has retowing at dawn, then continued hard-right rudder discovered underway, then Gallery's visit. It does not establish that he boarded exactly at dawn or personally turned the hand gear alone. Suggested body: “On 5 June, after towing resumed, Captain Gallery inspected the suspected trap. It was an open fuse-box cover obstructing the door dog. He closed it, checked the compartment, and went aft with his party to put the rudder amidships by hand.”

### 24. `secrecy` — Kept secret

**Later history is supported by supplementary official pages, but revise 1947 language.** The downloaded TG report alone is not evidence for Camp Ruston or repatriation. The museum page supports separation, families being told the men were considered dead, and the last prisoners' return in 1947. “They were not returned until 1947” incorrectly suggests every prisoner remained until then. Use “The last captives returned home in 1947.” David's Medal of Honor has an official NHHC citation; A3 paragraph 4 only recommends a Navy Cross and is not the later award record.

### 25. `museum` — U-505 today

**Correct donation-year formulation and omit an unverified opening date.** The museum's First Exhibition page supports a 1953 agreement/gift and 1954 arrival/dedication. Its restoration page describes the physical indoor relocation in April 2004. Suggested body: “U-505 opened as a permanent museum exhibit in Chicago in 1954 and became a National Historic Landmark in 1989. She is now displayed indoors.” The specific 2005 public-opening date was not established in this limited source check, so omit it or leave a field-level pending note rather than conflate it with the 2004 move.

## Supplementary official-source check

These are separate from the downloaded report audit. The museum pages opened in full. Several NHHC pages returned readable cached/indexed passages through search but direct opens timed out or returned 502; that distinction should remain in source-access notes.

- [MSI: Capturing the U-505](https://www.griffinmsi.org/exhibits/u-505-submarine/capturing-the-u-505), sections “Saving U-505,” “The boarding party,” and “Prisoners of war”: supports Lukosius's strainer action, named nine-man party, Gottfried Fischer, 58 survivors, Camp Ruston isolation, relatives notified the men were considered dead by August 1944, and last return in 1947. This does not say the men remained officially dead until 1947.
- [MSI: German Type IXC Submarine, U-505](https://collections.griffinmsi.org/collections/4855), object description: supports two nine-cylinder diesels, two electric motors, four bow/two stern tubes, and 59-person wartime complement. Its measured length is 251 ft 11.62 in (about 76.793 m), so it does not validate exactly 76.76 m.
- [MSI: The First Exhibition](https://www.griffinmsi.org/exhibits/u-505-submarine/the-first-exhibition-of-u-505), “Chicagoans save” and “Trip to Chicago”: supports the 1953 gift arrangement, 1954 arrival/dedication, and 1989 landmark designation.
- [MSI: Restoration and Relocation](https://www.griffinmsi.org/exhibits/u-505-submarine/restoration-relocation), “Relocating”: describes the physical move in April 2004. The 2005 instructor manual search excerpt conflicts by calling April 2005 the move, and could not be opened; do not use it to settle a date.
- [NPS asset record](https://npgallery.nps.gov/NRHP/AssetDetail/5aca3f60-9f4f-4d55-90e5-82146cbbe772) identifies the U-505 record and 29 June 1989 date. Its nomination's dimensions/displacements differ from the game's; do not substitute them uncritically either.
- [NHHC: Defeating the Sharks](https://www.history.navy.mil/browse-by-topic/wars-conflicts-and-operations/world-war-ii/1944/u-505-capture.html), readable indexed body: supports diesel shutdown, recovered Enigma/current rotors and communications equipment, codebreaking risk, Bermuda on 19 June, David's award, and 1989 landmark designation. Direct page open failed during this check.
- [NHHC: H-064-3](https://www.history.navy.mil/about-us/leadership/director/directors-corner/h-grams/h-gram-064/h-064-3.html), readable indexed body: supports Zschech's suicide during an October 1943 depth-charge attack and 59 crew on the final patrol. Direct page open failed.
- [NHHC: Albert LeRoy David citation](https://www.history.navy.mil/content/history/nhhc/browse-by-topic/heritage/awards/decorations/medal-of-honor/world-war-ii-medal-of-honor-recipients/lt-albert-leroy-david.html), readable indexed citation: supports the award and full name. Direct page open returned 502.

Remaining unresolved: exact capture-day own-pump power and valve lineup; game strainer effective aperture/Cd; exact charge count/location/handling; exact physical pump counts/capacities and placements; model initial water, buoyancy, lift, hull/compartment dimensions and timings where accounts conflict; exact German labels and pipe palette; 2005 exhibit-opening claim; image rights.
