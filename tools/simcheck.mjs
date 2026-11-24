// Runs the flooding sim from index.html under Node, without a browser.
// Usage: node tools/simcheck.mjs
// Prints what happens in a few scripted scenarios and fails (exit 1) if the tuning targets are missed.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const html = readFileSync(fileURLToPath(new URL('../index.html', import.meta.url)), 'utf8');
const block = id => {
  const m = html.match(new RegExp('<script[^>]*id="' + id + '"[^>]*>([\\s\\S]*?)</script>'));
  if (!m) throw new Error('no script block #' + id);
  return m[1];
};
const data = {
  timeline: JSON.parse(block('data-timeline')),
  compartments: JSON.parse(block('data-compartments')),
  systems: JSON.parse(block('data-systems')),
  scenario: JSON.parse(block('data-scenario')),
  items: JSON.parse(block('data-items')),
  charges: JSON.parse(block('data-charges')),
  act2: JSON.parse(block('data-act2')),
  act3: JSON.parse(block('data-act3')),
  epilogue: JSON.parse(block('data-epilogue'))
};
new Function(block('sim')).call(globalThis);
new Function(block('act')).call(globalThis);
new Function(block('turbulence')).call(globalThis);
const Sim = globalThis.U505Sim, Act = globalThis.U505Act;
const clockToT = (sim, c) => Sim.parseClock(c) - sim.t0;

// The physics checks run on the base boat: no placeholder scuttling valve or charges.
// The Act 2 checks further down run the boat as shipped, placeholders included.
const BASE = { placeholders: false };

// actions: [{ at: 'hh:mm:ss', do: sim => ... }]
function run(name, actions, until = '14:23:00', opts = BASE) {
  const sim = Sim.create(data, opts);
  const end = clockToT(sim, until);
  const todo = actions.map(a => ({ t: clockToT(sim, a.at), fn: a.do })).sort((a, b) => a.t - b.t);
  let maxTrim = 0, bad = false;
  while (sim.s.t < end && sim.s.status !== 'lost') {
    while (todo.length && todo[0].t <= sim.s.t) todo.shift().fn(sim);
    sim.step();
    maxTrim = Math.max(maxTrim, sim.s.trim);
    if (!Number.isFinite(sim.s.rb) || sim.s.V.some(v => !Number.isFinite(v) || v < 0) ||
        sim.s.tankV.some((v, k) => !Number.isFinite(v) || v < 0 || v > sim.tanks[k].cap + 1e-9) || !(sim.s.air >= 0)) { bad = true; break; }
  }
  const s = sim.s;
  // every tonne aboard must have come through a sea opening or been there at the start
  const start = Object.values(data.scenario.initial_water_t).reduce((a, b) => a + b, 0);
  const drift = Math.abs(s.water_t - (start + s.in_t - s.pumped_t));
  const res = { name, sim, lost: s.status === 'lost', lostAt: s.lostAt, zeroAt: s.zeroAt, maxTrim, bad, drift };
  console.log(name.padEnd(46) +
    (res.lost ? 'LOST ' + sim.clock(s.lostAt) + ' (zero reserve ' + sim.clock(s.zeroAt) + ')' : 'afloat at ' + sim.clock()) +
    '  rb ' + s.rb.toFixed(1).padStart(6) + ' t  water ' + s.water_t.toFixed(1).padStart(6) + ' t  max trim ' +
    (maxTrim * 57.2958).toFixed(1) + '°  drift ' + drift.toFixed(3) + ' t');
  return res;
}

const strainer = sim => sim.sources.findIndex(o => o.id === 'sea_strainer');
const cap = sim => { sim.s.sourceOpen[strainer(sim)] = false; };
const shutAll = sim => { sim.s.doorOpen.fill(false); };
const stop = sim => { sim.s.enginesOn = false; };
const pumpAft = sim => { sim.addPump(sim.comps.findIndex(c => c.id === 'aft_torpedo'), data.systems.pumps.handy_billy.rate_m3_per_min); };

