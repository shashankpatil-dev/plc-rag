'use client'

import { useState } from 'react'
import { ParsedCSV } from '@/types/api'

interface GenerationResult {
  status: string
  machine_name: string
  l5x_code: string
  code_length: number
  similar_count: number
  validation: {
    is_valid: boolean
    issues: Array<{
      severity: string
      message: string
      location: string
    }>
  }
  refinement?: {
    iterations: Array<{
      iteration: number
      is_valid: boolean
      error_count: number
      warning_count: number
      info_count: number
      issues: Array<{
        severity: string
        message: string
        location: string
      }>
    }>
    total_iterations: number
    final_valid: boolean
  }
}

interface GeneratePanelProps {
  parsedData: ParsedCSV
  uploadedFile: File | null
}

export default function GeneratePanel({ parsedData, uploadedFile }: GeneratePanelProps) {
  const [selectedMachine, setSelectedMachine] = useState<number>(0)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationResult, setGenerationResult] = useState<GenerationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [useRefinement, setUseRefinement] = useState(true)
  const [maxIterations, setMaxIterations] = useState(3)

  const handleGenerate = async () => {
    if (!uploadedFile) {
      setError('No file uploaded')
      return
    }

    setIsGenerating(true)
    setError(null)
    setGenerationResult(null)

    try {
      const formData = new FormData()
      formData.append('file', uploadedFile)
      formData.append('machine_index', selectedMachine.toString())

      // Choose endpoint based on refinement option
      const endpoint = useRefinement
        ? `http://localhost:8000/api/v1/generate-refined?max_iterations=${maxIterations}`
        : 'http://localhost:8000/api/v1/generate'

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Generation failed')
      }

      const result: GenerationResult = await response.json()
      setGenerationResult(result)
    } catch (err: any) {
      setError(err.message || 'Failed to generate L5X')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDownload = async () => {
    if (!uploadedFile) return

    try {
      const formData = new FormData()
      formData.append('file', uploadedFile)
      formData.append('machine_index', selectedMachine.toString())

      const response = await fetch('http://localhost:8000/api/v1/generate-download', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Download failed')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${parsedData.machines[selectedMachine].name.replace(/\s+/g, '_')}.L5X`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err: any) {
      setError(err.message || 'Failed to download L5X')
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-8 mb-8">
      <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
        Generate L5X Code
      </h2>

      {/* Machine Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Select Machine
        </label>
        <select
          value={selectedMachine}
          onChange={(e) => setSelectedMachine(Number(e.target.value))}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                     bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                     focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={isGenerating}
        >
          {parsedData.machines.map((machine, index) => (
            <option key={index} value={index}>
              {machine.name} ({machine.state_count} states, {machine.all_interlocks?.length || 0} interlocks)
            </option>
          ))}
        </select>
      </div>

      {/* Refinement Options */}
      <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="useRefinement"
              checked={useRefinement}
              onChange={(e) => setUseRefinement(e.target.checked)}
              disabled={isGenerating}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="useRefinement" className="text-sm font-medium text-blue-900 dark:text-blue-100">
              Use Refinement Loop (Recommended)
            </label>
          </div>
          {useRefinement && (
            <select
              value={maxIterations}
              onChange={(e) => setMaxIterations(Number(e.target.value))}
              disabled={isGenerating}
              className="px-3 py-1 text-sm border border-blue-300 dark:border-blue-700 rounded
                         bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            >
              <option value={1}>1 iteration</option>
              <option value={2}>2 iterations</option>
              <option value={3}>3 iterations</option>
              <option value={5}>5 iterations</option>
            </select>
          )}
        </div>
        <p className="text-xs text-blue-700 dark:text-blue-300">
          {useRefinement
            ? `Automatically fixes validation errors by refining L5X up to ${maxIterations} time(s)`
            : 'Generate once without refinement (may have validation issues)'}
        </p>
      </div>

      {/* Generate Button */}
      <div className="flex gap-4">
        <button
          onClick={handleGenerate}
          disabled={isGenerating || !uploadedFile}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400
                     text-white font-semibold rounded-lg transition-colors
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          {isGenerating ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Generating L5X...
            </span>
          ) : (
            'Generate L5X'
          )}
        </button>

        {generationResult && (
          <button
            onClick={handleDownload}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white
                       font-semibold rounded-lg transition-colors
                       focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
          >
            Download L5X File
          </button>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-red-800 dark:text-red-200 text-sm">
            <strong>Error:</strong> {error}
          </p>
        </div>
      )}

      {/* Generation Result */}
      {generationResult && (
        <div className="mt-6 space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="text-sm text-blue-600 dark:text-blue-400 font-medium">Machine</div>
              <div className="text-lg font-semibold text-blue-900 dark:text-blue-100 mt-1">
                {generationResult.machine_name}
              </div>
            </div>
            <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg border border-purple-200 dark:border-purple-800">
              <div className="text-sm text-purple-600 dark:text-purple-400 font-medium">Code Size</div>
              <div className="text-lg font-semibold text-purple-900 dark:text-purple-100 mt-1">
                {(generationResult.code_length / 1024).toFixed(1)} KB
              </div>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg border border-green-200 dark:border-green-800">
              <div className="text-sm text-green-600 dark:text-green-400 font-medium">Similar Examples</div>
              <div className="text-lg font-semibold text-green-900 dark:text-green-100 mt-1">
                {generationResult.similar_count} found
              </div>
            </div>
          </div>

          {/* Refinement History */}
          {generationResult.refinement && generationResult.refinement.iterations.length > 0 && (
            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
              <h3 className="text-lg font-semibold text-purple-900 dark:text-purple-100 mb-3">
                🔄 Refinement History ({generationResult.refinement.total_iterations} iteration{generationResult.refinement.total_iterations !== 1 ? 's' : ''})
              </h3>
              <div className="space-y-3">
                {generationResult.refinement.iterations.map((iter, index) => (
                  <div
                    key={index}
                    className="p-3 bg-white dark:bg-gray-800 rounded border border-purple-200 dark:border-purple-700"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-purple-900 dark:text-purple-100">
                        Iteration {iter.iteration}
                      </span>
                      <span className={`text-sm font-semibold ${
                        iter.is_valid
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-yellow-600 dark:text-yellow-400'
                      }`}>
                        {iter.is_valid ? '✓ Valid' : `${iter.error_count} error(s)`}
                      </span>
                    </div>
                    <div className="flex gap-4 text-xs text-gray-600 dark:text-gray-400">
                      <span className="text-red-600 dark:text-red-400">Errors: {iter.error_count}</span>
                      <span className="text-yellow-600 dark:text-yellow-400">Warnings: {iter.warning_count}</span>
                      <span className="text-blue-600 dark:text-blue-400">Info: {iter.info_count}</span>
                    </div>
                  </div>
                ))}
              </div>
              {generationResult.refinement.final_valid && (
                <div className="mt-3 p-2 bg-green-100 dark:bg-green-900/30 rounded text-sm text-green-800 dark:text-green-200 text-center font-medium">
                  ✓ Successfully refined to valid L5X!
                </div>
              )}
            </div>
          )}

          {/* Validation Results */}
          <div className={`p-4 rounded-lg border ${
            generationResult.validation.is_valid
              ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
              : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
          }`}>
            <div className="flex items-center gap-2 mb-2">
              <span className={`text-lg font-semibold ${
                generationResult.validation.is_valid
                  ? 'text-green-900 dark:text-green-100'
                  : 'text-yellow-900 dark:text-yellow-100'
              }`}>
                {generationResult.validation.is_valid ? '✓ Valid L5X' : '⚠ Validation Issues'}
              </span>
            </div>

            {generationResult.validation.issues.length > 0 && (
              <div className="mt-3 space-y-2">
                <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Final Issues ({generationResult.validation.issues.length}):
                </div>
                {generationResult.validation.issues.map((issue, index) => (
                  <div
                    key={index}
                    className={`text-sm p-2 rounded ${
                      issue.severity === 'error'
                        ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
                        : issue.severity === 'warning'
                        ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200'
                        : 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200'
                    }`}
                  >
                    <strong className="uppercase">{issue.severity}:</strong> {issue.message}
                    {issue.location && <span className="ml-2 opacity-75">({issue.location})</span>}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* L5X Preview */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Generated L5X Code Preview
              </h3>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(generationResult.l5x_code)
                }}
                className="text-sm px-3 py-1 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300
                           dark:hover:bg-gray-600 rounded text-gray-700 dark:text-gray-300"
              >
                Copy to Clipboard
              </button>
            </div>
            <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg border border-gray-200 dark:border-gray-700 max-h-96 overflow-y-auto">
              <pre className="text-xs text-gray-800 dark:text-gray-200 whitespace-pre-wrap break-words font-mono">
                {generationResult.l5x_code.substring(0, 2000)}
                {generationResult.l5x_code.length > 2000 && '\n\n... (truncated, download for full code)'}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
