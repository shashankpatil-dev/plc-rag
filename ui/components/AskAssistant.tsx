'use client'

import { useState } from 'react'

interface CodeExample {
  machine_name: string
  similarity_score: number
  state_count: number
  interlock_count: number
  source_csv: string
  l5x_preview?: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  code_examples?: CodeExample[]
  timestamp: Date
}

export default function AskAssistant() {
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isAsking, setIsAsking] = useState(false)
  const [suggestions, setSuggestions] = useState<Record<string, string[]>>({})
  const [showSuggestions, setShowSuggestions] = useState(true)

  // Load suggestions on mount
  const loadSuggestions = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/ask/suggestions')
      const data = await response.json()
      setSuggestions(data)
    } catch (err) {
      console.error('Failed to load suggestions:', err)
    }
  }

  // Ask assistant
  const handleAsk = async () => {
    if (!query.trim()) return

    setIsAsking(true)
    setShowSuggestions(false)

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content: query,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])

    try {
      const response = await fetch('http://localhost:8000/api/v1/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          n_examples: 3,
          include_code: true
        })
      })

      if (!response.ok) {
        throw new Error('Failed to get answer')
      }

      const data = await response.json()

      // Add assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer,
        code_examples: data.code_examples,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])

      setQuery('')
    } catch (err: any) {
      // Add error message
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${err.message}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsAsking(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAsk()
    }
  }

  const useSuggestion = (suggestion: string) => {
    setQuery(suggestion)
    setShowSuggestions(false)
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="text-3xl">🤖</div>
        <div>
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
            Your Personalized Coding Assistant
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Ask questions about YOUR code - trained only on your PLC projects
          </p>
        </div>
      </div>

      {/* Info Banner */}
      <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-2">
          <span className="text-blue-600 dark:text-blue-400 text-lg">💡</span>
          <div className="text-sm text-blue-800 dark:text-blue-200">
            <strong>Better than Copilot!</strong> This assistant ONLY knows YOUR code style.
            No generic PLC suggestions - just YOUR patterns, YOUR structures, YOUR way of coding.
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      {messages.length > 0 && (
        <div className="mb-6 space-y-4 max-h-96 overflow-y-auto">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl rounded-lg p-4 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Code Examples */}
                {msg.code_examples && msg.code_examples.length > 0 && (
                  <div className="mt-4 space-y-3">
                    <div className="text-sm font-semibold">
                      📚 Code Examples from Your Codebase:
                    </div>
                    {msg.code_examples.map((example, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-600"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-sm">{example.machine_name}</span>
                          <span className="text-xs text-gray-500">
                            {(example.similarity_score * 100).toFixed(0)}% match
                          </span>
                        </div>
                        <div className="flex gap-4 text-xs text-gray-600 dark:text-gray-400 mb-2">
                          <span>{example.state_count} states</span>
                          <span>{example.interlock_count} interlocks</span>
                          <span>{example.source_csv}</span>
                        </div>
                        {example.l5x_preview && (
                          <pre className="text-xs bg-gray-50 dark:bg-gray-900 p-2 rounded overflow-x-auto">
                            {example.l5x_preview.substring(0, 300)}...
                          </pre>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Query Suggestions */}
      {showSuggestions && Object.keys(suggestions).length > 0 && (
        <div className="mb-6">
          <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            💬 Try asking:
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(suggestions).slice(0, 2).map(([category, items]) => (
              <div key={category}>
                <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2 uppercase">
                  {category}
                </div>
                <div className="space-y-2">
                  {items.slice(0, 2).map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => useSuggestion(suggestion)}
                      className="w-full text-left text-sm px-3 py-2 bg-gray-50 dark:bg-gray-700
                                 hover:bg-gray-100 dark:hover:bg-gray-600 rounded
                                 text-gray-700 dark:text-gray-300 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={loadSuggestions}
            className="mt-3 text-xs text-blue-600 dark:text-blue-400 hover:underline"
          >
            Show all suggestions
          </button>
        </div>
      )}

      {/* Input Box */}
      <div className="flex gap-2">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about your code: 'How do I structure UDT_Sequencer?' or 'Show me timer examples'..."
          disabled={isAsking}
          rows={3}
          className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                     bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                     focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     resize-none"
        />
        <button
          onClick={handleAsk}
          disabled={isAsking || !query.trim()}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400
                     text-white font-semibold rounded-lg transition-colors
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          {isAsking ? (
            <div className="flex items-center gap-2">
              <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Asking...
            </div>
          ) : (
            'Ask'
          )}
        </button>
      </div>

      {/* Tips */}
      <div className="mt-4 text-xs text-gray-500 dark:text-gray-400">
        <strong>Tips:</strong> Press Enter to send • Ask specific questions about YOUR code structures •
        Examples: "How many timers in UDT_Sequencer?" or "Show me your interlock pattern"
      </div>
    </div>
  )
}
