# Product Requirements Document (PRD): YouTube Download Microservice Integration

> **Context:**
> This repository is a clone of the no-code-architects-toolkit, currently deployed to GCP Cloud Run. The existing deployment provides functional endpoint APIs. This PRD outlines the requirements to expand the toolkit’s functionality by integrating a YouTube download microservice, following the conventions and architecture of the toolkit.

---

## Project: YouTube Download Microservice Integration with No-Code Toolkit

### Goal
Integrate, dockerize, and expose the MatheusIshiyama YouTube Download API as a suite of `/v1/media/youtube` endpoints within the forked “no-code-toolkit” by Stephen Pope, ensuring seamless internal API use, clean maintainable code, and compliance with GPL v2.0.

---

## 1. Objectives

### Reliability
- Self-host all YouTube downloads behind an internal Node.js/Express microservice using ytdl-core.

### Integration
- Merge into the no-code-toolkit codebase, leveraging its dynamic route registration system.
- Maintain existing CI/CD pipelines (build, test, deploy) for the unified repo.

### Maintainability
- Containerize via Docker; enforce clear service boundaries and update guidelines.

### Compliance
- Document GPL v2.0 copyleft implications of distributing or modifying combined MIT-licensed YouTube code.

### Security
- Expose only on the private inter-container network.
- Strictly validate and sanitize all incoming URLs to prevent SSRF/RFI/injection.

---

## 2. Functional Requirements

### 2.1. Microservice Details

**Location in repo:**
```
/services/youtube-downloader/
```

**Dockerfile & Entrypoint:**
- Dockerfile based on Node.js LTS matching the toolkit baseline.
- Entrypoint script `start.sh` launches `index.js`.

**API base path:**
```
/v1/media/youtube
```

**Endpoints:**
| Path                        | Method | Description                                   | Query Params     |
|-----------------------------|:------:|-----------------------------------------------|-----------------|
| /v1/media/youtube/info      | GET    | Fetches metadata (title, duration, etc.)      | url=YOUTUBE_URL |
| /v1/media/youtube/mp3       | GET    | Streams/downloads audio in MP3 format         | url=YOUTUBE_URL |
| /v1/media/youtube/mp4       | GET    | Streams/downloads video in MP4 format         | url=YOUTUBE_URL |

**Payload validation & docs:**
- All endpoints leverage the toolkit’s Joi-based schema validator for:
  - Required `url` param
  - URL pattern: must match `^https?://(www\.)?youtube\.com/watch` or `youtu\.be/`
- Responses documented via OpenAPI v3 YAML under `/docs/media-youtube.yaml`.
- Detailed examples in main README (see § 3).

**Response behavior:**
- **Success:**
  - `200 OK` + binary stream (`Content-Type: audio/mpeg` or `video/mp4`).
- **Error:**
  - JSON payload `{ code, message }` + appropriate HTTP status (400/422/500).
  - Errors logged via the toolkit’s centralized Winston logger (no sensitive data).

### 2.2. Integration & Build

**Repository Setup:**
- Fork `stephengpope/no-code-architects-toolkit` under your org.
- Rename to `no-code-architects-toolkit-internal` (or similar).
- Define CODEOWNERS for `/services/youtube-downloader/`.

**Dynamic Route Registration:**
- In `src/index.js`, import and mount the YouTube routes:
  ```js
  const youtubeRouter = require('./services/youtube-downloader/routes');
  app.use('/v1/media/youtube', youtubeRouter);
  ```
- Add route registration docs under `docs/adding-routes.md`.

**CI/CD Pipelines:**
- Extend existing GitHub Actions workflow:
  - Lint & test `/services/youtube-downloader/`.
  - Build/push Docker image named `yourorg/youtube-downloader:latest`.
  - Deploy via Docker Compose / Kubernetes / Cloud Run (alongside toolkit).

**Licensing Implications:**
- MIT-licensed MatheusIshiyama code is GPLv2-compatible.
- Ensure LICENSE and headers in new code reference both MIT and GPLv2.
- For external distribution, tag the combined repo under GPLv2; for SaaS internal use, no code disclosure is required but include a `LICENSE_NOTICE.md`.

**Configuration & Networking:**
- **Environment variables:**
  ```ini
  YTDL_NETWORK_TIMEOUT=60000
  PORT=4000
  ```
- **Internal exposure only:**
  - Docker Compose network `internal_net`
  - No host-published ports; other services call `youtube-downloader:4000`.

### 2.3. Documentation & Support

- **README.md (root):**
  - Add “YouTube Downloader” section under Media:
    ```md
    ### Media › YouTube Downloader
    #### GET /v1/media/youtube/info?url={URL}
    #### GET /v1/media/youtube/mp3?url={URL}
    #### GET /v1/media/youtube/mp4?url={URL}
    Link to internal OpenAPI spec: /docs/media-youtube.yaml.
    ```
- **Developer Docs:**
  - Update `docs/media.md` with example curl calls, error scenarios, logging guidelines.
