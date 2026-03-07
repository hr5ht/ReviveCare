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
    const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
    // How far an arm has risen from hanging straight down (0) to shoulder height (90) or overhead (180).
    // `len` is the longest shoulder-wrist distance seen, i.e. the arm at rest, which corrects for the arm
    // pointing toward the camera (it looks shorter in 2D) during a forward raise.
    function elevation(shoulder, wrist, len) {
        return Math.round((Math.acos(Math.max(-1, Math.min(1, (wrist.y - shoulder.y) / len))) * 180) / Math.PI);
    }

    // MediaPipe Pose indexes: 0 nose, 11/12 shoulders, 13/14 elbows, 15/16 wrists, 23/24 hips, 25/26 knees, 27/28 ankles.
    // measure(lm) -> { value, left, right, labels: [[landmarkIndex, degrees]] }; thresholds come from the Exercise record.
    const RULES = {
        curl: {
            measure(lm) {
                const left = angle(lm[11], lm[13], lm[15]), right = angle(lm[12], lm[14], lm[16]);
                return { value: mean(left, right), left, right, labels: [[13, left], [14, right]] };
            },
            // Both arms must pass each threshold, so curling one arm and half-curling the other doesn't count
            isUp: (m, ex) => Math.max(m.left, m.right) < ex.upAngle,
            isDown: (m, ex) => Math.min(m.left, m.right) > ex.downAngle,
            better: (a, b) => (Math.max(b.left, b.right) < Math.max(a.left, a.right) ? b : a),  // judged by the weaker arm
            grade: (m, ex) => {
                const weaker = Math.max(m.left, m.right);
                return weaker < ex.upAngle - 5 ? 'excellent' : weaker < ex.upAngle + 10 ? 'good' : 'partial';
            },
            check(lm) {
                const left = angle(lm[11], lm[13], lm[15]), right = angle(lm[12], lm[14], lm[16]);
                return Math.abs(left - right) > 40 && Math.min(left, right) < 90 ? 'Curl both arms together' : null;
            },
            repMessage: 'Nice curl! Now lower all the way.',
            gradeMessages: { excellent: 'Perfect Form!', good: 'Good, pull a little higher next time.', partial: 'Try a fuller curl.' },
        },
        raise: {
            measure(lm) {
                const left = angle(lm[23], lm[11], lm[13]), right = angle(lm[24], lm[12], lm[14]);
                return { value: mean(left, right), left, right, labels: [[11, left], [12, right]] };
            },
            isUp: (m, ex) => m.value > ex.upAngle,
            isDown: (m, ex) => m.value < ex.downAngle,
            better: (a, b) => (b.value > a.value ? b : a),
            grade: (m, ex) => (m.value > ex.upAngle + 5 ? 'excellent' : m.value > ex.upAngle - 10 ? 'good' : 'partial'),
            repMessage: 'Good lift! Controlled descent now.',
            gradeMessages: { excellent: 'Great height!', good: 'Good, lift a little higher.', partial: 'Raise to shoulder height.' },
            // Shoulders creeping up toward the ears
            check: (lm) => (mean(lm[11].y, lm[12].y) < lm[0].y + 0.05 ? "DON'T SHRUG!" : null),
        },
        squat: {
            measure(lm) {
                const left = angle(lm[23], lm[25], lm[27]), right = angle(lm[24], lm[26], lm[28]);
                return { value: mean(left, right), left, right, labels: [[25, left], [26, right]] };
            },
            // Knees bend (angle closes) on both legs; standing tall resets
            isUp: (m, ex) => Math.max(m.left, m.right) < ex.upAngle,
            isDown: (m, ex) => Math.min(m.left, m.right) > ex.downAngle,
            better: (a, b) => (Math.max(b.left, b.right) < Math.max(a.left, a.right) ? b : a),
            grade: (m, ex) => {
                const depth = Math.max(m.left, m.right);
                return depth < ex.upAngle - 10 ? 'excellent' : depth < ex.upAngle + 5 ? 'good' : 'partial';
            },
            repMessage: 'Good depth! Push up through your heels.',
            gradeMessages: { excellent: 'Deep and controlled!', good: 'Good, sit a little lower next time.', partial: 'Try to bend your knees more.' },
        },
        front: {
            measure(lm, ctx) {
                ctx.leftLen = Math.max(ctx.leftLen || 0, dist(lm[11], lm[15]));
                ctx.rightLen = Math.max(ctx.rightLen || 0, dist(lm[12], lm[16]));
                const left = elevation(lm[11], lm[15], ctx.leftLen), right = elevation(lm[12], lm[16], ctx.rightLen);
                return { value: mean(left, right), left, right, labels: [[11, left], [12, right]] };
            },
            isUp: (m, ex) => m.value > ex.upAngle,
            isDown: (m, ex) => m.value < ex.downAngle,
            better: (a, b) => (b.value > a.value ? b : a),
            grade: (m, ex) => (m.value > ex.upAngle + 5 ? 'excellent' : m.value > ex.upAngle - 10 ? 'good' : 'partial'),
            repMessage: 'Nice raise! Lower with control.',
            gradeMessages: { excellent: 'Great height!', good: 'Good, lift a little higher.', partial: 'Raise to shoulder height.' },
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
            // Best jack = highest arms; graded on arm height and how wide the legs opened
            better: (a, b) => (b.left > a.left ? { ...b, right: Math.min(a.right, b.right) } : { ...a, right: Math.min(a.right, b.right) }),
            grade: (m, ex) => (m.left > ex.upAngle + 12 && m.right < 145 ? 'excellent' : m.left > ex.upAngle + 5 ? 'good' : 'partial'),
            repMessage: 'Keep moving! Dynamic tempo!',
            gradeMessages: { excellent: 'Full jack, great!', good: 'Good, reach higher overhead.', partial: 'Arms higher and feet wider.' },
        },
    };

    // exercise: { rule, upAngle, downAngle }. update(landmarks) reports what happened this frame:
    //   rep    - the threshold was crossed: count it now so feedback is instant
    //   graded - the patient is back at rest: the rep's quality, judged at its best (peak) position
    function createRepCounter(exercise) {
        const rule = RULES[exercise.rule];
        if (!rule) throw new Error('Unknown exercise rule: ' + exercise.rule);
        // null until the rest position is seen, so starting mid-movement (e.g. arms already up) doesn't count a rep
        let stage = null, peak = null, ctx = {};  // ctx: per-session memory for rules (e.g. resting arm length)
        return {
            get stage() { return stage; },
            reset() { stage = null; peak = null; ctx = {}; },
            update(lm) {
                const m = rule.measure(lm, ctx);
                const out = { measure: m, diff: Math.abs(m.left - m.right), rep: null, graded: null,
                              feedback: rule.check ? rule.check(lm) : null };
                if (stage === 'up') peak = rule.better(peak, m);
                if (rule.isDown(m, exercise)) {
                    if (stage === 'up') {
                        const quality = rule.grade(peak, exercise);
                        out.graded = { quality, angle: peak.value };
                        out.feedback = out.feedback || rule.gradeMessages[quality];
                    }
                    stage = 'down';
                }
                if (rule.isUp(m, exercise) && stage === 'down') {
                    stage = 'up';
                    peak = m;
                    out.rep = { angle: m.value };
                    out.feedback = out.feedback || rule.repMessage;
                }
                out.stage = stage;
                return out;
            },
        };
    }

    const api = { angle, elevation, RULES, createRepCounter };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    else root.RepCounter = api;
})(this);
