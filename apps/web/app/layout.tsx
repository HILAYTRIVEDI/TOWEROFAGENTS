import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Tower of Agents — The Governance & Execution Layer for Enterprise AI",
  description:
    "Deploy AI into mission-critical workflows with policy-aware execution, evidence-backed decisions, and human approval. From vendor onboarding to compliance reviews.",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