console.log('clock starts ' + data.scenario.sim_start + ', boarding party below at ' + data.scenario.boarding_at + '\n');
const nothing = run('do nothing', []);
const cap45 = run('cap strainer 11:45', [{ at: '11:45:00', do: cap }]);
const cap50 = run('cap strainer 11:50', [{ at: '11:50:00', do: cap }]);
const cap45stop = run('cap 11:45, stop engines 11:46', [{ at: '11:45:00', do: cap }, { at: '11:46:00', do: stop }]);
const stopOnly = run('stop engines 11:45, strainer left open', [{ at: '11:45:00', do: stop }]);
const doorsOnly = run('shut every hatch 11:45, strainer left open', [{ at: '11:45:00', do: shutAll }]);
const full = run('cap 11:45, hatches 12:40, pump aft 12:45', [
  { at: '11:45:00', do: cap }, { at: '12:40:00', do: shutAll }, { at: '12:45:00', do: pumpAft }]);
// Retained calibration example. The reports disagree on shutdown: A3 logs 13:18, D confirms 13:38.
// These selected intervention times are hypothetical and do not reconstruct an exact historical route.
const calibration = run('calibration: cap 11:50, engines 12:00, hatches, pump', [
  { at: '11:50:00', do: cap }, { at: '12:00:00', do: stop }, { at: '12:40:00', do: shutAll }, { at: '12:45:00', do: pumpAft }]);

// --- milestone 2: the systems graph
const V = (sim, id) => sim.valveIndex(id);
const set = (id, f) => sim => { sim.s.valve[V(sim, id)] = f; };
// turn a valve by hand at its rated speed, starting at a clock time (one action per 0.5 s)
const byHand = (at, id, dir) => {
  const out = [], s0 = Sim.parseClock(at), v = data.systems.valves.find(x => x.id === id);
  const n = Math.ceil(v.turns / v.turn_rate_per_s / 0.5);
  for (let i = 0; i < n; i++) out.push({ at: Sim.formatClock(s0 + i * 0.5), do: sim => sim.turnValve(V(sim, id), dir * v.turn_rate_per_s * 0.5) });
  return out;
};
const hullValve = run('turn hull valve shut from 11:45 (8 turns)', byHand('11:45:00', 'v_cooling_hull', -1));
const allVents = run('cap 11:45, open every vent 11:46', [{ at: '11:45:00', do: cap },
  { at: '11:46:00', do: set('v_vent_fwd', 1) }, { at: '11:46:00', do: set('v_vent_mid', 1) }, { at: '11:46:00', do: set('v_vent_aft', 1) }]);
const ventBlow = run('cap 11:45, vent fwd 11:46, shut 11:47, blow 11:47', [{ at: '11:45:00', do: cap },
  { at: '11:46:00', do: set('v_vent_fwd', 1) }, { at: '11:47:00', do: set('v_vent_fwd', 0) },
  { at: '11:47:00', do: set('v_blow_fwd', 1) }, { at: '11:49:00', do: set('v_blow_fwd', 0) }]);
const ventFwdOnly = run('cap 11:45, vent fwd 11:46 and leave it', [{ at: '11:45:00', do: cap }, { at: '11:46:00', do: set('v_vent_fwd', 1) }]);
const drainsShut = run('cap 11:45, shut every bilge valve 11:45', [{ at: '11:45:00', do: cap },
  ...['v_drain_bow', 'v_drain_po', 'v_drain_off', 'v_drain_aft'].map(id => ({ at: '11:45:00', do: set(id, 0) }))]);
const ownPump = run('cap 11:45, power + bilge pump 11:50', [{ at: '11:45:00', do: cap },
  { at: '11:50:00', do: sim => { sim.s.power = true; sim.s.fixedPumpOn[0] = true; } }]);
console.log('  vent/blow run: forward tanks end with ' + (ventBlow.sim.s.tankV[0] * 1.025).toFixed(1) + ' t, air left ' + ventBlow.sim.s.air.toFixed(0) + ' m3');
const all = [nothing, cap45, cap50, cap45stop, stopOnly, doorsOnly, full, calibration, hullValve, allVents, ventBlow, ventFwdOnly, drainsShut, ownPump];

