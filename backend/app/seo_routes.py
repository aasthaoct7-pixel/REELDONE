@router.post("/generate")
async def generate_seo(request: ScriptRequest):
    # Reject empty scripts early with a clear error message.
    if not request.script.strip():
        raise HTTPException(status_code=400, detail="Script is empty")

    # Ask the Muse model on Modal to write the SEO for every platform.
    try:
        answer = ask_muse(SYSTEM_PROMPT, request.script)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Muse call failed: {error}")

    # The model may wrap JSON in extra text, so keep only the {...} part.
    start = answer.find("{")
    end = answer.rfind("}")
    if start == -1 or end == -1:
        raise HTTPException(status_code=502, detail="Model did not return JSON")

    # strict=False allows line breaks inside text values.
    # If parsing still fails, show the real reason to help debugging.
    try:
        return json.loads(answer[start : end + 1], strict=False)
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=502,
            detail=f"JSON parse error: {error} | answer length: {len(answer)} | last 150 chars: {answer[-150:]}",
        )
