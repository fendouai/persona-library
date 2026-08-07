import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Persona Library",
  description: "Create, manage, mix, and apply writing personas.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-zinc-950 text-zinc-100 antialiased">
        <header className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur">
          <nav className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
            <Link href="/" className="text-lg font-semibold tracking-tight">
              🎭 Persona Library
            </Link>
            <div className="ml-auto flex items-center gap-1 text-sm">
              <NavLink href="/">Browse</NavLink>
              <NavLink href="/create">Create</NavLink>
              <NavLink href="/mix">Mix</NavLink>
            </div>
          </nav>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="rounded-md px-3 py-1.5 text-zinc-400 transition-colors hover:bg-zinc-900 hover:text-zinc-100"
    >
      {children}
    </Link>
  );
}
