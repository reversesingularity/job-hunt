# Interview Buddy — Phase 3

Desktop companion for live interview preparation. **Not implemented in Slice 1.**

## Planned features

- Electron shell with push-to-talk trigger
- Stealth screen-share overlay (user-controlled visibility)
- Real-time audio transcription (Gemini / GPT-4o)
- Context from JobHunt MCP (`get_applicant_context`, job-specific tailoring)

## Scaffold status

This directory is a placeholder. Implementation begins after Slice 2 (auto-submit) is stable.

## Future stack

- `electron`, `electron-builder`
- `@google/generative-ai` or `openai` for streaming responses
- Shared MCP connection to local JobHunt server
