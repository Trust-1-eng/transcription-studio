#!/bin/bash
# ═══════════════════════════════════════════
# API Test Script — Assembly Transcription Studio
# ═══════════════════════════════════════════

BASE="http://localhost:8000"
TID="${1:-f964af22-242d-4186-9bb0-86c8fcecc07d}"  # Pass transcript ID as arg, or use last known
PASS=0
FAIL=0
SKIP=0

green() { printf "\033[32m✓ %-45s %s\033[0m\n" "$1" "$2"; PASS=$((PASS+1)); }
red()   { printf "\033[31m✗ %-45s %s\033[0m\n" "$1" "$2"; FAIL=$((FAIL+1)); }
yellow(){ printf "\033[33m⊘ %-45s %s\033[0m\n" "$1" "$2"; SKIP=$((SKIP+1)); }

check() {
  local name="$1" url="$2" expect_type="$3"
  local code size ctype
  read code size ctype < <(curl -s -o /tmp/_test_body -w "%{http_code} %{size_download} %{content_type}" "$url")
  if [ "$code" = "200" ]; then
    if [ -n "$expect_type" ] && ! echo "$ctype" | grep -qi "$expect_type"; then
      red "$name" "200 but type=$ctype (expected $expect_type)"
    else
      green "$name" "${code} ${size}b"
    fi
  else
    red "$name" "HTTP $code"
  fi
}

check_post() {
  local name="$1" url="$2" body="$3"
  local code
  code=$(curl -s -o /tmp/_test_body -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$body" "$url")
  if [ "$code" = "200" ]; then
    green "$name" "$code"
  else
    red "$name" "HTTP $code — $(head -c 200 /tmp/_test_body)"
  fi
}

echo ""
echo "══════════════════════════════════════════════"
echo "  Testing API  •  TID: $TID"
echo "══════════════════════════════════════════════"
echo ""

echo "─── Health & Core ───"
check "GET /api/health"                "$BASE/api/health"
check "GET /api/transcript/{tid}"      "$BASE/api/transcript/$TID"
check "GET /api/resume/{tid}"          "$BASE/api/resume/$TID"

echo ""
echo "─── Upload (audio) ───"
# Create tiny test audio
ffmpeg -y -f lavfi -i "sine=frequency=440:duration=1" /tmp/_test.mp3 2>/dev/null
UPLOAD=$(curl -s -F "file=@/tmp/_test.mp3" "$BASE/api/upload")
FID=$(echo "$UPLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('file_id',''))" 2>/dev/null)
if [ -n "$FID" ]; then
  green "POST /api/upload (audio)"       "file_id=$FID"
else
  red "POST /api/upload (audio)"         "$UPLOAD"
fi

echo ""
echo "─── Upload (video) ───"
ffmpeg -y -f lavfi -i "sine=frequency=440:duration=1" -f lavfi -i "color=c=blue:s=160x120:d=1" -shortest /tmp/_test.mp4 2>/dev/null
UPLOAD_V=$(curl -s -F "file=@/tmp/_test.mp4" "$BASE/api/upload")
FID_V=$(echo "$UPLOAD_V" | python3 -c "import sys,json; print(json.load(sys.stdin).get('file_id',''))" 2>/dev/null)
if [ -n "$FID_V" ]; then
  green "POST /api/upload (video→mp3)"   "file_id=$FID_V"
else
  red "POST /api/upload (video→mp3)"     "$UPLOAD_V"
fi

echo ""
echo "─── Export: Transcript ───"
check "GET export/txt"                  "$BASE/api/export/$TID/txt"                "text/plain"
check "GET export/docx"                 "$BASE/api/export/$TID/docx"               "wordprocessing"
check "GET export/pdf"                  "$BASE/api/export/$TID/pdf"                "pdf"
check "GET export/md"                   "$BASE/api/export/$TID/md"                 "markdown"

echo ""
echo "─── Export: Captions ───"
check "GET export/srt"                  "$BASE/api/export/$TID/srt"                "text/plain"
check "GET export/vtt"                  "$BASE/api/export/$TID/vtt"                "text/vtt"

echo ""
echo "─── Export: Paragraphs ───"
check "GET export/paragraphs/txt"       "$BASE/api/export/$TID/paragraphs/txt"     "text/plain"
check "GET export/paragraphs/docx"      "$BASE/api/export/$TID/paragraphs/docx"    "wordprocessing"
check "GET export/paragraphs/pdf"       "$BASE/api/export/$TID/paragraphs/pdf"     "pdf"
check "GET export/paragraphs/md"        "$BASE/api/export/$TID/paragraphs/md"      "markdown"
check "GET export/paragraphs/json"      "$BASE/api/export/$TID/paragraphs/json"    "json"

echo ""
echo "─── Export: Sentences ───"
check "GET export/sentences/txt"        "$BASE/api/export/$TID/sentences/txt"      "text/plain"
check "GET export/sentences/csv"        "$BASE/api/export/$TID/sentences/csv"      "csv"
check "GET export/sentences/srt"        "$BASE/api/export/$TID/sentences/srt"      "text/plain"
check "GET export/sentences/json"       "$BASE/api/export/$TID/sentences/json"     "json"

echo ""
echo "─── Export: Words ───"
check "GET export/words/json"           "$BASE/api/export/$TID/words/json"         "json"
check "GET export/words/csv"            "$BASE/api/export/$TID/words/csv"          "csv"

echo ""
echo "─── Export: Translation (en) ───"
check "GET export/translation/en/txt"   "$BASE/api/export/$TID/translation/en/txt"  "text/plain"
check "GET export/translation/en/docx"  "$BASE/api/export/$TID/translation/en/docx" "wordprocessing"
check "GET export/translation/en/srt"   "$BASE/api/export/$TID/translation/en/srt"  "text/plain"
check "GET export/translation/en/vtt"   "$BASE/api/export/$TID/translation/en/vtt"  "text/vtt"

echo ""
echo "─── Export: Analytics ───"
check "GET export/entities/csv"         "$BASE/api/export/$TID/entities/csv"       "csv"
check "GET export/sentiment/csv"        "$BASE/api/export/$TID/sentiment/csv"      "csv"
check "GET export/topics/json"          "$BASE/api/export/$TID/topics/json"        "json"
check "GET export/highlights/txt"       "$BASE/api/export/$TID/highlights/txt"     "text/plain"

echo ""
echo "─── Export: ZIP ───"
check_post "POST export/zip (basic)"    "$BASE/api/export/$TID/zip" '{"formats":["txt","srt","paragraphs_txt","sentences_csv","words_csv"]}'
check_post "POST export/zip (full)"     "$BASE/api/export/$TID/zip" '{"formats":["txt","docx","pdf","md","srt","vtt","paragraphs_txt","paragraphs_json","sentences_txt","sentences_csv","sentences_srt","words_json","words_csv","translation_en_txt"]}'

echo ""
echo "══════════════════════════════════════════════"
printf "  Results:  \033[32m%d passed\033[0m  \033[31m%d failed\033[0m  \033[33m%d skipped\033[0m\n" $PASS $FAIL $SKIP
echo "══════════════════════════════════════════════"
echo ""
