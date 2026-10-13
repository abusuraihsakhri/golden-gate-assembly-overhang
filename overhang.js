/* Deterministic overhang sequence screening, not an empirical ligation-fidelity model. */
(function (root) {
  "use strict";
  const DNA = /^[ACGT]{4}$/;
  const complement = { A: "T", C: "G", G: "C", T: "A" };
  function reverseComplement(seq) {
    return seq.toUpperCase().split("").reverse().map(base => complement[base] || "?").join("");
  }
  function parseList(text) {
    return String(text).toUpperCase().split(/[\s,;]+/).map(s => s.trim()).filter(Boolean);
  }
  function gcPercent(seq) {
    return 100 * seq.split("").filter(base => base === "C" || base === "G").length / seq.length;
  }
  function distance(a, b) {
    if (a.length !== b.length) throw new Error("Equal-length sequences required");
    let diff = 0;
    for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) diff++;
    return diff;
  }
  function homopolymer(seq) { return /(A{3}|C{3}|G{3}|T{3})/.test(seq); }
  function screen(input) {
    const sequences = Array.isArray(input) ? input.map(s => String(s).toUpperCase().trim()) : parseList(input);
    const records = sequences.map((sequence, index) => ({
      index: index + 1, sequence, reverseComplement: DNA.test(sequence) ? reverseComplement(sequence) : "",
      gc: DNA.test(sequence) ? gcPercent(sequence) : null, nearestDistance: null, errors: [], cautions: []
    }));
    for (let i = 0; i < records.length; i++) {
      const row = records[i];
      if (!DNA.test(row.sequence)) { row.errors.push("Use exactly four A/C/G/T bases"); continue; }
      if (row.sequence === row.reverseComplement) row.errors.push("Self-complementary palindrome");
      if (homopolymer(row.sequence)) row.cautions.push("Run of three identical bases");
      if (row.gc < 25 || row.gc > 75) row.cautions.push("Extreme GC content");
      for (let j = 0; j < i; j++) {
        const other = records[j];
        if (!DNA.test(other.sequence)) continue;
        if (row.sequence === other.sequence) {
          row.errors.push("Duplicate of #" + (j + 1));
          other.errors.push("Duplicate of #" + (i + 1));
        }
        if (row.sequence === other.reverseComplement) {
          row.errors.push("Reverse complement of #" + (j + 1));
          other.errors.push("Reverse complement of #" + (i + 1));
        }
      }
      const others = records.filter((r, j) => j !== i && DNA.test(r.sequence));
      if (others.length) {
        row.nearestDistance = Math.min(...others.map(r => Math.min(distance(row.sequence, r.sequence), distance(row.sequence, r.reverseComplement))));
        if (row.nearestDistance < 2) row.cautions.push("Only one base differs from another overhang or its reverse complement");
      }
    }
    return {records, valid: records.length > 0 && records.every(r => r.errors.length === 0),
      errors: records.reduce((n, r) => n + r.errors.length, 0),
      cautions: records.reduce((n, r) => n + r.cautions.length, 0)};
  }
  function generate(count) {
    if (!Number.isInteger(count) || count < 2 || count > 16) throw new Error("Choose 2–16 junctions");
    const bases = "ACGT", candidates = [];
    for (const a of bases) for (const b of bases) for (const c of bases) for (const d of bases) {
      const seq = a + b + c + d;
      if (seq === reverseComplement(seq) || homopolymer(seq) || gcPercent(seq) < 25 || gcPercent(seq) > 75) continue;
      candidates.push(seq);
    }
    const picked = [];
    while (picked.length < count) {
      const eligible = candidates.filter(seq => !picked.includes(seq) && picked.every(other =>
        seq !== reverseComplement(other) && distance(seq, other) >= 2 && distance(seq, reverseComplement(other)) >= 2));
      if (!eligible.length) throw new Error("Cannot find enough overhangs under these rules; choose fewer junctions");
      const score = seq => {
        const closest = picked.length ? Math.min(...picked.map(other =>
          Math.min(distance(seq, other), distance(seq, reverseComplement(other))))) : 4;
        return closest * 10 + 2 - Math.abs(gcPercent(seq) - 50) / 25;
      };
      eligible.sort((a, b) => score(b) - score(a) || a.localeCompare(b));
      picked.push(eligible[0]);
    }
    return picked;
  }
  const api = {reverseComplement, parseList, gcPercent, distance, screen, generate};
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.Overhang = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
