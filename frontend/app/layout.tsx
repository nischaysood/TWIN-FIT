import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TwinFit — AI Virtual Try-On",
  description:
    "AI-powered virtual try-on and size recommendation for Indian fashion. Built for AMD Developer Hackathon ACT II.",
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