- **Architecture Diagram:**
  - In `docs/architecture.png`, insert a microservice box labeled “YouTube Downloader” connected to “Media Orchestrator” via the internal network.

---

## 3. Non-Functional Requirements

### Performance
- Limit CPU & memory via Docker resource constraints.
- Observe 95th-percentile latency < 200 ms for info calls; streaming endpoints scale with container count.

### Scalability
- Service is stateless; horizontal scale via replica count.

### Reliability
- `restart: always` in Docker Compose.
- Health-check on `/healthz` returning 200 if the service can fetch metadata.

### Dependency Management
- Use Node 18.x LTS; align with toolkit’s package.json.
- Lock file in version control; run `npm audit` in CI.

---

## 4. Constraints & Risks

### License
- External distribution requires GPLv2 compliance.

### YouTube changes
- Monitor ytdl-core releases; schedule bi-weekly dependency checks.

### Security
- Strict URL sanitization.
- Rate limit internal calls with the toolkit’s middleware (e.g. 10 req/sec).

### Resource usage
- Cap max download size via `--max-filesize` flag in ytdl-core.

---

## 5. Success Criteria / Acceptance

- **Build & CI:** All tests pass, new service linted and built in the toolkit pipeline.
- **Endpoint Reachability:**
  ```bash
  curl -H "x-api-key: $API_KEY" \
    http://media-orchestrator/v1/media/youtube/info?url=https://youtu.be/abc123
  ```
  returns valid JSON metadata.
- **Media Delivery:** Both MP3 and MP4 streams download correctly.
- **Logging & Errors:** Conform to toolkit standards (no PII).
- **Docs & License:** README, OpenAPI spec, and LICENSE_NOTICE.md present and accurate.
- **Security Audit:** Approves sanitization, rate limits, and network isolation.

---

## 6. Out of Scope

- Public-facing API
- Non-YouTube downloaders
- Per-user dynamic quotas

index.js

```
const express = require("express");
const ytdl = require("ytdl-core");
const cors = require("cors");

const app = express();
app.use(cors());

app.get("/", (req, res) => {
    const ping = new Date();
    ping.setHours(ping.getHours() - 3);
    console.log(
        `Ping at: ${ping.getUTCHours()}:${ping.getUTCMinutes()}:${ping.getUTCSeconds()}`
    );
    res.sendStatus(200);
});

app.get("/info", async (req, res) => {
    const { url } = req.query;

    if (url) {
        const isValid = ytdl.validateURL(url);

        if (isValid) {
            const info = (await ytdl.getInfo(url)).videoDetails;

            const title = info.title;
            const thumbnail = info.thumbnails[2].url;

            res.send({ title: title, thumbnail: thumbnail });
        } else {
            res.status(400).send("Invalid url");
        }
    } else {
        res.status(400).send("Invalid query");
    }
});

app.get("/mp3", async (req, res) => {
    const { url } = req.query;

    if (url) {
        const isValid = ytdl.validateURL(url);

        if (isValid) {
            const videoName = (await ytdl.getInfo(url)).videoDetails.title;

            res.header(
                "Content-Disposition",
                `attachment; filename="${videoName}.mp3"`
            );
            res.header("Content-type", "audio/mpeg3");

            ytdl(url, { quality: "highestaudio", format: "mp3" }).pipe(res);
        } else {
            res.status(400).send("Invalid url");
        }
    } else {
        res.status(400).send("Invalid query");
    }
});

app.get("/mp4", async (req, res) => {
    const { url } = req.query;

    if (url) {
        const isValid = ytdl.validateURL(url);

        if (isValid) {
            const videoName = (await ytdl.getInfo(url)).videoDetails.title;

            res.header(
                "Content-Disposition",
                `attachment; filename="${videoName}.mp4"`
            );

            ytdl(url, {
                quality: "highest",
                format: "mp4",
            }).pipe(res);
        } else {
            res.status(400).send("Invalid url");
        }
    } else {
        res.status(400).send("Invalid query");
    }
});

app.listen(process.env.PORT || 3500, () => {
    console.log("Server on");
});
```

package.json
```
{
    "name": "youtube-download-api",
    "description": "",
    "version": "1.0.0",
    "main": "index.js",
    "scripts": {
        "start": "node index.js",
        "test": "echo \"Error: no test specified\" && exit 1"
    },
    "repository": {
        "type": "git",
        "url": "git+https://github.com/MatheusIshiyama/youtube-download-api.git"
    },
    "author": "",
    "license": "ISC",
    "bugs": {
        "url": "https://github.com/MatheusIshiyama/youtube-download-api/issues"
    },
    "homepage": "https://github.com/MatheusIshiyama/youtube-download-api#readme",
    "dependencies": {
        "cors": "^2.8.5",
        "express": "^4.17.1",
        "ytdl-core": "^4.5.0"
    },
    "devDependencies": {}
}
```