// snapshot at boarding, for a feel of what the player walks into
const at = Sim.create(data, BASE); at.advanceTo(data.scenario.boarding_at);
console.log('\nat boarding ' + at.clock() + ': rb ' + at.s.rb.toFixed(1) + ' t, trim ' + (at.s.trim * 57.2958).toFixed(1) +
  '° stern down, keel depth ' + at.s.draught.toFixed(2) + ' m, strainer ' + (at.s.srcQ[strainer(at)] * 1.025 * 60).toFixed(2) + ' t/min');
at.comps.forEach((c, i) => console.log('  ' + c.de.padEnd(20) + (at.s.V[i] * 1.025).toFixed(1).padStart(6) + ' t  ' +
  Math.max(0, at.s.h[i] - at.hull.floor_height_m).toFixed(2) + ' m over the deck plates'));

// --- milestone 3: Act 2 from the selected boarding time (11:46) to the salvage party (12:40)
function playAct(name, actions, opts) {
  const sim = Sim.create(data, opts), act = Act.create(sim, data, opts);
  sim.advanceTo(data.act2.start);
  const todo = actions.map(a => ({ t: clockToT(sim, a.at), fn: a.do })).sort((a, b) => a.t - b.t);
  while (!act.s.ended) {
    while (todo.length && todo[0].t <= sim.s.t) todo.shift().fn(sim, act);
    if (sim.s.t < act.tEnd && sim.s.status !== 'lost') sim.step();
    act.update();
  }
  const done = act.orders().filter(o => o.done).map(o => o.id).join(', ') || 'none';
  console.log(name.padEnd(46) + (act.s.ended === 'won' ? 'WON at ' : 'LOST at ') + sim.clock(act.s.endAt) +
    '  orders done: ' + done + (sim.s.cause ? '  cause: ' + sim.s.cause : ''));
  return { sim, act };
}
const stopDiesels = sim => sim.fuel.forEach(k => { sim.s.valve[k] = 0; });
const allUp = (sim, act) => { act.items.forEach((it, i) => { act.s.items[i] = 'carried'; }); act.deliver(); };
const shutFlood = sim => { sim.s.valve[sim.valveIndex('v_scuttle_placeholder')] = 0; };
const safeCharges = (sim, act) => act.charges.forEach((c, k) => { act.chargeStep(k, 'lead'); act.chargeStep(k, 'detonator'); });
console.log('\nAct 2, boat as shipped (placeholder flood valve and two charges included):');
const historic = playAct('act 2: cap 11:47, flood valve 11:48, charges, diesels, papers', [
  { at: '11:47:00', do: cap }, { at: '11:48:00', do: shutFlood }, { at: '11:52:00', do: safeCharges },
  { at: '11:55:00', do: stopDiesels }, { at: '12:05:00', do: allUp }]);
const capOnly = playAct('act 2: cap 11:47 and nothing else', [{ at: '11:47:00', do: cap }]);
// a player walking from the ladder: everything done, at a realistic pace
const paced = playAct('act 2 paced: cap 11:50, flood 11:56, diesels 12:00, charges 12:05, papers 12:20', [
  { at: '11:50:00', do: cap }, { at: '11:56:00', do: shutFlood }, { at: '12:00:00', do: stopDiesels },
  { at: '12:05:00', do: safeCharges }, { at: '12:20:00', do: allUp }]);
const floodOpen = playAct('act 2 paced but the flood valve left open', [
  { at: '11:50:00', do: cap }, { at: '12:00:00', do: stopDiesels }, { at: '12:05:00', do: safeCharges }, { at: '12:20:00', do: allUp }]);
// The reports disagree on propulsion-stop timing. This is an alternative playable route.
const dieselsFirst = playAct('act 2: diesels first (11:47), strainer 11:50, flood 11:56', [
  { at: '11:47:00', do: stopDiesels }, { at: '11:50:00', do: cap }, { at: '11:56:00', do: shutFlood }]);
const idle = playAct('act 2: do nothing', []);
const chargeWrong = playAct('act 2: detonator before firing lead', [{ at: '11:48:00', do: (sim, act) => act.chargeStep(0, 'detonator') }]);
const base3 = playAct('act 2 without placeholders: cap, diesels, papers', [
  { at: '11:47:00', do: cap }, { at: '11:49:00', do: stopDiesels }, { at: '12:00:00', do: allUp }], BASE);
