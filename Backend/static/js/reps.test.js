// Run: node --test static/js/   (from Backend/). Fixtures are MediaPipe Pose landmarks recorded from the demo videos.
const test = require('node:test');
const assert = require('node:assert/strict');
const { angle, createRepCounter } = require('./reps.js');

// Same thresholds as the seeded Exercise rows (Patients migrations 0019 + 0022)
const EXERCISES = {
    'bicep-curl': { rule: 'curl', upAngle: 60, downAngle: 160 },
    'lateral-raise': { rule: 'raise', upAngle: 85, downAngle: 30 },
    'jumping-jacks': { rule: 'jack', upAngle: 110, downAngle: 50 },
    'arm-raises': { rule: 'raise', upAngle: 85, downAngle: 30 },
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
        if (res.rep) reps.push(res.rep.quality);
    }
    return reps;
}

test('angle() measures the angle at the middle point', () => {
    assert.equal(angle({ x: 0, y: 1 }, { x: 0, y: 0 }, { x: 1, y: 0 }), 90);
    assert.equal(angle({ x: -1, y: 0 }, { x: 0, y: 0 }, { x: 1, y: 0 }), 180);
    assert.equal(angle(undefined, { x: 0, y: 0 }, { x: 1, y: 0 }), 0);
});

test('demo bicep curl video counts one full curl', () => {
    assert.equal(run(EXERCISES['bicep-curl'], 'bc').length, 1);
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
    const reps = [170, 40, 40, 40, 170, 40].map((d) => counter.update(arm(d)).rep).filter(Boolean);
    assert.equal(reps.length, 2);
});
