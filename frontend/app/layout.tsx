import "./global.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ArjunaAI",
  description: "Bhagavad Gita grounded search with citations",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