// --- milestone 5: Act 3 carries on from the paced Act 2 (12:40 to the 14:23 tow), and the 7 June scene
function continueAct3(name, prev, actions) {
  const { sim, act } = prev;
  act.beginAct3();
  const todo = actions.map(a => ({ t: clockToT(sim, a.at), fn: a.do })).sort((a, b) => a.t - b.t);
  while (!act.s.ended) {
    while (todo.length && todo[0].t <= sim.s.t) todo.shift().fn(sim, act);
    if (sim.s.t < act.tEnd && sim.s.status !== 'lost') sim.step();
    act.update();
  }
  console.log(name.padEnd(46) + (act.s.ended === 'won' ? 'WON at ' : 'LOST at ') + sim.clock(act.s.endAt) +
    '  rb ' + sim.s.rb.toFixed(1) + ' t  orders done: ' + (act.orders().filter(o => o.done).map(o => o.id).join(', ') || 'none'));
  return { sim, act };
}
const pacedRun = () => playAct('  (paced act 2 again)', [
  { at: '11:50:00', do: cap }, { at: '11:56:00', do: shutFlood }, { at: '12:00:00', do: stopDiesels },
  { at: '12:05:00', do: safeCharges }, { at: '12:20:00', do: allUp }]);
const shutAft = sim => data.act3.doors.forEach(id => { sim.s.doorOpen[sim.doors.findIndex(d => d.id === id)] = false; });
const rigIn = (...ids) => (sim, act) => ids.forEach(id => {
  if (!act.s.pumpCarried) act.takePump();
  act.rigPump(sim.comps.findIndex(c => c.id === id));
});
console.log('\nAct 3, carrying on from the paced Act 2:');
const act3Good = continueAct3('act 3: pumps aft 12:50, hatches 12:55', pacedRun(), [
  { at: '12:50:00', do: rigIn('aft_torpedo', 'motor') }, { at: '12:55:00', do: shutAft }]);
const act3Idle = continueAct3('act 3: do nothing', pacedRun(), []);
const act3PumpsOnly = continueAct3('act 3: pumps aft 12:50, hatches left open', pacedRun(), [{ at: '12:50:00', do: rigIn('aft_torpedo', 'motor') }]);

const closeForwardAftHatches = sim => ['door_5', 'door_6'].forEach(id => {
  sim.s.doorOpen[sim.doors.findIndex(d => d.id === id)] = false;
});
const dieselWater = sim => sim.s.V[sim.comps.findIndex(c => c.id === 'diesel')] * sim.RHO;
function prototypeBoarding(opts, split) {
  const sim = Sim.create(data, opts), act = Act.create(sim, data, opts);
  sim.advanceTo(data.act2.start);
  act.replayBoarding(split);
  const handedOff = act.s.ended === 'won';
  const inherited = { water: dieselWater(sim), hatchOpen: sim.s.doorOpen[sim.doors.findIndex(d => d.id === 'door_6')] };
  return { sim, act, inherited, handedOff };
}
function playPrototype(opts, split, dieselFirst) {
  const prev = prototypeBoarding(opts, split);
  return continueAct3(`prototype: ${split ? 'diesel pocket' : 'water aft'} / ${dieselFirst ? 'diesel + stern' : 'stern + motor'}`, prev, [
    { at: '12:41:00', do: closeForwardAftHatches },
    { at: '12:42:00', do: rigIn(dieselFirst ? 'diesel' : 'aft_torpedo') },
    { at: '12:44:00', do: rigIn(dieselFirst ? 'aft_torpedo' : 'motor') }
  ]);
}
const prototypes = [{}, BASE].map(opts => {
  const open = prototypeBoarding(opts, false), split = prototypeBoarding(opts, true);
  const before = JSON.stringify(split.sim.s);
  split.act.beginAct3();
  const inherited = before === JSON.stringify(split.sim.s) && open.handedOff && split.handedOff &&
    open.inherited.water < 1 && open.inherited.hatchOpen && split.inherited.water > 20 && !split.inherited.hatchOpen &&
    split.act.salvageSurvey()[1].hatchOpen === false;
  const openAft = playPrototype(opts, false, false), openDiesel = playPrototype(opts, false, true);
  const splitAft = playPrototype(opts, true, false), splitDiesel = playPrototype(opts, true, true);
  return { inherited, openAft, openDiesel, splitAft, splitDiesel };
});
const pumpTrial = prototypeBoarding({}, false);
const { sim: pumpSim, act: pumpAct } = pumpTrial;
const [dieselIntake, motorIntake, sternIntake] = pumpAct.intakes.map(intake => intake.c);
pumpAct.beginAct3();
const dryAct3 = pumpAct.takePump() && !pumpAct.rigPump(dieselIntake) && pumpAct.s.pumpCarried === 1 && pumpSim.s.pumps.length === 0;
const pumpSwap = pumpAct.rigPump(motorIntake) && pumpAct.takePump() && !pumpAct.recoverPump(motorIntake) &&
  pumpAct.rigPump(sternIntake) && pumpAct.recoverPump(motorIntake) && pumpSim.s.pumps.length === 1 &&
  pumpAct.s.rigged[0].pump === 0 && pumpSim.s.pumps[0].c === sternIntake && pumpAct.rigPump(motorIntake) &&
  pumpAct.recoverPump(sternIntake) && pumpAct.stowPump() && pumpAct.s.pumpPile === 1 && pumpAct.s.pumpCarried === 0 &&
  pumpSim.s.pumps.length === 1 && pumpSim.s.pumps[0].c === motorIntake;

