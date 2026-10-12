import { parseSse } from "@/lib/sse";
import type { ChatResult, ModelInfo } from "@/lib/types";

const DEFAULT_API_URL = "http://localhost:8000";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_URL).replace(/\/+$/, "");

/** Mirrors the server's TT_MAX_INPUT_CHARS default; the server re-checks it. */
export const MAX_PROMPT_CHARS = 2000;

export type ApiErrorKind =
  "spend_cap" | "rate_limit" | "invalid" | "unavailable" | "network" | "unknown";

export class ApiError extends Error {
  constructor(
    readonly kind: ApiErrorKind,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const MESSAGES: Record<ApiErrorKind, string> = {
  spend_cap:
    "The demo has used up today's budget. It resets at midnight UTC, so please try again tomorrow.",
  rate_limit:
    "You have reached today's request limit for this demo. It resets at midnight UTC, so try again tomorrow.",
  invalid: "That request was not accepted. Check the prompt and the model, then try again.",
  unavailable: "The model is busy or unavailable right now. Wait a moment, or pick another model.",
  network: "Could not reach the server. Check your connection and try again.",
  unknown: "Something went wrong. Try again in a moment.",
};

export function messageFor(kind: ApiErrorKind): string {
  return MESSAGES[kind];
}

async function errorFromResponse(res: Response): Promise<ApiError> {
  let reason: unknown;
  try {
    reason = ((await res.json()) as { reason?: unknown }).reason;
  } catch {
    // body was not JSON; fall back to the status code
  }
  if (res.status === 429) {
    const kind = reason === "spend_cap" ? "spend_cap" : "rate_limit";
    return new ApiError(kind, MESSAGES[kind]);
  }
  if (res.status >= 400 && res.status < 500) return new ApiError("invalid", MESSAGES.invalid);
  if (res.status >= 500) return new ApiError("unavailable", MESSAGES.unavailable);
  return new ApiError("unknown", MESSAGES.unknown);
}

export async function fetchModels(signal?: AbortSignal): Promise<ModelInfo[]> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/models`, { signal });
  } catch {
    throw new ApiError("network", MESSAGES.network);
  }
  if (!res.ok) throw await errorFromResponse(res);
  return (await res.json()) as ModelInfo[];
}

export interface StreamOptions {
  model: string;
  prompt: string;
  onToken: (text: string) => void;
  signal?: AbortSignal;
}

/** POST /chat/stream and read the SSE body. Resolves with the final `done` payload. */
export async function streamChat({
  model,
  prompt,
  onToken,
  signal,
}: StreamOptions): Promise<ChatResult> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/chat/stream`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ model, prompt }),
      signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("network", MESSAGES.network);
  }
  if (!res.ok) throw await errorFromResponse(res);
  if (!res.body) throw new ApiError("unknown", MESSAGES.unknown);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: ChatResult | null = null;

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parsed = parseSse(buffer);
      buffer = parsed.rest;
      for (const ev of parsed.events) {
        const payload = JSON.parse(ev.data) as Record<string, unknown>;
        if (ev.event === "token") onToken(String(payload.text ?? ""));
        else if (ev.event === "done") result = payload as unknown as ChatResult;
        else if (ev.event === "error") throw new ApiError("unavailable", MESSAGES.unavailable);
      }
    }
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("network", MESSAGES.network);
  }
  if (!result) throw new ApiError("unavailable", MESSAGES.unavailable);
  return result;
}
