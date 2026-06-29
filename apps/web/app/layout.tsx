import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Tower of Agents — AI Control Tower for Enterprise Workflows",
  description:
    "Tower of Agents turns document-heavy internal workflows into structured, auditable decision packets using role-based AI agents and human approval.",
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
