"use strict";
const byId = id => document.getElementById(id);
let last = null;
function showMessage(message, kind = "info") {
  const element = byId("message");
  element.textContent = message;
  element.dataset.kind = kind;
}
function cell(row, value) {
  const element = document.createElement("td");
  element.textContent = String(value);
  row.appendChild(element);
}
function render(result) {
  last = result;
  const table = byId("results-body");
  table.replaceChildren();
  for (const record of result.records) {
    const row = document.createElement("tr");
    cell(row, record.index);
    cell(row, record.sequence);
    cell(row, record.reverseComplement || "—");
    cell(row, record.gc === null ? "—" : record.gc.toFixed(0) + "%");
    cell(row, record.nearestDistance === null ? "—" : record.nearestDistance);
    const report = record.errors.length ? "Conflict: " + record.errors.join("; ") :
      record.cautions.length ? "Caution: " + record.cautions.join("; ") : "No rule violations";
    cell(row, report);
    row.className = record.errors.length ? "error" : record.cautions.length ? "warning" : "";
    table.appendChild(row);
  }
  byId("count").textContent = result.records.length;
  byId("errors").textContent = result.errors;
  byId("cautions").textContent = result.cautions;
  byId("download").disabled = !result.records.length;
  showMessage(result.valid ?
    (result.cautions ? "No hard conflicts; review sequence cautions." : "No conflicts detected by these screening rules.") :
    "Resolve the listed conflicts before using the set.", result.valid ? "success" : "error");
}
function screenInput() {
  const sequences = Overhang.parseList(byId("overhangs").value);
  if (!sequences.length) return showMessage("Enter at least one overhang.", "error");
  if (sequences.length > 64) return showMessage("Limit screening to 64 entries.", "error");
  render(Overhang.screen(sequences));
}
function generateInput() {
  try {
    const sequences = Overhang.generate(Number(byId("junction-count").value));
    byId("overhangs").value = sequences.join(", ");
    render(Overhang.screen(sequences));
  } catch (error) { showMessage(error.message, "error"); }
}
function downloadCsv() {
  if (!last || !last.records.length) return;
  const rows = [["index","overhang_5to3","reverse_complement_5to3","gc_percent","nearest_hamming_distance","errors","cautions"]];
  for (const r of last.records) rows.push([
    r.index, r.sequence, r.reverseComplement, r.gc === null ? "" : r.gc,
    r.nearestDistance === null ? "" : r.nearestDistance, r.errors.join("; "), r.cautions.join("; ")
  ]);
  const csv = rows.map(row => row.map(value => '"' + String(value).replace(/"/g, '""') + '"').join(",")).join("\r\n") + "\r\n";
  const url = URL.createObjectURL(new Blob([csv], {type: "text/csv;charset=utf-8"}));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "overhang-screen.csv";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
byId("screen").addEventListener("click", screenInput);
byId("generate").addEventListener("click", generateInput);
byId("download").addEventListener("click", downloadCsv);
byId("overhangs").addEventListener("keydown", event => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") screenInput();
});
screenInput();
