import { describe, expect, it } from "vitest";

import { cn, formatCompact, formatPercent, formatSeconds } from "./index";
import { outlierTone } from "./labels";

describe("formatters", () => {
  it("shortens large numbers", () => {
    expect(formatCompact(184200)).toBe("184.2K");
    expect(formatCompact(1284600)).toBe("1.3M");
  });

  it("signs positive percentages only", () => {
    expect(formatPercent(0.32)).toBe("+32%");
    expect(formatPercent(-0.06)).toBe("-6%");
    expect(formatPercent(0)).toBe("0%");
  });

  it("formats durations", () => {
    expect(formatSeconds(11.4)).toBe("11s");
    expect(formatSeconds(75)).toBe("1m 15s");
  });

  it("lets the later Tailwind class win", () => {
    expect(cn("p-2", "p-4")).toBe("p-4");
  });
});

describe("outlierTone", () => {
  it("ranks by distance from the account median", () => {
    expect(outlierTone(2)).toBe("success");
    expect(outlierTone(1)).toBe("accent");
    expect(outlierTone(0.7)).toBe("neutral");
  });
});
