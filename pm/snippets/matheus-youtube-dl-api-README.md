## youtube-download-api

REST API to download `.mp3` and `.mp4` files.

**Base URL endpoint** `https://youtube-download-api.matheusishiyama.repl.co`

---

### Methods:

[Video Info](#get-video-info) |
[Download .mp3](#get-download-mp3-file) |
[Download .mp4](#get-download-mp4-file)

---

#### `GET` Video Info

**endpoint:** `BaseURL/info/?url=value`

| Query | Type   | Description      |
| ----- | ------ | ---------------- |
| `url` | string | youtube url link |

**Response:**

```json
{
    "title": "Video title",
    "thumbnail": "Video thumbnail url"
}
```

---

#### `GET` Download `mp3` file

**endpoint:** `BaseURL/mp3/?url=value`

| Query | Type   | Description      |
| ----- | ------ | ---------------- |
| `url` | string | youtube url link |

**Response:**

`<video-name>.mp3` file

---

#### `GET` Download `mp4` file

**endpoint:** `BaseURL/mp4/?url=value`

| Query | Type   | Description      |
| ----- | ------ | ---------------- |
| `url` | string | youtube url link |

**Response:**

`<video-name>.mp4` file

---

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