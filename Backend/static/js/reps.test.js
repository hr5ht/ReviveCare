// Run: node --test static/js/   (from Backend/). Fixtures are MediaPipe Pose landmarks recorded from the demo videos.
const test = require('node:test');
const assert = require('node:assert/strict');
const { angle, elevation, createRepCounter } = require('./reps.js');

// Same thresholds as the seeded Exercise rows (Patients migrations 0019 + 0022)
const EXERCISES = {
    'bicep-curl': { rule: 'curl', upAngle: 60, downAngle: 160 },
    'lateral-raise': { rule: 'raise', upAngle: 85, downAngle: 30 },
    'jumping-jacks': { rule: 'jack', upAngle: 110, downAngle: 50 },
    'arm-raises': { rule: 'front', upAngle: 85, downAngle: 30 },
};

function run(exercise, fixture) {
    const { frames } = require(`./fixtures/${fixture}.json`);
    const counter = createRepCounter(exercise);
    const reps = [];
    for (const frame of frames) {
        if (!frame) continue;
        const lm = [];
        for (const [i, [x, y, visibility]] of Object.entries(frame)) lm[+i] = { x, y, visibility };
        const res = counter.update(lm);
        if (res.graded) reps.push(res.graded.quality);
    }
    return reps;
}

test('angle() measures the angle at the middle point', () => {
    assert.equal(angle({ x: 0, y: 1 }, { x: 0, y: 0 }, { x: 1, y: 0 }), 90);
    assert.equal(angle({ x: -1, y: 0 }, { x: 0, y: 0 }, { x: 1, y: 0 }), 180);
    assert.equal(angle(undefined, { x: 0, y: 0 }, { x: 1, y: 0 }), 0);
});

test('demo bicep curl video counts one full curl, graded at its deepest point', () => {
    assert.deepEqual(run(EXERCISES['bicep-curl'], 'bc'), ['excellent']);
});

test('the old 45 degree curl threshold missed the demo curl', () => {
    assert.equal(run({ ...EXERCISES['bicep-curl'], upAngle: 45 }, 'bc').length, 0);
});

test('demo lateral raise video counts two raises', () => {
    assert.equal(run(EXERCISES['lateral-raise'], 'sl').length, 2);
});

test('demo jumping jack video counts the four jacks that start from rest', () => {
    assert.equal(run(EXERCISES['jumping-jacks'], 'jj').length, 4);
});

test('jumping jacks are graded on arm height and leg spread at the top', () => {
    // Demo jacks peak with arms at 125, 121, 120 and 125 degrees (excellent needs > upAngle + 12)
    assert.deepEqual(run(EXERCISES['jumping-jacks'], 'jj'), ['excellent', 'good', 'good', 'excellent']);
    assert.ok(run({ ...EXERCISES['jumping-jacks'], upAngle: 100 }, 'jj').every((q) => q === 'excellent'));
});

test('starting with arms already up does not count a rep', () => {
    assert.equal(run(EXERCISES['arm-raises'], 'ar').length, 0);
});

test('holding the top position counts once', () => {
    const counter = createRepCounter(EXERCISES['bicep-curl']);
    const arm = (elbowDeg) => {
        // Upper arm straight down from the shoulder, forearm rotated to make the elbow angle
        const lm = []; const s = { x: 0.4, y: 0.3 }, e = { x: 0.4, y: 0.5 };
        const bend = (180 - elbowDeg) * Math.PI / 180;  // 0 = forearm straight down
        const w = { x: e.x + 0.2 * Math.sin(bend), y: e.y + 0.2 * Math.cos(bend) };
        lm[11] = lm[12] = s; lm[13] = lm[14] = e; lm[15] = lm[16] = w;
        return lm;
    };
    const frames = [170, 40, 40, 40, 170, 40, 170].map((d) => counter.update(arm(d)));
    assert.equal(frames.filter((f) => f.rep).length, 2);
    assert.equal(frames.filter((f) => f.graded).length, 2);
});

test('front raise elevation corrects for the arm pointing at the camera', () => {
    const shoulder = { x: 0.5, y: 0.3 };
    assert.equal(elevation(shoulder, { x: 0.5, y: 0.6 }, 0.3), 0);     // hanging straight down
    assert.equal(elevation(shoulder, { x: 0.5, y: 0.3 }, 0.3), 90);    // at shoulder height, even though it looks short in 2D
    assert.equal(elevation(shoulder, { x: 0.5, y: 0.0 }, 0.3), 180);   // straight overhead
});

test('front raise counts a rep once the arm comes back down', () => {
    const counter = createRepCounter(EXERCISES['arm-raises']);
    const pose = (wristY) => {
        const lm = []; lm[11] = lm[12] = { x: 0.5, y: 0.3 };
        lm[15] = lm[16] = { x: 0.5, y: wristY };
        return lm;
    };
    // rest (arm 0.3 long) -> shoulder height (looks short: pointing at camera) -> rest
    const frames = [0.6, 0.45, 0.3, 0.29, 0.45, 0.6].map((y) => counter.update(pose(y)));
    assert.equal(frames.filter((f) => f.rep).length, 1);
    assert.deepEqual(frames.filter((f) => f.graded).map((f) => f.graded.quality), ['excellent']);
});
