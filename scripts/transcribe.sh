#!/bin/bash
# transcribe.sh - OpenAI audio transcription via curl
# Usage: transcribe.sh <audio_file_path>
# Reads OPENAI_API_KEY from env or falls back to hardcoded key

AUDIO_FILE="$1"
if [ -z "$AUDIO_FILE" ]; then
  echo "Usage: transcribe.sh <audio_file>" >&2
  exit 1
fi

API_KEY="${OPENAI_API_KEY:-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}"

RESULT=$(curl -s https://api.openai.com/v1/audio/transcriptions \
  -H "Authorization: Bearer $API_KEY" \
  -F model="gpt-4o-mini-transcribe" \
  -F file="@$AUDIO_FILE" \
  -F response_format="text")

echo "$RESULT"
