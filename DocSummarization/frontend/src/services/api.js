const BACKEND_ENDPOINT = import.meta.env.VITE_BACKEND_ENDPOINT || '';

// Helper function to decode Python string escape sequences
const decodePythonString = (str) => {
  // Unescape Python string literal - handle all Python escape sequences
  return str
    // First handle hex escapes (\xHH)
    .replace(/\\x([0-9a-fA-F]{2})/g, (match, hex) => {
      return String.fromCharCode(parseInt(hex, 16));
    })
    // Handle common escape sequences
    .replace(/\\n/g, '\n')
    .replace(/\\r/g, '\r')
    .replace(/\\t/g, '\t')
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'")
    // Handle escaped backslash - MUST BE LAST
    .replace(/\\\\/g, '\\');
};

export const generateSummary = async (formData) => {
  try {
    const response = await fetch(`${BACKEND_ENDPOINT}/v1/docsum`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }

    const responseText = await response.text();
    console.log('Raw response received:', responseText.substring(0, 200) + '...');

    // Handle streaming format: data: b'{"id":"...","text":"..."}'
    if (responseText.includes('data:')) {
      const lines = responseText.split('\n');
      let extractedText = '';

      for (const line of lines) {
        const trimmed = line.trim();

        // Skip [DONE] markers and empty lines
        if (trimmed.includes('[DONE]') || trimmed === '' || trimmed === 'data:') {
          continue;
        }

        if (trimmed.startsWith('data: ')) {
          let dataContent = trimmed.substring(6).trim();
          console.log('Processing line, data content:', dataContent.substring(0, 100));

          // Remove b' prefix and trailing ' if present (Python bytes string format)
          if (dataContent.startsWith("b'") && dataContent.endsWith("'")) {
            dataContent = dataContent.substring(2, dataContent.length - 1);
            console.log('After removing b prefix:', dataContent.substring(0, 100));
          }

          // Remove b" prefix and trailing " if present (alternative format)
          if (dataContent.startsWith('b"') && dataContent.endsWith('"')) {
            dataContent = dataContent.substring(2, dataContent.length - 1);
          }

          // Try to parse as JSON FIRST (before decoding, since JSON.parse handles escapes)
          try {
            const jsonData = JSON.parse(dataContent);
            console.log('Parsed JSON successfully, text field present:', !!jsonData.text);

            if (jsonData.text) {
              extractedText += jsonData.text;
              console.log('Extracted text:', jsonData.text.substring(0, 100));
            }
          } catch (parseError) {
            console.error('JSON parse failed, trying decode then parse');

            // If direct JSON parse fails, decode Python escapes then try again
            try {
              const decodedContent = decodePythonString(dataContent);
              const jsonData = JSON.parse(decodedContent);

              if (jsonData.text) {
                extractedText += jsonData.text;
                console.log('Extracted text after decode:', jsonData.text.substring(0, 100));
              }
            } catch (secondError) {
              console.error('Both parsing attempts failed, trying regex extraction');

              // Last resort: regex extraction
              try {
                const textMatch = dataContent.match(/"text":"([^"]*(?:\\.[^"]*)*)"/);
                if (textMatch && textMatch[1]) {
                  const unescapedText = textMatch[1]
                    .replace(/\\"/g, '"')
                    .replace(/\\\\/g, '\\')
                    .replace(/\\n/g, '\n');
                  extractedText += unescapedText;
                  console.log('Extracted via regex:', unescapedText.substring(0, 100));
                }
              } catch (regexError) {
                console.error('All parsing methods failed:', regexError);
              }
            }
          }
        }
      }

      if (extractedText) {
        console.log('Returning extracted text, length:', extractedText.length);
        return extractedText;
      } else {
        console.warn('No text extracted from data lines');
      }
    }

    // Try direct JSON parse as fallback
    try {
      const jsonData = JSON.parse(responseText);
      if (jsonData.text) {
        return jsonData.text;
      }
      if (jsonData.output_text) {
        return jsonData.output_text;
      }
    } catch (e) {
      console.error('Direct JSON parse failed:', e.message);
    }

    // Last resort - return response text but warn user
    console.error('Could not extract text field, returning raw response');
    return responseText;
  } catch (error) {
    console.error('Error generating summary:', error);
    throw error;
  }
};

export const generateSummaryStreaming = async (formData, onChunk) => {
  try {
    const response = await fetch(`${BACKEND_ENDPOINT}/v1/docsum`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete lines
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        const trimmed = line.trim();

        // Skip [DONE] markers and empty lines
        if (trimmed.includes('[DONE]') || trimmed === '' || trimmed === 'data:') {
          continue;
        }

        if (trimmed.startsWith('data: ')) {
          let dataContent = trimmed.substring(6).trim();

          // Remove b' prefix and trailing ' if present (Python bytes string format)
          if (dataContent.startsWith("b'") && dataContent.endsWith("'")) {
            dataContent = dataContent.substring(2, dataContent.length - 1);
          }

          // Remove b" prefix and trailing " if present (alternative format)
          if (dataContent.startsWith('b"') && dataContent.endsWith('"')) {
            dataContent = dataContent.substring(2, dataContent.length - 1);
          }

          // Try to parse as JSON first (JSON.parse handles escape sequences correctly)
          try {
            const data = JSON.parse(dataContent);
            if (data.text) {
              console.log('[STREAMING] JSON chunk:', data.text);
              onChunk(data.text);
            }
          } catch (parseError) {
            // Not JSON - this is a raw text token, decode then send
            if (dataContent) {
              const decodedText = decodePythonString(dataContent);
              console.log('[STREAMING] Raw token:', decodedText);
              onChunk(decodedText);
            }
          }
        }
      }
    }
  } catch (error) {
    console.error('Error generating summary:', error);
    throw error;
  }
};
