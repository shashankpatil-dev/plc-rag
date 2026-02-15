"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Zap, MessageSquare, Database, FileText, CheckCircle2, AlertCircle } from "lucide-react"
import axios from "axios"

export default function DashboardPage() {
  const router = useRouter()
  const [stats, setStats] = useState({
    apiStatus: "checking" as "online" | "offline" | "checking",
    knowledgeBaseCount: 0,
    generatedToday: 0,
  })

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Check API status
        await axios.get("http://localhost:8000/hello", { timeout: 3000 })
        setStats(prev => ({ ...prev, apiStatus: "online" }))
      } catch {
        setStats(prev => ({ ...prev, apiStatus: "offline" }))
      }

      // TODO: Fetch real stats from backend
      // For now, using placeholder values
      setStats(prev => ({
        ...prev,
        knowledgeBaseCount: 42,
        generatedToday: 5,
      }))
    }

    fetchStats()
  }, [])

  return (
    <DashboardLayout title="Dashboard" breadcrumbs={[{ name: "Home" }]}>
      <div className="space-y-6">
        {/* Welcome Section */}
        <div>
          <h2 className="text-2xl font-bold text-foreground">Welcome to PLC-RAG</h2>
          <p className="mt-1 text-muted-foreground">
            AI-powered ladder logic generation for industrial automation
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">API Status</CardTitle>
              {stats.apiStatus === "online" ? (
                <CheckCircle2 className="h-4 w-4 text-success" />
              ) : (
                <AlertCircle className="h-4 w-4 text-error" />
              )}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.apiStatus === "online" ? "Online" : "Offline"}
              </div>
              <p className="text-xs text-muted-foreground">
                Backend connection status
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Knowledge Base</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.knowledgeBaseCount}</div>
              <p className="text-xs text-muted-foreground">
                Stored machine examples
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Generated Today</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.generatedToday}</div>
              <p className="text-xs text-muted-foreground">
                L5X files created
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div>
          <h3 className="mb-4 text-lg font-semibold text-foreground">Quick Actions</h3>
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="cursor-pointer transition-all hover:shadow-md" onClick={() => router.push("/generate")}>
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-md bg-black text-white">
                    <Zap className="h-5 w-5" />
                  </div>
                  <div>
                    <CardTitle>Generate New L5X</CardTitle>
                    <CardDescription>
                      Upload CSV and generate ladder logic
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Button className="w-full bg-black text-white hover:bg-black/90">
                  Start Generation
                </Button>
              </CardContent>
            </Card>

            <Card className="cursor-pointer transition-all hover:shadow-md" onClick={() => router.push("/assistant")}>
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-md bg-black text-white">
                    <MessageSquare className="h-5 w-5" />
                  </div>
                  <div>
                    <CardTitle>Ask Assistant</CardTitle>
                    <CardDescription>
                      Query your codebase knowledge
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Button className="w-full bg-black text-white hover:bg-black/90">
                  Open Assistant
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* How It Works */}
        <Card>
          <CardHeader>
            <CardTitle>How PLC-RAG Works</CardTitle>
            <CardDescription>
              Understanding the AI-powered generation workflow
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-black text-xs font-semibold text-white">
                  1
                </div>
                <div>
                  <p className="font-medium">Upload CSV Process Sheet</p>
                  <p className="text-sm text-muted-foreground">
                    Define your machine logic with states, interlocks, and conditions
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-black text-xs font-semibold text-white">
                  2
                </div>
                <div>
                  <p className="font-medium">AI Retrieves Similar Examples</p>
                  <p className="text-sm text-muted-foreground">
                    RAG system finds matching patterns from your knowledge base
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-black text-xs font-semibold text-white">
                  3
                </div>
                <div>
                  <p className="font-medium">Generate L5X Ladder Logic</p>
                  <p className="text-sm text-muted-foreground">
                    AI creates complete PLC code with validation and refinement
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-black text-xs font-semibold text-white">
                  4
                </div>
                <div>
                  <p className="font-medium">Import to Studio 5000</p>
                  <p className="text-sm text-muted-foreground">
                    Download and import the generated L5X file into your PLC project
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Getting Started */}
        <Card>
          <CardHeader>
            <CardTitle>Getting Started</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between rounded-md border border-border p-3">
              <span className="text-sm">1. Ensure API backend is running</span>
              <Badge
                variant="outline"
                className={
                  stats.apiStatus === "online"
                    ? "border-success/20 bg-success/10 text-success-foreground"
                    : "border-error/20 bg-error/10 text-error-foreground"
                }
              >
                {stats.apiStatus === "online" ? "Ready" : "Not Ready"}
              </Badge>
            </div>
            <div className="flex items-center justify-between rounded-md border border-border p-3">
              <span className="text-sm">2. Upload your first CSV file</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push("/generate")}
              >
                Go to Generate
              </Button>
            </div>
            <div className="flex items-center justify-between rounded-md border border-border p-3">
              <span className="text-sm">3. Explore the knowledge base</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push("/knowledge")}
              >
                Browse Knowledge
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
