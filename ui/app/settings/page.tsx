"use client"

import { useState, useEffect } from "react"
import { DashboardLayout } from "@/components/dashboard/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { CheckCircle2, AlertCircle, Database, Cpu, Settings as SettingsIcon } from "lucide-react"
import axios from "axios"

export default function SettingsPage() {
  const [apiStatus, setApiStatus] = useState<"online" | "offline" | "checking">("checking")

  useEffect(() => {
    const checkAPI = async () => {
      try {
        await axios.get("http://localhost:8000/hello", { timeout: 3000 })
        setApiStatus("online")
      } catch {
        setApiStatus("offline")
      }
    }
    checkAPI()
  }, [])

  return (
    <DashboardLayout
      title="Settings"
      breadcrumbs={[{ name: "Dashboard", href: "/dashboard" }, { name: "Settings" }]}
    >
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Settings</h2>
          <p className="mt-1 text-muted-foreground">
            Configure your PLC-RAG system
          </p>
        </div>

        {/* API Configuration */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <SettingsIcon className="h-5 w-5" />
              <CardTitle>API Configuration</CardTitle>
            </div>
            <CardDescription>
              Backend connection settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Backend URL</label>
              <div className="flex items-center space-x-2">
                <code className="flex-1 rounded-md border border-border bg-muted px-3 py-2 text-sm">
                  http://localhost:8000
                </code>
                <Badge
                  variant="outline"
                  className={
                    apiStatus === "online"
                      ? "border-success/20 bg-success/10 text-success-foreground"
                      : "border-error/20 bg-error/10 text-error-foreground"
                  }
                >
                  {apiStatus === "online" && <CheckCircle2 className="mr-1 h-3 w-3" />}
                  {apiStatus === "offline" && <AlertCircle className="mr-1 h-3 w-3" />}
                  {apiStatus === "online" ? "Connected" : "Disconnected"}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                The FastAPI backend must be running for the application to work
              </p>
            </div>

            <Separator />

            <div className="grid gap-4 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Health Check Endpoint</span>
                <code className="rounded bg-muted px-2 py-1 text-xs">/hello</code>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Parse CSV Endpoint</span>
                <code className="rounded bg-muted px-2 py-1 text-xs">/api/v1/parse-csv</code>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Generate Endpoint</span>
                <code className="rounded bg-muted px-2 py-1 text-xs">/api/v1/generate</code>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* LLM Provider */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Cpu className="h-5 w-5" />
              <CardTitle>LLM Provider</CardTitle>
            </div>
            <CardDescription>
              Language model configuration
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-md border border-border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Current Provider</p>
                  <p className="text-sm text-muted-foreground">
                    Configured in backend .env file
                  </p>
                </div>
                <Badge variant="outline">Gemini 1.5 Flash</Badge>
              </div>
            </div>

            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Max Tokens</span>
                <span className="font-medium">8,192</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Temperature</span>
                <span className="font-medium">0.1</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Max Retries</span>
                <span className="font-medium">2</span>
              </div>
            </div>

            <Separator />

            <p className="text-xs text-muted-foreground">
              To change LLM settings, update the <code className="rounded bg-muted px-1 py-0.5">plc-rag/.env</code> file
              and restart the backend server.
            </p>
          </CardContent>
        </Card>

        {/* Vector Database */}
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Database className="h-5 w-5" />
              <CardTitle>Vector Database</CardTitle>
            </div>
            <CardDescription>
              Knowledge base storage configuration
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-md border border-border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Provider</p>
                  <p className="text-sm text-muted-foreground">
                    Local vector database
                  </p>
                </div>
                <Badge variant="outline">ChromaDB</Badge>
              </div>
            </div>

            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Host</span>
                <span className="font-mono">localhost:8001</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Collection</span>
                <span className="font-mono">plc_embeddings</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Stored Examples</span>
                <span className="font-medium">42 machines</span>
              </div>
            </div>

            <Separator />

            <div className="flex space-x-2">
              <Button variant="outline" size="sm">
                View Collections
              </Button>
              <Button variant="outline" size="sm">
                Clear Cache
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* System Info */}
        <Card>
          <CardHeader>
            <CardTitle>System Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Frontend Version</span>
              <span className="font-mono">1.0.0</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Framework</span>
              <span>Next.js 14.1.0</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">UI Library</span>
              <span>shadcn/ui</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
