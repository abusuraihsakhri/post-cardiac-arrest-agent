/**
 * Adult post-ROSC educational checklist.
 * Flags observations for review, never diagnoses, forecasts outcome, or changes care.
 * AHA 2025 Post-Cardiac Arrest Care: https://cpr.heart.org/en/resuscitation-science/cpr-and-ecc-guidelines/post-cardiac-arrest-care
 */
export const SOURCE_URL = "https://cpr.heart.org/en/resuscitation-science/cpr-and-ecc-guidelines/post-cardiac-arrest-care";

function numberInRange(value, name, min, max) {
  if (value === "" || value === null || value === undefined || !Number.isFinite(Number(value))) {
    throw new Error(name + " must be a finite number.");
  }
  const n = Number(value);
  if (n < min || n > max) throw new Error(name + " must be between " + min + " and " + max + ".");
  return n;
}

export function evaluatePostArrest(input) {
  if (!input || !["yes", "no", "unknown"].includes(input.unresponsive)) {
    throw new Error("Select the response-to-commands status.");
  }
  const temperature = numberInRange(input.temperatureC, "Temperature (°C)", 25, 45);
  const map = numberInRange(input.map, "Mean arterial pressure (mm Hg)", 0, 250);
  const hours = numberInRange(input.temperatureHours, "Temperature-control duration (hours)", 0, 720);
  const notes = [];
  const add = (severity, title, detail) => notes.push({ severity, title, detail });

  if (map < 65) {
    add("review", "MAP below guideline minimum",
      "Observed MAP is below 65 mm Hg. In adults after ROSC, the AHA recommends avoiding hypotension by maintaining MAP at least 65 mm Hg.");
  } else {
    add("information", "MAP reference check",
      "Observed MAP is not below the 65 mm Hg guideline minimum; this alone does not establish hemodynamic adequacy.");
  }

  if (input.unresponsive === "yes") {
    if (temperature < 32 || temperature > 37.5) {
      add("review", "Temperature outside recommended control range",
        "For adults unresponsive to verbal commands after ROSC, the recommended controlled range is 32–37.5 °C.");
    } else {
      add("information", "Temperature reference check",
        "Recorded temperature is within 32–37.5 °C; a single reading does not establish protocol adherence.");
    }
    if (hours < 36) {
      add("review", "Temperature-control duration to review",
        "Recorded duration is below 36 hours. For adults who remain unresponsive after ROSC, maintaining temperature control for at least 36 hours is reasonable.");
    } else {
      add("information", "Temperature-control duration recorded",
        "At least 36 hours are recorded, but duration alone does not establish protocol adherence.");
    }
    add("information", "Neurologic prognostication",
      "Use delayed, multimodal assessment by qualified clinicians; avoid conclusions from a single EEG, examination, biomarker, or early time point. Sedation and temperature can confound findings.");
  } else if (input.unresponsive === "unknown") {
    add("review", "Responsiveness is not established",
      "Confirm response to verbal commands; applicability of the temperature-control recommendations depends on clinical assessment.");
  } else {
    add("information", "Scope of temperature-control rules",
      "The 32–37.5 °C and 36-hour checks here target adults unresponsive to verbal commands after ROSC; do not apply them as a patient-specific treatment order.");
  }
  return {
    context: "Adult post-ROSC educational checklist; not validated clinical decision support",
    status: notes.some(n => n.severity === "review") ? "Observations for clinician review" : "No rule flags in submitted observations",
    observations: notes,
    source: SOURCE_URL
  };
}
