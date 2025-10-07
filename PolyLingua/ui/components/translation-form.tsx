"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Languages, Loader2 } from "lucide-react"

const languages = [
  { code: "en", name: "English" },
  { code: "es", name: "Spanish" },
  { code: "fr", name: "French" },
  { code: "de", name: "German" },
  { code: "it", name: "Italian" },
  { code: "pt", name: "Portuguese" },
  { code: "ru", name: "Russian" },
  { code: "ja", name: "Japanese" },
  { code: "ko", name: "Korean" },
  { code: "zh", name: "Chinese (Simplified)" },
  { code: "ar", name: "Arabic" },
  { code: "hi", name: "Hindi" },
  { code: "nl", name: "Dutch" },
  { code: "pl", name: "Polish" },
  { code: "tr", name: "Turkish" },
  { code: "sv", name: "Swedish" },
]

export function TranslationForm() {
  const [sourceText, setSourceText] = React.useState("")
  const [translatedText, setTranslatedText] = React.useState("")
  const [targetLanguage, setTargetLanguage] = React.useState("es")
  const [isLoading, setIsLoading] = React.useState(false)

  const handleTranslate = async () => {
    if (!sourceText.trim()) {
      return
    }

    setIsLoading(true)
    setTranslatedText("") // Clear previous translation

    try {
      const selectedLang = languages.find(lang => lang.code === targetLanguage)
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8888"

      const response = await fetch(`${backendUrl}/v1/translation`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          language_from: "auto",
          language_to: selectedLang?.name || "Spanish",
          source_language: sourceText,
        }),
      })

      if (!response.ok) {
        throw new Error(`Translation failed: ${response.statusText}`)
      }

      // Check if response is streaming (SSE)
      const contentType = response.headers.get("content-type")
      if (contentType?.includes("text/event-stream")) {
        // Handle Server-Sent Events streaming
        const reader = response.body?.getReader()
        const decoder = new TextDecoder()
        let accumulatedText = ""

        if (!reader) {
          throw new Error("Response body is not readable")
        }

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split("\n")

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6) // Remove "data: " prefix

              if (data === "[DONE]") {
                continue
              }

              try {
                const parsed = JSON.parse(data)
                // Extract content from chat completion streaming format
                const text = parsed.choices?.[0]?.delta?.content || ""
                if (text) {
                  accumulatedText += text
                  setTranslatedText(accumulatedText)
                }
              } catch (e) {
                // Skip malformed JSON chunks
                console.warn("Failed to parse chunk:", e)
              }
            }
          }
        }
      } else {
        // Handle regular JSON response (fallback)
        const data = await response.json()
        const translatedContent = data.choices?.[0]?.message?.content || data.text || "Translation not available"
        setTranslatedText(translatedContent)
      }
    } catch (error) {
      console.error("Translation error:", error)
      setTranslatedText(`Error: Translation failed. Please try again.\n\nDetails: ${error instanceof Error ? error.message : "Unknown error"}`)
    } finally {
      setIsLoading(false)
    }
  }

  const characterCount = sourceText.length

  return (
    <div className="w-full max-w-7xl mx-auto space-y-10">
      <div className="text-center space-y-2">
        <div className="flex items-center justify-center gap-2">
          <Languages className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold">Translation Service</h1>
        </div>
        <p className="text-muted-foreground">
          Translate your text to multiple languages
        </p>
      </div>

      <div className="flex items-center justify-center gap-12 mb-12">
        <img
          src="https://budecosystem.com/logo-black.svg"
          alt="Bud Ecosystem Logo"
          className="h-8 w-auto"
        />
        <img
          src="https://opea.dev/wp-content/uploads/sites/9/2024/04/opea-horizontal-color.svg"
          alt="OPEA Logo"
          className="h-9 w-auto"
        />
        <img
          src="https://www.netapp.com/media/na_logo_black_rgb_reg-mark_tcm19-21014.jpg"
          alt="NetApp Logo"
          className="h-14 w-auto"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Input Text</CardTitle>
                <CardDescription>
                  Enter the text to translate
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-48">
                  <Select value={targetLanguage} onValueChange={setTargetLanguage}>
                    <SelectTrigger id="target-language">
                      <SelectValue placeholder="Select target language" />
                    </SelectTrigger>
                    <SelectContent>
                      {languages.map((lang) => (
                        <SelectItem key={lang.code} value={lang.code}>
                          {lang.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  onClick={handleTranslate}
                  disabled={!sourceText.trim() || isLoading}
                  size="lg"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Translating...
                    </>
                  ) : (
                    <>
                      <Languages className="mr-2 h-4 w-4" />
                      Translate
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Textarea
                id="source-text"
                placeholder="Enter text to translate..."
                value={sourceText}
                onChange={(e) => setSourceText(e.target.value)}
                className="min-h-[400px] resize-none"
              />
              <p className="text-sm text-muted-foreground text-right">
                {characterCount} characters
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Translation</CardTitle>
            <CardDescription>
              {translatedText
                ? `Translated to ${languages.find(lang => lang.code === targetLanguage)?.name}`
                : "Translation will appear here"
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Textarea
                value={translatedText}
                readOnly
                placeholder="Translation will appear here..."
                className="min-h-[400px] resize-none bg-muted"
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
