import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "sonner";
import { Providers } from "./providers";
import { AppShell } from "./app-shell";

export const metadata: Metadata = {
  title: "ReboundIQ - Layoff-to-Offer AI Copilot",
  description: "Privacy-first, local-first AI career recovery OS. From layoff to offer with structured execution.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
        <Toaster position="top-center" richColors closeButton />
      </body>
    </html>
  );
}
