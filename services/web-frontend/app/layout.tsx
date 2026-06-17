import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Providers from "@/components/Providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "IIoT Predictive Maintenance",
  description: "Real-time AI-powered industrial monitoring and anomaly detection",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
        <footer className="w-full py-8 bg-black border-t border-white/10 text-center text-zinc-500 text-sm">
          <div className="container mx-auto px-6">
            <p>&copy; {new Date().getFullYear()} Smart Energy Guardien. All rights reserved.</p>
            <p className="mt-2">Optimisation Energetique et Maintenance predicitve pour l industrie 4.0</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
