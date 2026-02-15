import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from '@/components/ui/toaster'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'PLC-RAG - AI-Powered PLC Logic Generator',
  description: 'Generate PLC ladder logic from CSV process definitions using AI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="light">
      <body className={inter.className}>
        {children}
        <Toaster />
      </body>
    </html>
  )
}