const replayHatch = pumpSim.doors.findIndex(door => door.a === dieselIntake && door.b === motorIntake);
const replaySample = (t, water, open) => ({
  t, water: pumpSim.comps.map(room => water[room.id] ?? 0),
  doors: pumpSim.doors.map((_, i) => i === replayHatch ? open : true)
});
const closedReplayFrames = [
  replaySample(5, { diesel: 27 }, true), replaySample(10, { diesel: 26 }, false),
  replaySample(20, { diesel: 25 }, true), replaySample(30, { diesel: 24 }, false),
  replaySample(40, { aft_torpedo: 32 }, false), replaySample(50, { diesel: 6, aft_torpedo: 4 }, false)
];
const replayEvents = [
  { t: 5, text: 'Strainer cover fitted.', kind: 'leak', compartmentId: 'diesel' },
  ...[10, 20, 30].map(t => ({ t, text: 'Motor-room hatch operated.', kind: 'hatch', hatchId: pumpSim.doors[replayHatch].id, open: t === 20 })),
  { t: 40, text: 'Aft pump connected.', kind: 'pump', compartmentId: 'aft_torpedo' }
];
const hatchDecision = Act.towDecision(pumpSim, closedReplayFrames, replayEvents);
const openReplayFrames = [...closedReplayFrames.slice(0, -1), replaySample(50, { diesel: 1, aft_torpedo: 9 }, true)];
const pumpDecision = Act.towDecision(pumpSim, openReplayFrames, replayEvents);
const legacyEvents = replayEvents.map(({ t, text, kind }) => ({ t, text, kind }));
const leakDecision = Act.towDecision(pumpSim, closedReplayFrames, legacyEvents);
const snapshotDecision = Act.towDecision(pumpSim, openReplayFrames, legacyEvents.slice(1));

console.log('\nAct 4, 7 June (settling, no headway):');
function playAwash(name, actions, hours = 40) {
  const sim = Sim.create(data), sc = Act.awash(sim, data).start();
  const rb0 = sim.s.rb, end = hours * 3600;
  const todo = actions.map(a => ({ t: a.after * 60, fn: a.do })).sort((a, b) => a.t - b.t);
  while (!sc.ended && sim.s.t < end) { while (todo.length && todo[0].t <= sim.s.t) todo.shift().fn(sim, sc); sim.step(); sc.update(); }
  const h = sim.s.t / 3600;
  console.log(name.padEnd(46) + (sc.ended || 'still going') + ' after ' + h.toFixed(1) + ' h  (rb at start ' + rb0.toFixed(1) +
    ' t, now ' + sim.s.rb.toFixed(1) + ' t, trim ' + (sim.s.trim * 57.3).toFixed(0) + '°)');
  return { sim, sc, h, rb0 };
}
const awashIdle = playAwash('7 June: no pumps', []);
const awashPumps = playAwash('7 June: three pumps rigged within 10 min', [
  { after: 4, do: (sim, sc) => { sc.takePump(); sc.rigPump(sim.comps.findIndex(c => c.id === 'aft_torpedo'), 0, 0); } },
  { after: 7, do: (sim, sc) => { sc.takePump(); sc.rigPump(sim.comps.findIndex(c => c.id === 'motor'), 0, 0); } },
  { after: 10, do: (sim, sc) => { sc.takePump(); sc.rigPump(sim.comps.findIndex(c => c.id === 'diesel'), 0, 0); } }]);
