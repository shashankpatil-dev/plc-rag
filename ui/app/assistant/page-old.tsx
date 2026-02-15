"use client"

import { useState, useEffect, useRef } from "react"
import { DashboardLayout } from "@/components/dashboard/dashboard-layout"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { useToast } from "@/hooks/use-toast"
import { MessageSquare, Send, Loader2, Lightbulb, Code2 } from "lucide-react"

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

export default function AssistantPage() {
  const { toast } = useToast()
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isAsking, setIsAsking] = useState(false)
  const [suggestions] = useState([
    "Show me timer logic examples",
    "How are interlocks typically used?",
    "Examples of sequence control patterns",
    "What's the pattern for emergency stop logic?",
  ])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleAsk = async () => {
    if (!query.trim()) return

    setIsAsking(true)

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
      toast({
        title: "Error",
        description: err.message || 'Failed to get answer',
        variant: "destructive",
      })
      // Remove the user message if failed
      setMessages(prev => prev.slice(0, -1))
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

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion)
  }

  return (
    <DashboardLayout
      title="AI Assistant"
      breadcrumbs={[{ name: "Dashboard", href: "/dashboard" }, { name: "Assistant" }]}
    >
      <div className="grid h-[calc(100vh-7rem)] gap-6 lg:grid-cols-3">
        {/* Chat Area */}
        <div className="lg:col-span-2">
          <Card className="flex h-full flex-col">
            <CardHeader>
              <CardTitle>Ask PLC Assistant</CardTitle>
              <CardDescription>
                Query your codebase knowledge base for patterns and examples
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col space-y-4">
              {/* Messages */}
              <ScrollArea className="flex-1 pr-4">
                {messages.length === 0 ? (
                  <div className="flex h-full items-center justify-center text-center">
                    <div>
                      <MessageSquare className="mx-auto h-12 w-12 text-muted-foreground" />
                      <p className="mt-4 text-sm text-muted-foreground">
                        No messages yet. Ask a question to get started.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {messages.map((message, index) => (
                      <div key={index} className="space-y-2">
                        <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div
                            className={`max-w-[80%] rounded-lg p-3 ${
                              message.role === 'user'
                                ? 'bg-black text-white'
                                : 'border border-border bg-muted'
                            }`}
                          >
                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                            <p className={`mt-1 text-xs ${
                              message.role === 'user' ? 'text-gray-300' : 'text-muted-foreground'
                            }`}>
                              {message.timestamp.toLocaleTimeString()}
                            </p>
                          </div>
                        </div>

                        {/* Code Examples */}
                        {message.code_examples && message.code_examples.length > 0 && (
                          <div className="space-y-2 pl-4">
                            {message.code_examples.map((example, i) => (
                              <Card key={i} className="border-l-4 border-l-black">
                                <CardHeader className="pb-3">
                                  <div className="flex items-center justify-between">
                                    <CardTitle className="text-sm">{example.machine_name}</CardTitle>
                                    <Badge variant="outline">
                                      {(example.similarity_score * 100).toFixed(0)}% match
                                    </Badge>
                                  </div>
                                </CardHeader>
                                <CardContent className="space-y-2 text-xs">
                                  <div className="flex items-center justify-between">
                                    <span className="text-muted-foreground">States:</span>
                                    <span className="font-medium">{example.state_count}</span>
                                  </div>
                                  <div className="flex items-center justify-between">
                                    <span className="text-muted-foreground">Interlocks:</span>
                                    <span className="font-medium">{example.interlock_count}</span>
                                  </div>
                                  <div className="flex items-center justify-between">
                                    <span className="text-muted-foreground">Source:</span>
                                    <span className="font-mono">{example.source_csv}</span>
                                  </div>
                                  {example.l5x_preview && (
                                    <div className="mt-2">
                                      <div className="flex items-center space-x-2 text-muted-foreground">
                                        <Code2 className="h-3 w-3" />
                                        <span>L5X Preview:</span>
                                      </div>
                                      <div className="mt-1 rounded-md bg-muted p-2">
                                        <pre className="text-xs">
                                          {example.l5x_preview.substring(0, 200)}...
                                        </pre>
                                      </div>
                                    </div>
                                  )}
                                </CardContent>
                              </Card>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </ScrollArea>

              <Separator />

              {/* Input */}
              <div className="flex space-x-2">
                <Textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="Ask about PLC patterns, logic examples, or best practices..."
                  className="resize-none"
                  disabled={isAsking}
                />
                <Button
                  onClick={handleAsk}
                  disabled={isAsking || !query.trim()}
                  className="bg-black hover:bg-black/90"
                >
                  {isAsking ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Suggestions Sidebar */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Lightbulb className="h-5 w-5" />
                <CardTitle className="text-base">Suggestions</CardTitle>
              </div>
              <CardDescription>
                Click to ask common questions
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {suggestions.map((suggestion, index) => (
                <Button
                  key={index}
                  variant="outline"
                  className="w-full justify-start text-left text-sm"
                  onClick={() => handleSuggestionClick(suggestion)}
                >
                  {suggestion}
                </Button>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">How to Use</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p>Ask questions about:</p>
              <ul className="list-disc space-y-1 pl-4">
                <li>Logic patterns in your codebase</li>
                <li>Timer and counter usage</li>
                <li>Interlock configurations</li>
                <li>Safety logic examples</li>
                <li>Sequence control patterns</li>
              </ul>
              <Separator />
              <p className="text-xs">
                The assistant searches your knowledge base and provides relevant examples with code snippets.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
