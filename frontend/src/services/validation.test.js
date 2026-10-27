import { describe, expect, it } from "vitest";
import { FEATURES, toPayload, validateAll, validateField } from "./validation.js";

describe("validateField", () => {
  it("accepts finite numbers", () => {
    expect(validateField("V1", "-1.5")).toBeNull();
    expect(validateField("Amount", "149.62")).toBeNull();
    expect(validateField("Time", "1e3")).toBeNull();
  });
  it("rejects empty, text, NaN and Infinity", () => {
    expect(validateField("V1", "")).toBe("Required.");
    expect(validateField("V1", "abc")).toMatch(/finite/);
    expect(validateField("V1", "NaN")).toMatch(/finite/);
    expect(validateField("V1", "Infinity")).toMatch(/finite/);
  });
  it("enforces bounds", () => {
    expect(validateField("Amount", "-1")).toMatch(/between/);
    expect(validateField("Time", "-5")).toMatch(/between/);
    expect(validateField("V9", "5000")).toMatch(/between/);
  });
});

describe("validateAll / toPayload", () => {
  const full = Object.fromEntries(FEATURES.map((f) => [f, "1"]));
  it("has 30 features and passes when complete", () => {
    expect(FEATURES).toHaveLength(30);
    expect(validateAll(full)).toEqual({});
  });
  it("flags every missing field", () => {
    expect(Object.keys(validateAll({}))).toHaveLength(30);
  });
  it("builds a numeric payload in feature order", () => {
    const p = toPayload(full);
    expect(Object.keys(p)).toEqual(FEATURES);
    expect(p.V1).toBe(1);
  });
});
