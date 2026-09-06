import "./globals.css";
import type { Metadata } from "next";
import { Plus_Jakarta_Sans, JetBrains_Mono } from "next/font/google";
import { ToastProvider } from "@/components/ui/Toast";
import { SidebarProvider } from "@/components/SidebarContext";
import { ThemeProvider } from "@/components/ThemeContext";
import AppShell from "@/components/AppShell";
import CommandPalette from "@/components/ui/CommandPalette";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
  display: "swap",
  weight: ["300", "400", "500", "600", "700", "800"],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "JobAgent — Autonomous AI Career Copilot",
  description: "Desktop-first AI command center for job discovery, evaluation, and application automation",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-theme="dark" className={`${jakarta.variable} ${jetbrainsMono.variable}`}>
      <body className={jakarta.className}>
        <ThemeProvider>
          <ToastProvider>
            <SidebarProvider>
              <AppShell>{children}</AppShell>
              <CommandPalette />
            </SidebarProvider>
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
