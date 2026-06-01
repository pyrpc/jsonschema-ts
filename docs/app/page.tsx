import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-neutral-950 to-neutral-900 px-4">
      <div className="text-center">
        <div className="mb-6 text-5xl font-light tracking-tighter text-neutral-500">
          {'{ }'}
        </div>
        <h1 className="mb-3 text-4xl font-light text-neutral-100 sm:text-5xl">
          jsonschema-ts
        </h1>
        <p className="mb-1 text-lg text-neutral-400">
          Convert JSON Schema → TypeScript interfaces
        </p>
        <p className="mb-8 text-sm text-neutral-600">
          Python · Zero deps · Battle-tested
        </p>

        <div className="mb-10 flex items-center justify-center gap-4">
          <Link
            href="/docs"
            className="rounded-lg border border-neutral-700 px-5 py-2.5 text-sm text-neutral-300 transition-colors hover:border-neutral-500 hover:text-white"
          >
            Docs
          </Link>
          <a
            href="https://github.com/pyrpc/jsonschema-ts"
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-neutral-700 px-5 py-2.5 text-sm text-neutral-300 transition-colors hover:border-neutral-500 hover:text-white"
          >
            GitHub
          </a>
        </div>

        <pre className="mx-auto mb-8 max-w-lg overflow-x-auto rounded-lg border border-neutral-800 bg-neutral-950/60 p-4 text-left text-sm leading-relaxed text-neutral-300">
          <code>
            <span className="text-blue-400">from</span>{' '}
            <span className="text-amber-300">jsonschema_ts</span>{' '}
            <span className="text-blue-400">import</span> convert{'\n\n'}
            ts = convert(schema, <span className="text-green-300">'User'</span>)
            {'\n'}
            <span className="text-neutral-600">
              {'# '}export interface User {'{'}
            </span>
            {'\n'}
            <span className="text-neutral-600">
              {'# '}  name: string;
            </span>
            {'\n'}
            <span className="text-neutral-600">
              {'# '}
              {'}'}
            </span>
          </code>
        </pre>

        <code className="rounded-md bg-neutral-900 px-3 py-1.5 text-sm text-neutral-500">
          pip install jsonschema-ts
        </code>
      </div>
    </main>
  );
}
