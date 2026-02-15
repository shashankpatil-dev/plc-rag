"use client"

import { useState, useEffect, useRef } from "react"
import { DashboardLayout } from "@/components/dashboard/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import { MessageSquare, Send, Lightbulb, Code2, Copy, Check, Loader2 } from "lucide-react"
import { MarkdownRenderer } from "@/components/markdown-renderer"

interface CodeExample {
  routine_name: string
  similarity_score: number
  rung_count: number
  source_file: string
  code_preview?: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  code_examples?: CodeExample[]
  timestamp: Date
  isStreaming?: boolean
}

export default function AssistantPage() {
  const { toast } = useToast()
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isAsking, setIsAsking] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [streamingExamples, setStreamingExamples] = useState<CodeExample[]>([])
  const [statusMessage, setStatusMessage] = useState('')
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatBoxRef = useRef<HTMLDivElement>(null)

  const suggestions = [
    "Show me conveyor logic examples",
    "How do timers work?",
    "What instructions are used?",
    "Show safety interlock patterns",
    "Explain auto mode routines",
  ]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent])

  const handleAsk = async () => {
    if (!query.trim() || isAsking) return

    const userQuery = query
    setQuery('')
    setIsAsking(true)
    setStreamingContent('')
    setStreamingExamples([])
    setStatusMessage('')

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content: userQuery,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])

    // Add placeholder for assistant message
    const assistantMessage: Message = {
      role: 'assistant',
      content: '',
      code_examples: [],
      timestamp: new Date(),
      isStreaming: true
    }
    setMessages(prev => [...prev, assistantMessage])

    try {
      // Use EventSource for SSE
      const eventSource = new EventSource(
        `http://localhost:8000/api/v1/ask-stream?` + new URLSearchParams({
          query: userQuery,
          n_examples: '3'
        })
      )

      let fullContent = ''
      let examples: CodeExample[] = []

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'status':
            setStatusMessage(data.message)
            break

          case 'example':
            examples.push(data.data)
            setStreamingExamples([...examples])
            break

          case 'content':
            fullContent += data.text
            setStreamingContent(fullContent)
            break

          case 'done':
            // Finalize message
            setMessages(prev => {
              const newMessages = [...prev]
              const lastMessage = newMessages[newMessages.length - 1]
              if (lastMessage.role === 'assistant') {
                lastMessage.content = fullContent
                lastMessage.code_examples = examples
                lastMessage.isStreaming = false
              }
              return newMessages
            })
            setStreamingContent('')
            setStreamingExamples([])
            setStatusMessage('')
            setIsAsking(false)
            eventSource.close()
            break

          case 'error':
            toast({
              title: "Error",
              description: data.message,
              variant: "destructive",
            })
            setMessages(prev => prev.slice(0, -1))
            setIsAsking(false)
            eventSource.close()
            break
        }
      }

      eventSource.onerror = () => {
        toast({
          title: "Connection Error",
          description: "Failed to connect to assistant",
          variant: "destructive",
        })
        setMessages(prev => prev.slice(0, -1))
        setIsAsking(false)
        eventSource.close()
      }

    } catch (err: any) {
      toast({
        title: "Error",
        description: err.message || 'Failed to get answer',
        variant: "destructive",
      })
      setMessages(prev => prev.slice(0, -1))
      setIsAsking(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAsk()
    }
  }

  const handleCopyCode = (code: string, index: number) => {
    navigator.clipboard.writeText(code)
    setCopiedIndex(index)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  return (
    <DashboardLayout
      title="AI Assistant"
      breadcrumbs={[{ name: "Dashboard", href: "/dashboard" }, { name: "Assistant" }]}
    >
      <div className="h-[calc(100vh-7rem)]">
        {/* Full-width Chat Area */}
        <div className="h-full max-w-6xl mx-auto">
          <Card className="h-full flex flex-col border-0 shadow-none">
            {/* Minimal Header */}
            <CardHeader className="border-b pb-3 px-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600">
                    <MessageSquare className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">PLC Assistant</CardTitle>
                    <CardDescription className="text-xs">
                      9 L5X files • 78 rungs
                    </CardDescription>
                  </div>
                </div>
                {isAsking && (
                  <Badge variant="outline" className="text-xs animate-pulse">
                    <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                    Working...
                  </Badge>
                )}
              </div>
            </CardHeader>

            {/* Chat Messages - Scrollable */}
            <CardContent className="flex-1 overflow-hidden p-0">
              <div
                ref={chatBoxRef}
                className="h-full overflow-y-auto px-6 py-8 scroll-smooth"
                style={{ scrollBehavior: 'smooth' }}
              >
                {messages.length === 0 ? (
                  // Empty State with Suggestions
                  <div className="flex h-full flex-col items-center justify-center">
                    <div className="max-w-5xl w-full text-center">
                      <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg">
                        <MessageSquare className="h-10 w-10 text-white" />
                      </div>
                      <h2 className="text-3xl font-bold mb-3">Hi! I'm your PLC Assistant</h2>
                      <p className="text-base text-muted-foreground mb-8">
                        Ask me anything about your PLC code patterns, ladder logic, or best practices.
                      </p>

                      {/* Suggestion Cards - ChatGPT Style */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto mb-8">
                        {suggestions.slice(0, 4).map((suggestion, index) => (
                          <button
                            key={index}
                            onClick={() => setQuery(suggestion)}
                            disabled={isAsking}
                            className="group relative p-4 text-left rounded-xl border-2 border-gray-200 hover:border-blue-400 hover:bg-blue-50/50 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <div className="flex items-start gap-3">
                              <Lightbulb className="h-5 w-5 text-amber-500 mt-0.5 flex-shrink-0" />
                              <p className="text-sm font-medium text-gray-700 group-hover:text-blue-700">
                                {suggestion}
                              </p>
                            </div>
                          </button>
                        ))}
                      </div>

                      {/* Status Indicator */}
                      <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                        <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
                        <span>RAG Enabled • Knowledge base active</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  // Messages - ChatGPT Style
                  <div className="space-y-6 max-w-5xl mx-auto">
                    {messages.map((message, index) => (
                      <div key={index} className="space-y-3">
                        {/* Message */}
                        <div className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                          {/* Avatar */}
                          <div className={`flex-shrink-0 h-8 w-8 rounded-lg flex items-center justify-center ${
                            message.role === 'user'
                              ? 'bg-blue-600'
                              : 'bg-gradient-to-br from-blue-500 to-indigo-600'
                          }`}>
                            <span className="text-white text-sm font-semibold">
                              {message.role === 'user' ? 'You' : 'AI'}
                            </span>
                          </div>

                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <div className={`${message.role === 'user' ? 'text-right' : ''}`}>
                              <span className="text-sm font-semibold text-gray-900">
                                {message.role === 'user' ? 'You' : 'PLC Assistant'}
                              </span>
                              <span className="ml-2 text-xs text-gray-400">
                                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            </div>

                            <div className="mt-2">
                              {message.role === 'user' ? (
                                <p className="text-sm text-gray-700 whitespace-pre-wrap">{message.content}</p>
                              ) : (
                                <>
                                  {message.isStreaming && (
                                    <>
                                      {statusMessage && (
                                        <div className="mb-3 flex items-center gap-2 text-sm text-gray-500">
                                          <Loader2 className="h-4 w-4 animate-spin" />
                                          {statusMessage}
                                        </div>
                                      )}
                                      {streamingContent && (
                                        <div className="text-gray-700">
                                          <MarkdownRenderer content={streamingContent} />
                                        </div>
                                      )}
                                      {!streamingContent && !statusMessage && (
                                        <div className="flex items-center gap-2 text-sm text-gray-500">
                                          <div className="flex gap-1">
                                            <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: '0ms' }}></div>
                                            <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: '150ms' }}></div>
                                            <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: '300ms' }}></div>
                                          </div>
                                          Thinking...
                                        </div>
                                      )}
                                    </>
                                  )}
                                  {!message.isStreaming && message.content && (
                                    <div className="text-gray-700">
                                      <MarkdownRenderer content={message.content} />
                                    </div>
                                  )}
                                </>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Code Examples - Cleaner Design */}
                        {(message.isStreaming ? streamingExamples : message.code_examples)?.length ? (
                          <div className="mt-4 space-y-3">
                            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                              Related Examples ({(message.isStreaming ? streamingExamples : message.code_examples)?.length ?? 0})
                            </div>
                            {(message.isStreaming ? streamingExamples : message.code_examples)?.map((example, i) => (
                              <div key={i} className="group">
                                <Card className="border border-gray-200 hover:border-blue-300 transition-colors">
                                  <CardHeader className="pb-3">
                                    <div className="flex items-start justify-between gap-3">
                                      <div className="flex items-start gap-2 flex-1 min-w-0">
                                        <Code2 className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                                        <div className="min-w-0 flex-1">
                                          <div className="font-mono text-sm font-semibold text-gray-900 truncate">
                                            {example.routine_name}
                                          </div>
                                          <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                                            <span>{example.rung_count} rungs</span>
                                            <span>•</span>
                                            <span className="truncate">{example.source_file}</span>
                                          </div>
                                        </div>
                                      </div>
                                      <Badge variant="secondary" className="text-xs flex-shrink-0">
                                        {(example.similarity_score * 100).toFixed(0)}% match
                                      </Badge>
                                    </div>
                                  </CardHeader>
                                  {example.code_preview && (
                                    <CardContent className="pt-0">
                                      <div className="relative">
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          className="absolute right-2 top-2 h-7 w-7 p-0 bg-gray-800/80 hover:bg-gray-700 z-10"
                                          onClick={() => handleCopyCode(example.code_preview!, i)}
                                        >
                                          {copiedIndex === i ? (
                                            <Check className="h-3.5 w-3.5 text-green-400" />
                                          ) : (
                                            <Copy className="h-3.5 w-3.5 text-gray-300" />
                                          )}
                                        </Button>
                                        <pre className="max-h-40 overflow-auto rounded-lg bg-gray-900 p-4 text-xs text-gray-100 font-mono">
                                          <code>{example.code_preview}</code>
                                        </pre>
                                      </div>
                                    </CardContent>
                                  )}
                                </Card>
                              </div>
                            ))}
                          </div>
                        ) : null}
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>
            </CardContent>

            {/* Input Area - ChatGPT Style */}
            <div className="border-t p-4 bg-white">
              <div className="max-w-5xl mx-auto">
                <div className="flex gap-3 items-end">
                  <Textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder="Ask about PLC patterns, ladder logic, timers, or any code question..."
                    className="min-h-[56px] resize-none border-gray-300 focus:border-blue-500 focus:ring-blue-500 rounded-xl shadow-sm"
                    disabled={isAsking}
                  />
                  <Button
                    onClick={handleAsk}
                    disabled={isAsking || !query.trim()}
                    className="h-[56px] px-5 bg-blue-600 hover:bg-blue-700 rounded-xl shadow-sm"
                    size="lg"
                  >
                    {isAsking ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                      <Send className="h-5 w-5" />
                    )}
                  </Button>
                </div>
                <p className="mt-2 text-xs text-center text-gray-400">
                  Press <kbd className="px-1.5 py-0.5 rounded bg-gray-100 border border-gray-300 text-gray-600">Enter</kbd> to send • <kbd className="px-1.5 py-0.5 rounded bg-gray-100 border border-gray-300 text-gray-600">Shift+Enter</kbd> for new line
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
