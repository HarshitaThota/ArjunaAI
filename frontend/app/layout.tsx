import * as React from "react";

export const metadata = { title: "ArjunaAI", description: "Bhagavad Gita Q&A" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      {/* If you add Tailwind later, ensure globals.css is imported here */}
      <body>{children}</body>
    </html>
  );
}
