import {evaluatePostArrest} from "./audit.mjs";
  const form = document.getElementById("audit-form");
  const resultNode = document.getElementById("results");
  const statusNode = document.getElementById("status");
  const errorNode = document.getElementById("error");
  const download = document.getElementById("download");
  let currentResult = null;
  form.addEventListener("submit", event => {
    event.preventDefault();
    errorNode.textContent = "";
    const raw = {
      unresponsive: document.getElementById("unresponsive").value,
      temperatureC: document.getElementById("temperature").value,
      temperatureHours: document.getElementById("duration").value,
      map: document.getElementById("map").value
    };
    try {
      currentResult = evaluatePostArrest(raw);
      statusNode.textContent = currentResult.status;
      resultNode.replaceChildren();
      for (const observation of currentResult.observations) {
        const item = document.createElement("article");
        item.className = "result";
        const heading = document.createElement("h3");
        heading.className = observation.severity === "review" ? "review" : "info";
        heading.textContent = observation.title;
        const description = document.createElement("p");
        description.textContent = observation.detail;
        item.append(heading, description);
        resultNode.append(item);
      }
      download.disabled = false;
    } catch (error) {
      currentResult = null;
      resultNode.replaceChildren();
      statusNode.textContent = "No assessment generated";
      errorNode.textContent = error.message;
      download.disabled = true;
    }
  });
  form.addEventListener("reset", () => {
    currentResult = null;
    statusNode.textContent = "No observations evaluated";
    errorNode.textContent = "";
    resultNode.textContent = "No observations evaluated.";
    download.disabled = true;
  });
  download.addEventListener("click", () => {
    if (!currentResult) return;
    const blob = new Blob([JSON.stringify(currentResult, null, 2)], {type:"application/json"});
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "post-arrest-observation-checklist.json";
    anchor.click();
    URL.revokeObjectURL(url);
  });