// at walking pace: three loaded round trips from the ladder, wading aft (about 80, 160, 240 s of real time at x6)
const awashPaced = playAwash('7 June: pumps at +8, +16, +24 min (walking pace)', [
  { after: 8, do: (sim, sc) => { sc.takePump(); sc.rigPump(sim.comps.findIndex(c => c.id === 'aft_torpedo'), 0, 0); } },
  { after: 16, do: (sim, sc) => { sc.takePump(); sc.rigPump(sim.comps.findIndex(c => c.id === 'motor'), 0, 0); } },
  { after: 24, do: (sim, sc) => { sc.takePump(); sc.rigPump(sim.comps.findIndex(c => c.id === 'diesel'), 0, 0); } }]);
// a pump cannot be rigged where there is nothing to pump
const dry = Sim.create(data), drySc = Act.awash(dry, data).start(); drySc.takePump();
const dryRefused = !drySc.rigPump(dry.comps.findIndex(c => c.id === 'bow_torpedo'), 0, 0) && drySc.carried === 1 && drySc.rigged.length === 0;

// Players have to open the hatches to reach the rooms. Flow across the open hatches can leave
// the last room dry and isolate water below the sills after the other pumps draw down their rooms.
const aftRooms = ['diesel', 'motor', 'aft_torpedo'];
const openAft = [5, 6, 7].map((door, i) => ({ after: 1 + i * 2, do: sim => {
  sim.s.doorOpen[sim.doors.findIndex(d => d.id === 'door_' + door)] = true;
} }));
const orders = aftRooms.flatMap(first => aftRooms.filter(room => room !== first).map(second =>
  [first, second, aftRooms.find(room => room !== first && room !== second)]));
let formerlyStranded = false;
const deckRuns = orders.map(order => playAwash('7 June open hatches: ' + order.join(' / '), [
  ...openAft,
  ...order.map((room, i) => ({ after: 8 * (i + 1), do: (sim, sc) => {
    if (!sc.carried) sc.takePump();
    const installed = sc.rigPump(sim.comps.findIndex(c => c.id === room), 0, 0);
    if (order.join('/') === 'aft_torpedo/motor/diesel' && i === 2) formerlyStranded = !installed && sc.carried === 1;
  } })),
  { after: 26, do: (_sim, sc) => sc.beginDeckSupport() }
]));
const deckWithoutPump = drySc.beginDeckSupport();
const onePump = playAwash('7 June open hatches: one aft pump, then deck crew', [
  ...openAft,
  { after: 8, do: (sim, sc) => { sc.takePump(); sc.rigPump(sim.comps.findIndex(c => c.id === 'aft_torpedo'), 0, 0); } },
  { after: 12, do: (_sim, sc) => sc.beginDeckSupport() }
]);

// carrying limits
const cs = Sim.create(data), ca = Act.create(cs, data);
const iEnigma = ca.items.findIndex(i => i.id === 'enigma'), iRadio = ca.items.findIndex(i => i.id === 'radio');
const carryOk = ca.pick(iEnigma) && !ca.pick(iRadio);

const hatchSim = Sim.create(data);
const hatchIndex = hatchSim.doors.findIndex(d => hatchSim.comps[d.a].id === 'diesel' && hatchSim.comps[d.b].id === 'motor');
const hatch = hatchSim.doors[hatchIndex];
hatchSim.startFrom({ engines: false, initial_water_t: { diesel: 12, motor: 25 },
  closed_sources: hatchSim.sources.map(source => source.id), doors_shut: hatchSim.doors.map(door => door.id) });
