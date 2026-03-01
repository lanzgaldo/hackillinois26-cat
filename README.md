AI Powered Foreman Report

Inspired by zero-click architecture of Palantir, we were inspired to create an inspection system where technicians don't need to surf through multiple pages to do their inspections. Adding voice recognition and AI generated summaries allows technicians to visit multiple sites in a day quickly while ensuring quality inspection.

Caterpillar Track - Best AI Inspection

Tech Stack

Backend
- OpenAI Whisper - used to transcribe voice notes to test
- Mistral-7B - trained on public CAT D6N files and CAT inspection guidelines to classify criteria (ASAP/Soon/Okay)
- Claude Sonnet 4 - image analysis and report generation
- FastAPI - HTTPS to share Modal Volumes

Frontend
- Expo/React + TS - mobile app

AI Tools Used
- OpenAI Whisper - speech to text, generating transcripts
- Mistral-7B - trained to classify inspection data
- Claude Sonnet 4 - image analysis, report generation
- Claude - assistance, drafting prompts, code review
- Google AI Antigravity - writing the code
- Modal - AI training
