/* Rep counting for the workout tracker: pose landmarks in, angles and rep events out.
   Used by templates/exercise_workout.html and by static/js/reps.test.js (Node). */
(function (root) {
    // Angle at b (degrees, 0-180) formed by points a-b-c
    function angle(a, b, c) {
        if (!a || !b || !c) return 0;
        const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
        let deg = Math.abs((radians * 180) / Math.PI);
        if (deg > 180) deg = 360 - deg;
        return Math.round(deg);
    }
    const mean = (a, b) => (a + b) / 2;

    // MediaPipe Pose indexes: 0 nose, 11/12 shoulders, 13/14 elbows, 15/16 wrists, 23/24 hips, 25/26 knees, 27/28 ankles.
    // measure(lm) -> { value, left, right, labels: [[landmarkIndex, degrees]] }; thresholds come from the Exercise record.
    const RULES = {
        curl: {
            measure(lm) {
                const left = angle(lm[11], lm[13], lm[15]), right = angle(lm[12], lm[14], lm[16]);
                return { value: mean(left, right), left, right, labels: [[13, left], [14, right]] };
            },
            isUp: (m, ex) => m.value < ex.upAngle,
            isDown: (m, ex) => m.value > ex.downAngle,
            grade: (m, ex) => (m.value < ex.upAngle - 5 ? 'excellent' : m.value < ex.upAngle + 10 ? 'good' : 'partial'),
            upMessage: (q) => (q === 'excellent' ? 'Perfect Form!' : 'Good, pull higher!'),
            downMessage: 'Great! Fully extend and curl again.',
        },
        raise: {
            measure(lm) {
                const left = angle(lm[23], lm[11], lm[13]), right = angle(lm[24], lm[12], lm[14]);
                return { value: mean(left, right), left, right, labels: [[11, left], [12, right]] };
            },
            isUp: (m, ex) => m.value > ex.upAngle,
            isDown: (m, ex) => m.value < ex.downAngle,
            grade: (m, ex) => (m.value > ex.upAngle + 5 ? 'excellent' : m.value > ex.upAngle - 10 ? 'good' : 'partial'),
            upMessage: () => 'Good lift! Controlled descent now.',
            // Shoulders creeping up toward the ears
            check: (lm) => (mean(lm[11].y, lm[12].y) < lm[0].y + 0.05 ? "DON'T SHRUG!" : null),
        },
        jack: {
            measure(lm) {
                const legs = mean(angle(lm[11], lm[23], lm[25]), angle(lm[12], lm[24], lm[26]));
                const arms = mean(angle(lm[23], lm[11], lm[13]), angle(lm[24], lm[12], lm[14]));
                return { value: arms, left: arms, right: legs, labels: [] };
            },
            // Top of a jack: arms up AND legs spread (hip angle closes); rest: arms down AND legs together
            isUp: (m, ex) => m.left > ex.upAngle && m.right < 155,
            isDown: (m, ex) => m.left < ex.downAngle && m.right > 165,
            grade: () => 'excellent',
            upMessage: () => 'Keep moving! Dynamic tempo!',
        },
    };

    // exercise: { rule, upAngle, downAngle }. Returns a counter whose update() reports what happened this frame.
    function createRepCounter(exercise) {
        const rule = RULES[exercise.rule];
        if (!rule) throw new Error('Unknown exercise rule: ' + exercise.rule);
        // null until the rest position is seen, so starting mid-movement (e.g. arms already up) doesn't count a rep
        let stage = null;
        return {
            get stage() { return stage; },
            reset() { stage = null; },
            update(lm) {
                const m = rule.measure(lm);
                const out = { measure: m, diff: Math.abs(m.left - m.right), rep: null, transition: false,
                              feedback: rule.check ? rule.check(lm) : null };
                if (rule.isDown(m, exercise)) {
                    if (stage === 'up') {
                        out.transition = true;
                        out.feedback = out.feedback || rule.downMessage || null;
                    }
                    stage = 'down';
                }
                if (rule.isUp(m, exercise) && stage === 'down') {
                    stage = 'up';
                    const quality = rule.grade(m, exercise);
                    out.rep = { quality, angle: m.value };
                    out.feedback = rule.upMessage(quality);
                }
                out.stage = stage;
                return out;
            },
        };
    }

    const api = { angle, RULES, createRepCounter };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    else root.RepCounter = api;
})(this);
