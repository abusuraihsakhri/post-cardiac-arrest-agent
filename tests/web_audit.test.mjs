import test from "node:test";
import assert from "node:assert/strict";
import {evaluatePostArrest, SOURCE_URL} from "../web/audit.mjs";

const patient = {unresponsive:"yes", temperatureC:36.5, map:75, temperatureHours:40};

test("results remain educational, not a clinical clearance", () => {
  const outcome = evaluatePostArrest(patient);
  assert.match(outcome.status, /No rule flags/);
  assert.match(outcome.context, /not validated clinical decision support/);
  assert.equal(outcome.source, SOURCE_URL);
});

test("flags temperature, duration, and MAP observations independently", () => {
  const outcome = evaluatePostArrest({...patient, temperatureC:38.2, map:60, temperatureHours:24});
  const review = outcome.observations.filter(n => n.severity === "review");
  assert.equal(review.length, 3);
  assert.match(outcome.status, /clinician review/);
});

test("does not apply unconscious temperature protocol to responsive patient", () => {
  const outcome = evaluatePostArrest({...patient, unresponsive:"no", temperatureC:38.2, temperatureHours:1});
  assert.equal(outcome.observations.filter(n=>n.severity==="review").length, 0);
});

test("calls for responsiveness confirmation when unknown", () => {
  const outcome = evaluatePostArrest({...patient, unresponsive:"unknown"});
  assert.ok(outcome.observations.some(n => n.title.includes("Responsiveness")));
});

test("rejects invalid, missing, and non-finite measurements", () => {
  for (const temperatureC of ["", "oops", "Infinity", 46, -1]) {
    assert.throws(() => evaluatePostArrest({...patient, temperatureC}), Error);
  }
  for (const map of ["", "NaN", -1, 300]) {
    assert.throws(() => evaluatePostArrest({...patient, map}), Error);
  }
  assert.throws(() => evaluatePostArrest({...patient, temperatureHours:""}), Error);
  assert.throws(() => evaluatePostArrest({...patient, unresponsive:""}), Error);
});

test("36 hours and 65 mm Hg thresholds do not trigger review at equality", () => {
  const outcome = evaluatePostArrest({...patient, temperatureC:37.5, temperatureHours:36, map:65});
  assert.equal(outcome.observations.filter(n=>n.severity==="review").length,0);
});
