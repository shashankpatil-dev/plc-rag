"use client"

import { useState } from "react"
import { DashboardLayout } from "@/components/dashboard/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Progress } from "@/components/ui/progress"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { useToast } from "@/hooks/use-toast"
import { FileUp, Upload, CheckCircle2, Download, Copy, Loader2, ArrowRight } from "lucide-react"
import axios from "axios"
import { ParsedCSV, MachineLogic } from "@/types/api"

export default function GeneratePage() {
  const { toast } = useToast()
  const [currentStep, setCurrentStep] = useState(1)
  const [dragActive, setDragActive] = useState(false)
  const [fileName, setFileName] = useState<string | null>(null)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [parsedData, setParsedData] = useState<ParsedCSV | null>(null)
  const [selectedMachineIndex, setSelectedMachineIndex] = useState(0)
  const [useRefinement, setUseRefinement] = useState(true)
  const [maxIterations, setMaxIterations] = useState(3)
  const [generating, setGenerating] = useState(false)
  const [generationResult, setGenerationResult] = useState<any>(null)

  // Upload handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = async (file: File) => {
    if (!file.name.endsWith('.csv')) {
      toast({
        title: "Invalid file type",
        description: "Please upload a CSV file",
        variant: "destructive",
      })
      return
    }

    setFileName(file.name)
    setUploadedFile(file)  // Store the original file
    setUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(
        'http://localhost:8000/api/v1/parse-csv',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      )

      setParsedData(response.data)
      setCurrentStep(2)
      toast({
        title: "CSV parsed successfully",
        description: `Found ${response.data.total_machines} machine(s)`,
      })
    } catch (err: any) {
      toast({
        title: "Upload failed",
        description: err.response?.data?.detail || 'Failed to parse CSV',
        variant: "destructive",
      })
    } finally {
      setUploading(false)
    }
  }

  // Generate L5X
  const handleGenerate = async () => {
    if (!parsedData || !uploadedFile) return

    setGenerating(true)
    setCurrentStep(3)

    try {
      const endpoint = useRefinement
        ? `http://localhost:8000/api/v1/generate-refined?machine_index=${selectedMachineIndex}&max_iterations=${maxIterations}`
        : `http://localhost:8000/api/v1/generate?machine_index=${selectedMachineIndex}`

      const formData = new FormData()
      formData.append('file', uploadedFile)  // Use the original CSV file

      const response = await axios.post(endpoint, formData)
      setGenerationResult(response.data)
      setCurrentStep(4)
      toast({
        title: "Generation complete",
        description: "L5X code generated successfully",
      })
    } catch (err: any) {
      toast({
        title: "Generation failed",
        description: err.response?.data?.detail || 'Failed to generate L5X',
        variant: "destructive",
      })
      setCurrentStep(2)
    } finally {
      setGenerating(false)
    }
  }

  // Download L5X
  const handleDownload = () => {
    if (!generationResult) return

    const blob = new Blob([generationResult.l5x_code], { type: 'application/xml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${generationResult.machine_name}.L5X`
    a.click()
    URL.revokeObjectURL(url)

    toast({
      title: "Download started",
      description: `${generationResult.machine_name}.L5X`,
    })
  }

  // Copy to clipboard
  const handleCopy = () => {
    if (!generationResult) return
    navigator.clipboard.writeText(generationResult.l5x_code)
    toast({
      title: "Copied to clipboard",
      description: "L5X code copied successfully",
    })
  }

  const selectedMachine = parsedData?.machines[selectedMachineIndex]

  return (
    <DashboardLayout
      title="Generate L5X"
      breadcrumbs={[{ name: "Dashboard", href: "/dashboard" }, { name: "Generate" }]}
    >
      <div className="space-y-6">
        {/* Progress Steps */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              {[1, 2, 3, 4].map((step) => (
                <div key={step} className="flex items-center">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-full border-2 ${
                    currentStep >= step
                      ? 'border-black bg-black text-white'
                      : 'border-border bg-background text-muted-foreground'
                  }`}>
                    {currentStep > step ? <CheckCircle2 className="h-5 w-5" /> : step}
                  </div>
                  {step < 4 && (
                    <div className={`mx-2 h-0.5 w-16 ${
                      currentStep > step ? 'bg-black' : 'bg-border'
                    }`} />
                  )}
                </div>
              ))}
            </div>
            <div className="mt-3 flex justify-between text-sm">
              <span className={currentStep >= 1 ? 'font-medium' : 'text-muted-foreground'}>Upload CSV</span>
              <span className={currentStep >= 2 ? 'font-medium' : 'text-muted-foreground'}>Review Logic</span>
              <span className={currentStep >= 3 ? 'font-medium' : 'text-muted-foreground'}>Generate</span>
              <span className={currentStep >= 4 ? 'font-medium' : 'text-muted-foreground'}>Download</span>
            </div>
          </CardContent>
        </Card>

        {/* Step 1: Upload */}
        {currentStep === 1 && (
          <Card>
            <CardHeader>
              <CardTitle>Step 1: Upload CSV</CardTitle>
              <CardDescription>
                Upload your process sheet with machine logic definitions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  id="file-upload"
                  accept=".csv"
                  onChange={handleChange}
                  className="hidden"
                  disabled={uploading}
                />
                <label
                  htmlFor="file-upload"
                  className={`flex h-64 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors ${
                    uploading
                      ? 'cursor-wait border-border bg-muted'
                      : dragActive
                      ? 'border-black bg-muted'
                      : 'border-border hover:border-black hover:bg-muted'
                  }`}
                >
                  {uploading ? (
                    <div className="text-center">
                      <Loader2 className="mx-auto h-12 w-12 animate-spin text-muted-foreground" />
                      <p className="mt-4 text-sm text-muted-foreground">Parsing {fileName}...</p>
                    </div>
                  ) : (
                    <div className="text-center">
                      <FileUp className="mx-auto h-12 w-12 text-muted-foreground" />
                      <p className="mt-4 text-sm font-medium">
                        Click to upload or drag and drop
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        CSV files only (LogicSheet format)
                      </p>
                    </div>
                  )}
                </label>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Review Logic */}
        {currentStep >= 2 && parsedData && (
          <Card>
            <CardHeader>
              <CardTitle>Step 2: Review Parsed Logic</CardTitle>
              <CardDescription>
                Verify the machine logic before generation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Summary */}
                <div className="flex items-center justify-between rounded-md border border-border p-4">
                  <div className="flex items-center space-x-4">
                    <Upload className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{fileName}</p>
                      <p className="text-sm text-muted-foreground">
                        {parsedData.total_machines} machine(s) • {parsedData.total_states} total states
                      </p>
                    </div>
                  </div>
                  <Badge variant="outline" className="border-success/20 bg-success/10 text-success-foreground">
                    Parsed
                  </Badge>
                </div>

                {/* Machine Details */}
                {selectedMachine && (
                  <div className="space-y-4">
                    <div>
                      <h4 className="mb-2 font-medium">{selectedMachine.name}</h4>
                      <div className="grid gap-2 text-sm">
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">States:</span>
                          <span className="font-medium">{selectedMachine.state_count}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Interlocks:</span>
                          <span className="font-medium">{selectedMachine.total_interlock_count}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Cycle Path:</span>
                          <div className="flex items-center space-x-1 font-mono text-xs">
                            {selectedMachine.cycle_path?.slice(0, 5).map((step, i) => (
                              <div key={i} className="flex items-center">
                                <span>{step}</span>
                                {i < 4 && selectedMachine.cycle_path && i < selectedMachine.cycle_path.length - 1 && (
                                  <ArrowRight className="mx-1 h-3 w-3" />
                                )}
                              </div>
                            ))}
                            {selectedMachine.cycle_path && selectedMachine.cycle_path.length > 5 && <span>...</span>}
                          </div>
                        </div>
                      </div>
                    </div>

                    <Separator />

                    {/* State Table */}
                    <div className="rounded-md border border-border">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Step</TableHead>
                            <TableHead>Description</TableHead>
                            <TableHead>Interlocks</TableHead>
                            <TableHead>Condition</TableHead>
                            <TableHead>Next</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {selectedMachine.states.slice(0, 5).map((state) => (
                            <TableRow key={state.step}>
                              <TableCell className="font-mono">{state.step}</TableCell>
                              <TableCell>{state.description}</TableCell>
                              <TableCell>
                                <div className="flex flex-wrap gap-1">
                                  {state.interlocks.slice(0, 3).map((interlock, i) => (
                                    <Badge key={i} variant="outline" className="text-xs">
                                      {interlock}
                                    </Badge>
                                  ))}
                                  {state.interlocks.length > 3 && (
                                    <Badge variant="outline" className="text-xs">
                                      +{state.interlocks.length - 3}
                                    </Badge>
                                  )}
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline">{state.condition}</Badge>
                              </TableCell>
                              <TableCell className="font-mono">{state.next_step}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                      {selectedMachine.states.length > 5 && (
                        <div className="border-t border-border p-2 text-center text-xs text-muted-foreground">
                          Showing 5 of {selectedMachine.states.length} states
                        </div>
                      )}
                    </div>

                    {currentStep === 2 && (
                      <div className="flex justify-end space-x-3">
                        <Button variant="outline" onClick={() => { setParsedData(null); setCurrentStep(1); }}>
                          Upload Different File
                        </Button>
                        <Button className="bg-black hover:bg-black/90" onClick={() => setCurrentStep(3)}>
                          Continue to Generate
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 3: Configure & Generate */}
        {currentStep >= 3 && parsedData && (
          <Card>
            <CardHeader>
              <CardTitle>Step 3: Configure & Generate</CardTitle>
              <CardDescription>
                Select machine and generation options
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Select Machine</label>
                <Select
                  value={selectedMachineIndex.toString()}
                  onValueChange={(v) => setSelectedMachineIndex(parseInt(v))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {parsedData.machines.map((machine, index) => (
                      <SelectItem key={index} value={index.toString()}>
                        {machine.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="refinement"
                  checked={useRefinement}
                  onCheckedChange={(checked) => setUseRefinement(checked as boolean)}
                />
                <label htmlFor="refinement" className="text-sm font-medium">
                  Use refinement loop (auto-fix validation errors)
                </label>
              </div>

              {useRefinement && (
                <div className="ml-6 space-y-2">
                  <label className="text-sm font-medium">Max Iterations</label>
                  <Select
                    value={maxIterations.toString()}
                    onValueChange={(v) => setMaxIterations(parseInt(v))}
                  >
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1</SelectItem>
                      <SelectItem value="2">2</SelectItem>
                      <SelectItem value="3">3</SelectItem>
                      <SelectItem value="5">5</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}

              {currentStep === 3 && !generating && (
                <div className="flex justify-end space-x-3">
                  <Button variant="outline" onClick={() => setCurrentStep(2)}>
                    Back to Review
                  </Button>
                  <Button className="bg-black hover:bg-black/90" onClick={handleGenerate}>
                    Generate L5X
                  </Button>
                </div>
              )}

              {generating && (
                <div className="flex items-center justify-center space-x-3 rounded-md border border-border p-6">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span className="text-sm text-muted-foreground">Generating L5X code...</span>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Step 4: Download */}
        {currentStep === 4 && generationResult && (
          <Card>
            <CardHeader>
              <CardTitle>Step 4: Download L5X</CardTitle>
              <CardDescription>
                Generation complete! Download your L5X file
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-md border border-success/20 bg-success/10 p-4">
                <div className="flex items-center space-x-3">
                  <CheckCircle2 className="h-5 w-5 text-success" />
                  <div>
                    <p className="font-medium">Generation Successful</p>
                    <p className="text-sm text-muted-foreground">
                      {generationResult.machine_name} • {(generationResult.code_length / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex space-x-3">
                <Button className="flex-1 bg-black hover:bg-black/90" onClick={handleDownload}>
                  <Download className="mr-2 h-4 w-4" />
                  Download L5X File
                </Button>
                <Button variant="outline" onClick={handleCopy}>
                  <Copy className="mr-2 h-4 w-4" />
                  Copy Code
                </Button>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Code Preview</label>
                <div className="rounded-md border border-border bg-muted p-4">
                  <pre className="max-h-64 overflow-auto text-xs">
                    {generationResult.l5x_code.substring(0, 2000)}
                    {generationResult.l5x_code.length > 2000 && '\n...'}
                  </pre>
                </div>
              </div>

              <Button variant="outline" onClick={() => { setCurrentStep(1); setParsedData(null); setGenerationResult(null); }}>
                Generate Another
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}
