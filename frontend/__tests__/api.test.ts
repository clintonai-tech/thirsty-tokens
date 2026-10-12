/** @jest-environment node */
import { ApiError, streamChat } from "@/lib/api";

function sseResponse(chunks: string[]): Response {
  const encoder = new TextEncoder();
  const body = new ReadableStream({
    start(controller) {
      for (const c of chunks) controller.enqueue(encoder.encode(c));
      controller.close();
    },
  });
  return { ok: true, status: 200, body } as unknown as Response;
}

function errorResponse(status: number, json: unknown): Response {
  return { ok: false, status, json: async () => json } as unknown as Response;
}

const DONE = {
  model: "nova-micro",
  input_tokens: 5,
  output_tokens: 7,
  cost_usd: 0.0001,
  latency_ms: 900,
  ttft_ms: 300,
  tokens_per_sec: 12,
  footprint: { energy_wh: 0.01, carbon_g: 0.002, water_l: 0.00005 },
  equivalents: [],
};

afterEach(() => jest.restoreAllMocks());

describe("streamChat", () => {
  it("streams tokens and returns the done payload, even when events split across chunks", async () => {
    jest
      .spyOn(global, "fetch")
      .mockResolvedValue(
        sseResponse([
          'event: token\ndata: {"text":"Hel"}\n\nevent: tok',
          'en\ndata: {"text":"lo"}\n\n',
          `event: done\ndata: ${JSON.stringify(DONE)}\n\n`,
        ]),
      );
    const tokens: string[] = [];
    const result = await streamChat({
      model: "nova-micro",
      prompt: "hi",
      onToken: (t) => tokens.push(t),
    });
    expect(tokens.join("")).toBe("Hello");
    expect(result.output_tokens).toBe(7);
  });

  it.each([
    ["spend_cap", "spend_cap"],
    ["rate_limit", "rate_limit"],
  ])("maps a 429 with reason %s", async (reason, kind) => {
    jest.spyOn(global, "fetch").mockResolvedValue(errorResponse(429, { detail: "x", reason }));
    await expect(streamChat({ model: "m", prompt: "p", onToken: () => {} })).rejects.toMatchObject({
      kind,
    });
  });

  it("maps 5xx to unavailable and a failed fetch to network", async () => {
    jest.spyOn(global, "fetch").mockResolvedValueOnce(errorResponse(503, {}));
    await expect(streamChat({ model: "m", prompt: "p", onToken: () => {} })).rejects.toMatchObject({
      kind: "unavailable",
    });
    jest.spyOn(global, "fetch").mockRejectedValueOnce(new TypeError("failed"));
    await expect(streamChat({ model: "m", prompt: "p", onToken: () => {} })).rejects.toBeInstanceOf(
      ApiError,
    );
  });

  it("fails when the stream ends without a done event", async () => {
    jest
      .spyOn(global, "fetch")
      .mockResolvedValue(sseResponse(['event: token\ndata: {"text":"a"}\n\n']));
    await expect(streamChat({ model: "m", prompt: "p", onToken: () => {} })).rejects.toMatchObject({
      kind: "unavailable",
    });
  });
});
