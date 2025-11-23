import type { Metadata } from "next";
import { Geist_Mono } from "next/font/google";
import localFont from "next/font/local";
import "./globals.css";

const estedad = localFont({
  variable: "--font-estedad",
  src: [
    { path: "./fonts/Estedad-Thin.woff2", weight: "100", style: "normal" },
    { path: "./fonts/Estedad-ExtraLight.woff2", weight: "200", style: "normal" },
    { path: "./fonts/Estedad-Light.woff2", weight: "300", style: "normal" },
    { path: "./fonts/Estedad-Regular.woff2", weight: "400", style: "normal" },
    { path: "./fonts/Estedad-Medium.woff2", weight: "500", style: "normal" },
    { path: "./fonts/Estedad-SemiBold.woff2", weight: "600", style: "normal" },
    { path: "./fonts/Estedad-Bold.woff2", weight: "700", style: "normal" },
    { path: "./fonts/Estedad-ExtraBold.woff2", weight: "800", style: "normal" },
    { path: "./fonts/Estedad-Black.woff2", weight: "900", style: "normal" },
  ],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "BaTarikh – Telegram Archive",
  description: "Mirror of the batarikh Telegram channel",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fa" dir="rtl">
      <body
        className={`${estedad.className} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
