import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Methodology · Thirsty Tokens" };

export default function Methodology() {
  return (
    <main className="mx-auto w-full max-w-2xl px-4 py-10 sm:px-8 sm:py-16">
      <Link href="/" className="text-sm text-tide underline underline-offset-4">
        Back to the app
      </Link>
      <h1 className="font-display mt-6 text-4xl font-bold sm:text-5xl">How these are estimated</h1>
      <p className="mt-4 text-lg text-muted-foreground">
        A full methodology write-up is coming. This is the short version.
      </p>

      <div className="mt-8 space-y-6 text-lg leading-relaxed">
        <p>
          <strong>Cost and speed are measured.</strong> Token counts come from the model provider.
          Cost is those tokens times the published price per token. Times are measured on the
          server.
        </p>
        <p>
          <strong>Energy, carbon and water are estimates.</strong> Model makers do not publish how
          much power one answer takes, so each model is placed in a small, medium or large tier with
          an assumed energy per output token. Carbon uses the EU-27 average grid intensity. Water
          uses a factor for cooling on site plus power generation.
        </p>
        <p>
          <strong>Sources disagree by up to 5 times.</strong> Treat the numbers as the right order
          of magnitude, good for comparing models with each other, not as audited figures.
        </p>
        <p>
          <strong>Quality is not compared.</strong> This app compares cost, speed and footprint. It
          does not judge which answer is better.
        </p>
      </div>
    </main>
  );
}
