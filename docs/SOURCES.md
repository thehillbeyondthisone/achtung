# Primary sources for the accuracy review

Retrieved 17 November 2026. These are local copies of U-boat Archive's hosted historical report transcriptions, with their linked figures and enclosures. The HTML source bytes are unchanged. They are readable documents, not merely search results or catalog entries. They are not a newly authenticated collection of scans of every original report page.

## Open the requested documents

| Document | Offline copy | Online source |
| --- | --- | --- |
| Commander Task Group 22.3, *Capture of German Submarine U-505*, USS Guadalcanal CVE60/A16-3, Serial (0021) | [Main report](sources/tg-22-3/U-505TG22.3Report.htm) · [Enclosure index](sources/tg-22-3/U-505.htm) | [U-boat Archive report](https://www.uboatarchive.net/U-505A/U-505TG22.3Report.htm) |
| *Design Study of Former German Submarine — Type IXC*, Report 2G-9C, Portsmouth Naval Shipyard, 1946 | [Full report](sources/report-2g-9c/DesignStudiesTypeIXC.htm) · [Package notes](sources/report-2g-9c/README.md) | [U-boat Archive transcription](https://www.uboatarchive.net/Design/DesignStudiesTypeIXC.htm) |
| Development handoff | [HANDOFF.md](HANDOFF.md) | Reconstructed from the current code, history, session notes, and user status. The original externally supplied design document was not found. |

Open the `.htm` files in a browser. Their historical formatting and ISO-8859-1 encoding are retained. No PDF edition was found or generated. The downloaded text and figures can be read without access to the archive. Archive-wide navigation and unrelated documents linked from the original index are outside this local package.

## TG 22.3 enclosure map

| Enclosure | Local reading link |
| --- | --- |
| A1 | [Commander Escort Division Four](sources/tg-22-3/U-505ComCortDiv4Report.htm) |
| A2 | [USS Chatelain report](sources/tg-22-3/U-505ChatelainReport.htm) |
| A3 | [USS Pillsbury contact and action report](sources/tg-22-3/U-505Pillsbury%20Report.htm) |
| A4 | [USS Pope report](sources/tg-22-3/U-505PopeReport.htm) |
| A5 | [USS Flaherty report](sources/tg-22-3/U-505FlahertyReport.htm) |
| A6 | [USS Jenks report](sources/tg-22-3/U-505JenksReport.htm) |
| A7 | [Composite Squadron Eight ASW-6 reports](sources/tg-22-3/U-505VC-8ASW-6Report.htm) |
| A8 | [Statement by U-505's commanding officer](sources/tg-22-3/U-505LangeStatement.htm) |
| B | [Chronological narrative](sources/tg-22-3/U-505Chronology.htm) |
| C | [Track charts](sources/tg-22-3/U-505TrackChart.htm) |
| D | [Radio/communications log](sources/tg-22-3/U-505CommunicationsLog.htm) |
| E | [Prisoners list](sources/tg-22-3/U-505PrisonersList.htm) |
| F | [Boarding parties](sources/tg-22-3/U-505BoardingParties.htm) |
| G | [Photographs and captions](sources/tg-22-3/U-505Photographs.htm) |
| H(2) | [Plan of the Day, 4 June](sources/tg-22-3/U-505PlanOfTheDay.htm) |
| I | [Third antisubmarine cruise report](sources/tg-22-3/U-505ASCruise.htm) |

The main report lists H(1), “Intentions for the Night Signal for 17 May,” but the archive index links only H(2). H(1) was not located as a separate document. Do not describe this download as every enclosure of the original archival packet. The main report also explains that most distributed copies of Enclosure I ended at 0800 on 4 June; assess the hosted version's coverage when citing it.

Enclosure G is saved with all 59 detail pages explicitly linked by its hosted index and all 58 unique full-size JPEGs they reference, as well as the thumbnails. The main report lists 60 photographs. The hosted detail page numbered 433 embeds image 443, which is also used on page 443. This discrepancy is preserved and recorded in the manifest; no unlinked photo numbers were guessed. The TG package contains 251 downloaded source files totaling 11,213,506 bytes.

The radio log is now available for review. It has not been turned into game dialogue in this task. Compare its timestamps and callsigns with the unit reports before choosing any quotations. The boarding-party list and prisoner list also require interpretation; the prisoner list is titled *Prisoners Taken*, so it should not be assumed to settle the identity of the sailor killed.

## Using Report 2G-9C

The full hosted report and all 18 directly referenced images are local. Its sections have their own dates and pagination. The introduction lists U-505 among boats examined, but substantial descriptions and tabulated values concern Type IXC40 boats. A design value is not automatically a U-505 measurement or evidence of the boat's condition on 4 June 1944.

Start with S16 (access), S22 (steering and diving), S29 (weight, stability and integrity), S48-1 (pumping and drainage), S60–S64 (electrical plant and distribution), and S88 (damage control). Use the report's contents and browser Find to navigate the large single HTML document.

S48-1 describes installed pumps, motors, and operating limits. It does **not** establish usable battery power, circuit condition, or valve lineup during capture. The game's own-pump power question remains open. Record a section and printed page for each technical claim before replacing an assumed game value.

## Provenance and integrity

- [TG 22.3 manifest](sources/tg-22-3/manifest.json): downloaded files, original URLs, byte lengths, SHA-256 hashes, and retrieval time.
- [2G-9C manifest](sources/report-2g-9c/manifest.json): the same information for the technical report and its figures.
- [TG acquisition script](../tools/fetch-tg22-3.mjs): downloads only the report/enclosure links identified in the archive index and their linked images. Recheck the archive address before a future rerun.

Ordinary DNS lookup for `www.uboatarchive.net` failed on this machine. A public DNS-over-HTTPS lookup at `https://dns.google/resolve?name=www.uboatarchive.net&type=A` returned `65.254.227.224`. Downloads succeeded with `curl --resolve www.uboatarchive.net:443:65.254.227.224`; the requested hostname, SNI, and normal TLS certificate validation were retained. No certificate-verification bypass or hosts-file change was used. The address is a retrieval detail, not a permanent DNS setting.

The reports are historical US Navy material hosted by a third-party archive. Source retrieval does not clear rights for reusing archive presentation, individual photographs, MSI photography, or Skizzenbuch plates in the game. The Skizzenbuch and its rights remain outside this delivery. No game data, codex claims, tuning, or save state was changed during this task.
