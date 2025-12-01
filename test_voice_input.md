# Voice Input Testing Guide

## ⚠️ Important Note

**Python Version Issue**: If you're using Python 3.14, Whisper cannot be installed due to dependency compatibility. The system will use placeholder transcription instead. For real transcription, you'll need Python 3.10-3.13.

However, you can still test the voice input functionality - it will work but show placeholder messages instead of actual transcription.

## Quick Test Steps

1. **Open the frontend in your browser:**
   - Navigate to `http://localhost:5173`
   - You should see the Excel AI Agent interface

2. **Test Voice Input:**
   - Look for the "Voice Input" section (🎤 icon) in the main panel
   - Click the "Start Recording" button
   - **Grant microphone permission** when prompted by your browser
   - Speak your question clearly (e.g., "What are the total sales by region?")
   - You should see:
     - A recording timer counting up
     - "Listening..." with partial transcripts appearing as you speak
     - After you stop speaking (2 seconds of silence) or click "Stop Recording":
       - Final transcript appears
       - Status shows "Analyzing..."
       - Analysis results appear below

3. **What to Check:**
   - ✅ Microphone permission is granted
   - ✅ Recording button changes to "Stop Recording" when active
   - ✅ Recording timer increments
   - ✅ Partial transcripts appear while speaking (if Whisper is installed)
   - ✅ Final transcript appears after stopping
   - ✅ Analysis results are displayed

## Troubleshooting

### If microphone permission is denied:
- Check browser settings for microphone access
- Try refreshing the page and granting permission again
- On Chrome: Click the lock icon in the address bar → Site settings → Microphone → Allow

### If you see "Placeholder transcription" message:
- Whisper model may not be loaded yet (first use takes time)
- Check backend console for Whisper loading messages
- The model loads on first WebSocket connection

### If WebSocket connection fails:
- Verify backend is running: `curl http://localhost:8000/health`
- Check browser console (F12) for WebSocket errors
- Ensure no firewall is blocking port 8000

### If no transcripts appear:
- Check browser console for errors
- Check backend terminal for error messages
- Verify Whisper is installed: `pip list | grep whisper`

## Testing with Browser DevTools

1. **Open DevTools (F12 or Cmd+Option+I)**
2. **Go to Console tab** - Watch for:
   - "WebSocket connected" message
   - Any error messages
   - WebSocket message logs

3. **Go to Network tab** - Filter by "WS" (WebSocket):
   - You should see a connection to `ws://localhost:8000/ws/speech`
   - Status should be "101 Switching Protocols"

## ✅ Verification

The WebSocket endpoint has been tested and is working correctly. You can proceed with browser testing.

## Expected Behavior

1. **Click "Start Recording"**:
   - Button changes to "Stop Recording" with ⏹ icon
   - Timer starts counting
   - "Recording in progress..." indicator appears
   - WebSocket connects (check console)

2. **While Speaking**:
   - Partial transcripts may appear under "Listening..."
   - Timer continues counting

3. **After Stopping (or 2s silence)**:
   - Final transcript appears
   - Status shows "Analyzing..."
   - Analysis results populate in the results section

## Test Questions to Try

- "What are the total sales by region?"
- "Show me the average revenue per product"
- "List all columns in the student thesis file"
- "What is the maximum value in the power generation log?"

