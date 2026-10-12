import { parseSse } from "@/lib/sse";

describe("parseSse", () => {
  it("parses complete events and keeps the partial remainder", () => {
    const { events, rest } = parseSse(
      'event: token\ndata: {"text":"Hi"}\n\nevent: token\ndata: {"te',
    );
    expect(events).toEqual([{ event: "token", data: '{"text":"Hi"}' }]);
    expect(rest).toBe('event: token\ndata: {"te');
  });

  it("handles CRLF and an event split across chunks", () => {
    const first = parseSse("event: done\r\ndata: {}\r\n");
    expect(first.events).toEqual([]);
    const second = parseSse(first.rest + "\r\n");
    expect(second.events).toEqual([{ event: "done", data: "{}" }]);
  });
});
