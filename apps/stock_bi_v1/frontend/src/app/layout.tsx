import type { Metadata } from "next";
import { Cormorant_Garamond, IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

const terminalBody = IBM_Plex_Sans({
  variable: "--font-terminal-body",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const terminalMono = IBM_Plex_Mono({
  variable: "--font-terminal-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const terminalDisplay = Cormorant_Garamond({
  variable: "--font-terminal-display",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Stock BI V1",
  description: "Bloomberg terminal style stock analytics platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body
        className={`${terminalBody.variable} ${terminalMono.variable} ${terminalDisplay.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
