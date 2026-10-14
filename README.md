# Video Dubbing: Chinese to Vietnamese

Web application that accepts a Chinese-language video and produces
a Vietnamese-dubbed video with Vietnamese subtitles burned in.

## Planned architecture

- Frontend: React, TypeScript, Vite
- Backend API: FastAPI
- Database: PostgreSQL
- Background jobs: Celery
- Queue and broker: Redis
- Media processing: FFmpeg
- AI models: Chinese ASR, Chinese-to-Vietnamese translation, Vietnamese TTS
- Reverse proxy: Nginx
- Deployment: Docker Compose on a VPS

## Development status

- [x] Project structure
- [x] Git initialization
- [x] Environment template
- [x] PostgreSQL and Redis Compose services
- [x] FastAPI and database models
- [x] Celery worker
- [x] Job upload and status API
- [ ] AI pipeline and FFmpeg integration
- [x] Frontend
- [ ] Nginx and VPS deployment

## Initial setup

1. Copy `.env.example` to `.env`.
2. Review the local development settings.
3. Start the infrastructure:

   docker compose up -d

4. Check service status:

   docker compose ps

## Important

- Never commit `.env` or real credentials.
- Do not commit uploaded videos, generated videos, or model weights.
- Back up persistent database and application data before production changes.
