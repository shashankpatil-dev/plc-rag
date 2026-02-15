"use client"

import { DashboardLayout } from "@/components/dashboard/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Search, Database, FileText, Eye } from "lucide-react"

// Mock data - replace with real API call
const mockKnowledgeBase = [
  {
    id: "1",
    machine_name: "Mat_Roll_Transfer_Conveyor1",
    state_count: 12,
    interlock_count: 8,
    source_csv: "conveyor_logic.csv",
    created_at: "2024-01-15",
  },
  {
    id: "2",
    machine_name: "Assembly_Station_Main",
    state_count: 15,
    interlock_count: 12,
    source_csv: "assembly.csv",
    created_at: "2024-01-14",
  },
  {
    id: "3",
    machine_name: "Quality_Check_Unit",
    state_count: 8,
    interlock_count: 6,
    source_csv: "quality_control.csv",
    created_at: "2024-01-13",
  },
  {
    id: "4",
    machine_name: "Packaging_Line_A",
    state_count: 10,
    interlock_count: 7,
    source_csv: "packaging.csv",
    created_at: "2024-01-12",
  },
]

export default function KnowledgePage() {
  return (
    <DashboardLayout
      title="Knowledge Base"
      breadcrumbs={[{ name: "Dashboard", href: "/dashboard" }, { name: "Knowledge" }]}
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-foreground">Knowledge Base</h2>
            <p className="mt-1 text-muted-foreground">
              Browse stored machine logic patterns and examples
            </p>
          </div>
          <Badge variant="outline" className="text-sm">
            <Database className="mr-1 h-4 w-4" />
            {mockKnowledgeBase.length} Examples
          </Badge>
        </div>

        {/* Search */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex space-x-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search by machine name, source file, or logic pattern..."
                  className="pl-10"
                />
              </div>
              <Button className="bg-black hover:bg-black/90">Search</Button>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        <div className="grid gap-4 md:grid-cols-2">
          {mockKnowledgeBase.map((item) => (
            <Card key={item.id} className="transition-all hover:shadow-md">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{item.machine_name}</CardTitle>
                    <CardDescription className="mt-1">
                      Source: {item.source_csv}
                    </CardDescription>
                  </div>
                  <FileText className="h-5 w-5 text-muted-foreground" />
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">States</p>
                    <p className="font-medium">{item.state_count}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Interlocks</p>
                    <p className="font-medium">{item.interlock_count}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between border-t border-border pt-4">
                  <span className="text-xs text-muted-foreground">
                    Added {new Date(item.created_at).toLocaleDateString()}
                  </span>
                  <Button variant="outline" size="sm">
                    <Eye className="mr-2 h-3 w-3" />
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Empty State (if no results) */}
        {mockKnowledgeBase.length === 0 && (
          <Card>
            <CardContent className="flex h-64 items-center justify-center">
              <div className="text-center">
                <Database className="mx-auto h-12 w-12 text-muted-foreground" />
                <p className="mt-4 text-sm text-muted-foreground">
                  No examples found in knowledge base
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Upload and generate L5X files to build your knowledge base
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}