hatchSim.s.drainOpen.fill(false);
hatchSim.s.doorOpen[hatchIndex] = true;
const beforeHatch = hatchSim.s.V.slice();
hatchSim.step();
const hatchFlow = hatchSim.s.doorQ[hatchIndex];
const hatchFlowMatchesTransfer = hatchFlow < 0 &&
  Math.abs(hatchSim.s.V[hatch.a] - beforeHatch[hatch.a] + hatchFlow * hatchSim.DT) < 1e-9 &&
  Math.abs(hatchSim.s.V[hatch.b] - beforeHatch[hatch.b] - hatchFlow * hatchSim.DT) < 1e-9;
hatchSim.s.doorOpen[hatchIndex] = false;
hatchSim.step();

const basin = globalThis.U505Turbulence.create();
function basinPulse() {
  basin.impulse(0, 0, .85, 1.6);
  let peak = 0, travelled = 0;
  for (let i = 0; i < 240; i++) {
    basin.step(1 / 120, 1.1);
    peak = Math.max(peak, Math.abs(basin.sample(0, 0)));
    travelled = Math.max(travelled, Math.abs(basin.sample(1.6, 0)));
  }
  return { peak, travelled };
}
const pulse = basinPulse();
const pulseField = basin.displacement.slice();
basin.reset();
const basinReset = basin.displacement.every(value => value === 0) && basin.velocity.every(value => value === 0);
basinPulse();
const basinRepeatable = basin.displacement.every((value, index) => value === pulseField[index]);
for (let i = 0; i < 1200; i++) basin.step(1 / 120, 1.1);
const basinSettled = basin.displacement.every(value => Math.abs(value) < pulse.peak * .05);

