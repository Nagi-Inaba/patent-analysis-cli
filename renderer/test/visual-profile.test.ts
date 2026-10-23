import { describe, expect, it } from "vitest";

async function loadVisualProfile() {
  try {
    const modulePath = "../src/visual-profile.ts";
    return { loaded: true, module: await import(modulePath) } as const;
  } catch {
    return { loaded: false } as const;
  }
}

describe("renderer visual profile", () => {
  it("exports the literal immutable Japanese ranking profile", async () => {
    const loaded = await loadVisualProfile();

    expect(loaded).toEqual({
      loaded: true,
      module: expect.objectContaining({
        RENDER_PROFILE_ID: "ranking-svg-ja-jp-node24-echarts6.v1",
        VISUAL_PROFILE: {
          width: 1200,
          height: {
            minimum: 675,
            base: 160,
            per_row: 36,
            row_count: { minimum: 0, maximum: 101 }
          },
          font_family: "Yu Gothic UI, Yu Gothic, Meiryo, sans-serif",
          colors: {
            background: "#FFFFFF",
            positive: "#2563EB",
            negative: "#DC2626",
            remainder: "#94A3B8",
            text: "#0F172A",
            grid: "#E2E8F0"
          },
          remainder_border: "dashed",
          animation: false,
          ssr: true,
          axis_label_max_graphemes: 28,
          echarts_version: "6.1.0",
          source_order: "preserved",
          empty_state_text: "表示できるランキングデータがありません"
        }
      })
    });
    if (!loaded.loaded) return;

    expect(Object.isFrozen(loaded.module.VISUAL_PROFILE)).toBe(true);
    expect(Object.isFrozen(loaded.module.VISUAL_PROFILE.height)).toBe(true);
    expect(Object.isFrozen(loaded.module.VISUAL_PROFILE.height.row_count)).toBe(true);
    expect(Object.isFrozen(loaded.module.VISUAL_PROFILE.colors)).toBe(true);
    expect(loaded.module.VISUAL_PROFILE.colors.background).toBe("#FFFFFF");
  });

  it("binds height to the exact row-count formula through the 101-row boundary", async () => {
    const loaded = await loadVisualProfile();
    expect(loaded.loaded).toBe(true);
    if (!loaded.loaded) return;
    const profile = loaded.module.VISUAL_PROFILE;
    const heightFor = (rows: number) => Math.max(
      profile.height.minimum,
      profile.height.base + profile.height.per_row * rows
    );

    expect([0, 14, 15, 101].map(heightFor)).toEqual([675, 675, 700, 3796]);
  });
});
