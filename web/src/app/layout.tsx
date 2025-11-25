import type { Metadata } from "next";
import { Geist_Mono } from "next/font/google";
import localFont from "next/font/local";
import "./globals.css";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";

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

const peyda = localFont({
  variable: "--font-peyda",
  src: [
    { path: "./fonts/PeydaWeb-Black.woff2", weight: "900", style: "normal" },
    { path: "./fonts/PeydaWeb-ExtraBlack.woff2", weight: "950", style: "normal" },
  ],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "https://batarikh.xyz"),
  title: { default: "با تاریخ", template: "با تاریخ / %s" },
  description: "نه بودن‌ِمان نه رفتن‌ِمان فرقی به حال دنیا نمی‌کند.",
  applicationName: "با تاریخ",
  alternates: { canonical: "/" },
  robots: { index: true, follow: true },
  openGraph: {
    title: "با تاریخ",
    description: "نه بودن‌ِمان نه رفتن‌ِمان فرقی به حال دنیا نمی‌کند.",
    siteName: "با تاریخ",
    locale: "fa_IR",
    type: "website",
    url: "/",
  },
  twitter: {
    card: "summary_large_image",
    title: "با تاریخ",
    description: "نه بودن‌ِمان نه رفتن‌ِمان فرقی به حال دنیا نمی‌کند.",
  },
};

export const viewport = {
  themeColor: "#f5f5f5",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fa" dir="rtl">
      <body
        className={`${estedad.className} ${geistMono.variable} ${peyda.variable} antialiased bg-neutral-100`}
      >
        <div className="relative">
        <div className="min-h-screen w-full bg-white fixed -z-1 top-0">
          {/* Noise Texture (Darker Dots) Background */}
          <div
            className="absolute inset-0 z-0"
            style={{
              background: "#f5f5f5",
              backgroundImage: "radial-gradient(circle at 1px 1px, rgba(0, 0, 0, 0.35) 1px, transparent 0)",
              backgroundSize: "20px 20px",
            }}
          />
            {/* Your Content/Components */}
        </div>
        <div className="w-full max-w-6xl mx-auto py-4 md:py-20 px-4 md:px-0 grid grid-col-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Header />
        {children}
        <Footer />
        </div>
        </div>
      </body>
    </html>
  );
}
