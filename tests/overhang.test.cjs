"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const o = require("../overhang.js");
test("reverse complement", () => assert.equal(o.reverseComplement("ATGC"), "GCAT"));
test("separator parsing", () => assert.deepEqual(o.parseList(" atgc, GCTA\nTTAG;CGAT "), ["ATGC","GCTA","TTAG","CGAT"]));
test("invalid nucleotides and lengths rejected", () => {
  const result = o.screen("ATGN,AAA");
  assert.equal(result.valid, false);
  assert.equal(result.errors, 2);
});
test("duplicate, complementary and palindromic overlaps rejected", () => {
  assert.equal(o.screen("AATG,CATT").valid, false);
  assert.equal(o.screen("AATG,AATG").valid, false);
  assert.equal(o.screen("ATAT").valid, false);
});
test("distance uses sequence and reverse-complement orientation", () => {
  assert.equal(o.distance("AAAA", "AAAT"), 1);
  assert.equal(o.screen("AATG,CATG").records[0].nearestDistance, 1);
});
test("generator returns a reproducible screened set", () => {
  const set = o.generate(6);
  assert.deepEqual(set, o.generate(6));
  assert.equal(set.length, 6);
  const result = o.screen(set);
  assert.equal(result.valid, true);
  assert.equal(result.cautions, 0);
  assert.ok(result.records.every(row => row.nearestDistance >= 2));
});
test("generation rejects invalid count", () => {
  assert.throws(() => o.generate(1));
  assert.throws(() => o.generate(17));
  assert.throws(() => o.generate(2.5));
});
