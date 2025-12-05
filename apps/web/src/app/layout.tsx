import "./globals.css";
import Header from "@/components/header";
import Footer from "@/components/footer";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v15-appRouter";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Cyberattack Simulation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AppRouterCacheProvider>
          <div className="flex min-h-screen flex-col bg-slate-950 text-white">
            <Header />
            <main className="flex-1 pb-12">{children}</main>
            <Footer />
          </div>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
