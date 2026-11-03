import ReactMarkdown, { type Components } from "react-markdown";

// Model output is untrusted: react-markdown ignores raw HTML, and links open in a new tab
// without leaking the referrer. Headings start at h3 because the page owns h1 and h2.
const components: Components = {
  h1: ({ children }) => <h3 className="font-display mt-6 mb-2 text-xl font-bold">{children}</h3>,
  h2: ({ children }) => <h3 className="font-display mt-6 mb-2 text-xl font-bold">{children}</h3>,
  h3: ({ children }) => (
    <h4 className="font-display mt-5 mb-2 text-lg font-semibold">{children}</h4>
  ),
  h4: ({ children }) => <h5 className="font-display mt-4 mb-1 font-semibold">{children}</h5>,
  p: ({ children }) => <p className="my-3">{children}</p>,
  ul: ({ children }) => <ul className="my-3 list-disc space-y-1 pl-6">{children}</ul>,
  ol: ({ children }) => <ol className="my-3 list-decimal space-y-1 pl-6">{children}</ol>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  blockquote: ({ children }) => (
    <blockquote className="my-3 border-l-2 pl-4 text-muted-foreground">{children}</blockquote>
  ),
  code: ({ children }) => (
    <code className="rounded bg-muted px-1.5 py-0.5 text-[0.9em] break-words">{children}</code>
  ),
  pre: ({ children }) => (
    <pre className="my-3 overflow-x-auto rounded-lg bg-muted p-3 text-sm [&_code]:bg-transparent [&_code]:p-0">
      {children}
    </pre>
  ),
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-tide underline underline-offset-4"
    >
      {children}
    </a>
  ),
};

export function Markdown({ text }: { text: string }) {
  return (
    <div className="[&>:first-child]:mt-0 [&>:last-child]:mb-0">
      <ReactMarkdown components={components}>{text}</ReactMarkdown>
    </div>
  );
}
