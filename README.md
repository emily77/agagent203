# Japan Life Language School OS

This repository is the lightweight deployment entrypoint for the AI 日語補習班營運平台。

It boots the latest verified application bundle at runtime, then serves the FastAPI app through `uvicorn api:app`.

## Deployment Notes

- The runtime bundle is downloaded from a public artifact URL.
- The bootstrap verifies the bundle SHA-256 before extracting it.
- This repo intentionally stays minimal so Render can redeploy quickly while GitHub write access is being stabilized.
