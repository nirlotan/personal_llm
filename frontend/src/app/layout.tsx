// Root layout – fonts, Tailwind, glassmorphism background.
import "@/styles/globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Personal Chat Experiment",
  description: "The Impact of Personalization on Large Language Models (LLMs)",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
        <body className="site-bg flex items-center justify-center p-4 font-sans text-slate-800 antialiased selection:bg-blue-200 min-h-screen">
        <main className="w-full max-w-5xl mx-auto flex flex-col items-center justify-center py-10">
          {children}
        </main>
      </body>
    </html>
  );
}
