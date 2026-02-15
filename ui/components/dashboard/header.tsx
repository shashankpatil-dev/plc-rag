"use client"

import { useEffect, useState } from "react"
import { Badge } from "@/components/ui/badge"
import axios from "axios"

interface HeaderProps {
  title: string
  breadcrumbs?: { name: string; href?: string }[]
}

export function Header({ title, breadcrumbs }: HeaderProps) {
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
    const interval = setInterval(checkAPI, 30000) // Check every 30 seconds

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex h-16 items-center justify-between border-b border-border bg-background px-6">
      <div className="flex items-center space-x-4">
        <div>
          <h1 className="text-lg font-semibold text-foreground">{title}</h1>
          {breadcrumbs && breadcrumbs.length > 0 && (
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              {breadcrumbs.map((item, index) => (
                <div key={item.name} className="flex items-center space-x-2">
                  {index > 0 && <span>/</span>}
                  <span>{item.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-muted-foreground">API Status:</span>
          <Badge
            variant="outline"
            className={
              apiStatus === "online"
                ? "border-success/20 bg-success/10 text-success-foreground"
                : apiStatus === "offline"
                ? "border-error/20 bg-error/10 text-error-foreground"
                : "border-muted bg-muted text-muted-foreground"
            }
          >
            {apiStatus === "online" && "● Online"}
            {apiStatus === "offline" && "● Offline"}
            {apiStatus === "checking" && "● Checking..."}
          </Badge>
        </div>
      </div>
    </div>
  )
}