const checks = [
  ['no NaN, negative or overfull volumes, air never negative', all.every(r => !r.bad)],
  ['water is conserved (drift < 0.05 t)', all.every(r => r.drift < 0.05)],
  ['signed hatch flow matches the transferred volume and clears on closure', hatchFlowMatchesTransfer && hatchSim.s.doorQ[hatchIndex] === 0],
  ['basin pulse propagates and settles', pulse.peak > .025 && pulse.travelled > .001 && basinSettled],
  ['basin reset clears motion and reproduces the same pulse', basinReset && basinRepeatable],
  ['doing nothing loses the boat between 11:52 and 12:08', nothing.lost &&
    nothing.lostAt >= clockToT(nothing.sim, '11:52:00') && nothing.lostAt <= clockToT(nothing.sim, '12:08:00')],
  ['capping the strainer at 11:45 keeps her up until the salvage party (12:40)', !cap45.lost ||
    cap45.lostAt > clockToT(cap45.sim, '12:40:00')],
  ['cap, hatches and a pump keep her up until the tow (14:23)', !full.lost],
  ['stopping the engines with the strainer open is worse than doing nothing', stopOnly.lost && stopOnly.lostAt < nothing.lostAt],
  ['turning the hull valve shut from 11:45 keeps her up until 12:40', !hullValve.lost || hullValve.lostAt > clockToT(hullValve.sim, '12:40:00')],
  ['opening every vent loses her within 3 minutes', allVents.lost && allVents.lostAt <= clockToT(allVents.sim, '11:49:00')],
  ['a wrongly opened vent can be shut and blown out again', !ventBlow.lost && ventBlow.sim.s.tankV[0] * 1.025 < 1],
  ['shutting the bilge valves does no harm on its own', !drainsShut.lost],
  ['the calibration example (cap 11:50, engines 12:00, hatches, pump) is afloat at the 14:23 tow', !calibration.lost],
  ['act 2 at a realistic pace, everything done, is won with at least 5 t of reserve', paced.act.s.ended === 'won' && paced.sim.s.rb >= 5],
  ['act 2: leaving the flood valve open with the diesels stopped loses her before 12:40', floodOpen.act.s.ended === 'lost'],
  ['act 2 as shipped has all five orders; without placeholders, three', historic.act.orders().length === 5 && base3.act.orders().length === 3],
  ['act 2 with every objective completed is won at 12:40 with every order done', historic.act.s.ended === 'won' &&
    historic.act.orders().every(o => o.done)],
  // At the corrected later boarding time, nonlinear flooding/equalization can reverse the terminal
  // reserve ranking. Guard the alternative route's viability instead of treating that ranking as history.
  ['act 2: propulsion first, then inflow, remains a winnable alternative with positive reserve',
    dieselsFirst.act.s.ended === 'won' && dieselsFirst.act.done.diesels() && dieselsFirst.act.done.inflow() && dieselsFirst.sim.s.rb > 0],
  ['act 2: doing nothing loses her between 11:50 and 12:08', idle.act.s.ended === 'lost' &&
    idle.act.s.endAt >= clockToT(idle.sim, '11:50:00') && idle.act.s.endAt <= clockToT(idle.sim, '12:08:00')],
  ['act 2: the detonator before the firing lead sets a charge off', chargeWrong.act.s.ended === 'lost' && chargeWrong.sim.s.cause === 'charge'],
  ['act 2 without placeholders still wins with three orders done', base3.act.s.ended === 'won' && base3.act.orders().every(o => o.done)],
  ['carrying: the Enigma fits, the radio on top of it does not', carryOk],
  ['act 3: hatches and pumps after the paced act 2 hold her up to the 14:23 tow', act3Good.act.s.ended === 'won'],
  // Measured, not assumed: once the after room is flooded to the outside waterline the seep stops, so idling
  // in Act 3 does not sink her; the pumps and hatches show up as margin at the tow.
  ['act 3: hatches and pumps leave far more reserve at the tow than doing nothing', act3Good.sim.s.rb > act3Idle.sim.s.rb + 15],
  ['prototype: Act 3 inherits two materially different flood states with and without placeholders', prototypes.every(run => run.inherited)],
  ['prototype: targeting both aft rooms earns at least 20 t more reserve when the diesel room drained', prototypes.every(run =>
    run.openAft.act.s.ended === 'won' && run.openAft.sim.s.rb - run.openDiesel.sim.s.rb >= 20)],
  ['prototype: targeting the isolated diesel pocket removes at least 20 t more from that room', prototypes.every(run =>
    run.splitDiesel.act.s.ended === 'won' && dieselWater(run.splitAft.sim) - dieselWater(run.splitDiesel.sim) >= 20)],
  ['prototype: a dry intake keeps the pump and a recovered pump can be redeployed or stowed', dryAct3 && pumpSwap],
  ['tow replay: last motor-hatch closure that remains shut uses recorded diesel-room volumes', hatchDecision?.eventIndex === 3 &&
    hatchDecision.c === dieselIntake && hatchDecision.frame.water[dieselIntake] === 24 && hatchDecision.tow.water[dieselIntake] === 6],
  ['tow replay: an open motor hatch falls back to recorded volumes for the first connected intake', pumpDecision?.eventIndex === 4 &&
    pumpDecision.c === sternIntake && pumpDecision.frame.water[sternIntake] === 32 && pumpDecision.tow.water[sternIntake] === 9],
  ['tow replay: text-only events can use the recorded leak bookmark or the final frame', leakDecision?.eventIndex === 0 &&
    leakDecision.c === dieselIntake && leakDecision.frame.water[dieselIntake] === 27 &&
    snapshotDecision?.eventIndex === -1 && snapshotDecision.c === sternIntake && snapshotDecision.frame === undefined],
  ['7 June: she starts nearly awash but still afloat', awashIdle.rb0 > 0 && awashIdle.rb0 < 15],
  ['7 June: with no pumps she founders', awashIdle.sc.ended === 'lost'],
  ['7 June: three electric pumps reach the model buoyancy target (within 40 h)', awashPumps.sc.ended === 'won'],
  ['7 June: walking pace and all six open-hatch orders recover, including the dry-last stall',
    awashPaced.sc.ended === 'won' && formerlyStranded && deckRuns.every(run => run.sc.ended === 'won') && onePump.sc.ended === 'won'],
  ['pumps: dry placement retains the pump, and deck help requires a rigged pump', dryRefused && !deckWithoutPump]
];
console.log('');
let failed = 0;
for (const [text, ok] of checks) { console.log((ok ? 'ok    ' : 'FAIL  ') + text); if (!ok) failed++; }
process.exit(failed ? 1 : 0);
