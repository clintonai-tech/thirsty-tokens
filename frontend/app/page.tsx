import Link from "next/link";

import { Chat } from "@/components/chat";
import { ThemeToggle } from "@/components/theme-toggle";

export default function Home() {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-8 sm:py-10">
      <header className="flex items-center justify-between">
        <span className="font-display text-lg font-bold">Thirsty Tokens</span>
        <nav className="flex items-center gap-2 text-sm">
          <Link
            href="/methodology"
            className="rounded-md px-2 py-1 underline-offset-4 hover:underline"
          >
            Methodology
          </Link>
          <ThemeToggle />
        </nav>
      </header>

      <main className="mt-10 sm:mt-16">
        <h1 className="font-display max-w-3xl text-4xl font-bold leading-[1.05] sm:text-6xl">
          Ask a model. See what the answer drank.
        </h1>
        <p className="mt-5 max-w-xl text-lg text-muted-foreground">
          Every answer takes electricity, and cooling takes water. Pick a model, ask something, and
          read the estimate next to the bill.
        </p>
        <div className="mt-12">
          <Chat />
        </div>
      </main>
    </div>
  );
}
