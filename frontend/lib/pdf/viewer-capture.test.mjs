import test from "node:test";
import assert from "node:assert/strict";

import { extractViewerCanvasDataUrl } from "./viewer-capture.mjs";

test("extractViewerCanvasDataUrl prefers a nested canvas data URL", () => {
  const fakeCanvas = {
    toDataURL(format) {
      assert.equal(format, "image/png");
      return "data:image/png;base64,abc";
    },
  };
  const fakeNode = {
    querySelector(selector) {
      assert.equal(selector, "canvas");
      return fakeCanvas;
    },
  };

  assert.equal(extractViewerCanvasDataUrl(fakeNode), "data:image/png;base64,abc");
});

test("extractViewerCanvasDataUrl returns null when canvas is missing", () => {
  const fakeNode = {
    querySelector() {
      return null;
    },
  };

  assert.equal(extractViewerCanvasDataUrl(fakeNode), null);
});
