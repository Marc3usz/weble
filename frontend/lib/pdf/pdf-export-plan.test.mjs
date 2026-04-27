import test from "node:test";
import assert from "node:assert/strict";

import {
  buildPdfFileName,
  summarizePartsForPdf,
  selectStepsForPdf,
} from "./pdf-export-plan.mjs";

test("selectStepsForPdf returns all steps by default", () => {
  const steps = [{ step_number: 1 }, { step_number: 2 }, { step_number: 3 }];

  const selected = selectStepsForPdf(steps);

  assert.deepEqual(selected, steps);
});

test("selectStepsForPdf returns the requested step only", () => {
  const steps = [{ step_number: 1 }, { step_number: 2 }, { step_number: 3 }];

  const selected = selectStepsForPdf(steps, 1);

  assert.deepEqual(selected, [{ step_number: 2 }]);
});

test("buildPdfFileName distinguishes full export from single step", () => {
  assert.equal(buildPdfFileName("model-123"), "weble-model-123-instrukcja.pdf");
  assert.equal(
    buildPdfFileName("model-123", 4),
    "weble-model-123-krok-4.pdf"
  );
});

test("summarizePartsForPdf adds fallback labels when name is missing", () => {
  const parts = [
    { id: "A", quantity: 2, part_type: "panel", dimensions: { width: 10, height: 20, depth: 2 } },
    { id: "B", quantity: 8, part_type: "fastener", dimensions: {} },
  ];

  const summary = summarizePartsForPdf(parts);

  assert.deepEqual(summary, [
    {
      id: "A",
      label: "A",
      quantity: 2,
      typeLabel: "panel",
      dimensionsLabel: "10 x 20 x 2 mm",
    },
    {
      id: "B",
      label: "B",
      quantity: 8,
      typeLabel: "fastener",
      dimensionsLabel: "-",
    },
  ]);
});
