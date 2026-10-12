"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { Results } from "@/components/results";
import { WaterGlass } from "@/components/water-glass";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, MAX_PROMPT_CHARS, fetchModels, messageFor, streamChat } from "@/lib/api";
import type { ChatResult, ModelInfo } from "@/lib/types";

type Status = "idle" | "loading" | "streaming" | "done" | "error";

const EXAMPLES = [
  "Explain how a rainbow forms in two sentences.",
  "Write a haiku about a data center.",
  "Why is the sky blue? Keep it short.",
];

export function Chat() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [model, setModel] = useState("");
  const [prompt, setPrompt] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<ChatResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchModels(controller.signal)
      .then((list) => {
        setModels(list);
        setModel((current) => current || list[0]?.id || "");
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setModelsError(err instanceof ApiError ? err.message : messageFor("unknown"));
      });
    return () => {
      controller.abort();
      abortRef.current?.abort();
    };
  }, []);

  const busy = status === "loading" || status === "streaming";
  const canSubmit = !busy && model !== "" && prompt.trim().length > 0;

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!canSubmit) return;
    const controller = new AbortController();
    abortRef.current = controller;
    setStatus("loading");
    setAnswer("");
    setResult(null);
    setError(null);
    try {
      const done = await streamChat({
        model,
        prompt,
        signal: controller.signal,
        onToken: (text) => {
          setStatus("streaming");
          setAnswer((prev) => prev + text);
        },
      });
      setResult(done);
      setStatus("done");
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setStatus("idle");
        return;
      }
      setError(err instanceof ApiError ? err.message : messageFor("unknown"));
      setStatus("error");
    }
  }

  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,26rem)_minmax(0,1fr)] lg:gap-14">
      <form onSubmit={submit} className="space-y-5 lg:sticky lg:top-8 lg:self-start">
        <div className="space-y-2">
          <label htmlFor="model" className="text-sm font-medium">
            Model
          </label>
          <select
            id="model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            disabled={busy || models.length === 0}
            className="h-11 w-full rounded-lg border bg-card px-3 text-base disabled:opacity-60"
          >
            {models.length === 0 && (
              <option value="">{modelsError ? "Models unavailable" : "Loading models"}</option>
            )}
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.display_name}
              </option>
            ))}
          </select>
          {modelsError && (
            <p role="alert" className="text-sm text-destructive">
              {modelsError}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <label htmlFor="prompt" className="text-sm font-medium">
            Prompt
          </label>
          <Textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value.slice(0, MAX_PROMPT_CHARS))}
            maxLength={MAX_PROMPT_CHARS}
            rows={6}
            placeholder="Ask anything. Short questions keep the footprint small."
            className="min-h-36 bg-card text-base"
            aria-describedby="prompt-count"
          />
          <p id="prompt-count" className="tabular text-right text-xs text-muted-foreground">
            {prompt.length.toLocaleString()} / {MAX_PROMPT_CHARS.toLocaleString()}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button type="submit" size="lg" disabled={!canSubmit} className="h-11 px-5 text-base">
            {busy ? "Asking" : "Ask the model"}
          </Button>
          {busy && (
            <Button
              type="button"
              variant="ghost"
              className="h-11 px-4"
              onClick={() => abortRef.current?.abort()}
            >
              Stop
            </Button>
          )}
        </div>

        <p className="text-sm text-muted-foreground">
          Energy, carbon and water are estimates.{" "}
          <Link href="/methodology" className="text-tide underline underline-offset-4">
            How are these estimated?
          </Link>
        </p>
      </form>

      <div aria-live="polite" className="min-w-0 space-y-8">
        {status === "idle" && (
          <div className="flex flex-col items-start gap-5 rounded-xl border border-dashed p-6 sm:flex-row sm:items-center">
            <WaterGlass className="h-32 w-24 shrink-0" />
            <div className="space-y-3">
              <p className="font-display text-xl font-semibold">Nothing has been drunk yet.</p>
              <p className="text-muted-foreground">Write a prompt, or start from one of these:</p>
              <ul className="flex flex-wrap gap-2">
                {EXAMPLES.map((text) => (
                  <li key={text}>
                    <Button
                      type="button"
                      variant="outline"
                      className="h-auto whitespace-normal px-3 py-2 text-left"
                      onClick={() => setPrompt(text)}
                    >
                      {text}
                    </Button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {status === "loading" && (
          <p className="text-muted-foreground" role="status">
            Waiting for the first token. The first request after a quiet period can take 20 seconds
            or more while the server wakes up.
          </p>
        )}

        {status === "error" && error && (
          <div role="alert" className="rounded-xl border border-destructive/50 p-5">
            <p className="font-display text-lg font-semibold text-destructive">Request failed</p>
            <p className="mt-1">{error}</p>
          </div>
        )}

        {answer && (
          <section aria-labelledby="answer-heading">
            <h2 id="answer-heading" className="font-display text-lg font-semibold">
              Answer
            </h2>
            <p className="mt-2 max-w-prose whitespace-pre-wrap text-lg leading-relaxed">
              {answer}
              {status === "streaming" && (
                <span aria-hidden className="ml-0.5 inline-block h-5 w-2 bg-tide align-middle" />
              )}
            </p>
          </section>
        )}

        {result && <Results result={result} />}
      </div>
    </div>
  );
}
