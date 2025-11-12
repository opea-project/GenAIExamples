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
import { Languages, Loader2, Upload, X, FileText } from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

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

// Supported file types
const SUPPORTED_FILE_TYPES = [
  ".docx",
  ".txt",
  ".md",
  ".markdown",
  ".rst",
  ".log",
  ".csv",
]

const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB

export function PolyLinguaForm() {
  const [sourceText, setSourceText] = React.useState("")
  const [translatedText, setTranslatedText] = React.useState("")
  const [targetLanguage, setTargetLanguage] = React.useState("es")
  const [isLoading, setIsLoading] = React.useState(false)
  const [inputMode, setInputMode] = React.useState<"text" | "file">("text")
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null)
  const [fileError, setFileError] = React.useState<string>("")
  const [dragActive, setDragActive] = React.useState(false)
  const [extractedText, setExtractedText] = React.useState("")
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  // Validate file
  const validateFile = (file: File): string | null => {
    const fileExt = `.${file.name.split(".").pop()?.toLowerCase()}`
    if (!SUPPORTED_FILE_TYPES.includes(fileExt)) {
      return `Unsupported file type. Supported: ${SUPPORTED_FILE_TYPES.join(", ")}`
    }
    if (file.size > MAX_FILE_SIZE) {
      return `File size exceeds 20MB limit`
    }
    return null
  }

  // Handle file selection
  const handleFileSelect = (file: File) => {
    const error = validateFile(file)
    if (error) {
      setFileError(error)
      setSelectedFile(null)
    } else {
      setFileError("")
      setSelectedFile(file)
      setTranslatedText("")
      setExtractedText("")
    }
  }

  // Handle drag events
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  // Handle drop
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  // Handle file input change
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0])
    }
  }

  // Clear file selection
  const clearFile = () => {
    setSelectedFile(null)
    setFileError("")
    setExtractedText("")
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const handleTranslate = async () => {
    // Validate input based on mode
    if (inputMode === "text" && !sourceText.trim()) {
      return
    }
    if (inputMode === "file" && !selectedFile) {
      return
    }

    setIsLoading(true)
    setTranslatedText("") // Clear previous translation

    try {
      const selectedLang = languages.find(lang => lang.code === targetLanguage)
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8888"

      let response: Response

      if (inputMode === "file" && selectedFile) {
        // Handle file upload
        const formData = new FormData()
        formData.append("file", selectedFile)
        formData.append("language_from", "auto")
        formData.append("language_to", selectedLang?.name || "Spanish")

        response = await fetch(`${backendUrl}/v1/translation`, {
          method: "POST",
          body: formData,
        })
      } else {
        // Handle text input
        response = await fetch(`${backendUrl}/v1/translation`, {
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
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Translation failed: ${response.statusText}`)
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
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Languages className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold">PolyLingua</h1>
          </div>
          <p className="text-muted-foreground">
            Translate your text to multiple languages
          </p>
        </div>

        <img
          src="https://www.netapp.com/media/na_logo_black_rgb_reg-mark_tcm19-21014.jpg"
          alt="NetApp"
          className="h-14 w-auto"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Input</CardTitle>
                <CardDescription>
                  Enter text or upload a document
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
                  disabled={
                    (inputMode === "text" && !sourceText.trim()) ||
                    (inputMode === "file" && !selectedFile) ||
                    isLoading
                  }
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
            <Tabs value={inputMode} onValueChange={(value) => setInputMode(value as "text" | "file")}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="text">Text Input</TabsTrigger>
                <TabsTrigger value="file">File Upload</TabsTrigger>
              </TabsList>

              <TabsContent value="text" className="space-y-2 mt-4">
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
              </TabsContent>

              <TabsContent value="file" className="mt-4">
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    dragActive
                      ? "border-primary bg-primary/5"
                      : "border-muted-foreground/25 hover:border-primary/50"
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    accept={SUPPORTED_FILE_TYPES.join(",")}
                    onChange={handleFileInputChange}
                  />

                  {selectedFile ? (
                    <div className="space-y-4">
                      <div className="flex items-center justify-center gap-3 p-4 bg-muted rounded-lg">
                        <FileText className="h-8 w-8 text-primary" />
                        <div className="flex-1 text-left">
                          <p className="font-medium">{selectedFile.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={clearFile}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
                      <div>
                        <p className="text-lg font-medium">
                          Drop your file here, or{" "}
                          <button
                            type="button"
                            onClick={() => fileInputRef.current?.click()}
                            className="text-primary hover:underline"
                          >
                            browse
                          </button>
                        </p>
                        <p className="text-sm text-muted-foreground mt-2">
                          Supported: DOCX, TXT, MD, CSV, LOG, RST
                        </p>
                        <p className="text-sm text-muted-foreground">
                          Max file size: 20MB
                        </p>
                      </div>
                    </div>
                  )}

                  {fileError && (
                    <p className="text-sm text-destructive mt-4">{fileError}</p>
                  )}
                </div>
              </TabsContent>
            </Tabs>
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

      {/* Powered by footer */}
      <div className="mt-16 pt-8 border-t border-border">
        <div className="text-center space-y-4">
          <p className="text-sm text-muted-foreground">Powered by</p>
          <div className="flex items-center justify-center gap-8 flex-wrap">
            <img
              src="https://budecosystem.com/logo-black.svg"
              alt="Bud Ecosystem"
              className="h-6 w-auto opacity-70 hover:opacity-100 transition-opacity"
            />
            <img
              src="https://opea.dev/wp-content/uploads/sites/9/2024/04/opea-horizontal-color.svg"
              alt="OPEA"
              className="h-7 w-auto opacity-70 hover:opacity-100 transition-opacity"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
