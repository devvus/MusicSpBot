<div align="center">

# 🌸 DevuxMitsu - The Love Hashira Music Bot 🌸

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHp1M3N2ZTF2N2V4OXo3Y3Z2ZTF2N2V4OXo3Y3Z2ZTF2N2V4OXomZXA9djFfaW50ZXJuYWxfnaWQmbp3cT1MvZ2dpZjEyOC9naWZhbjiw/giphy.gif" width="400" alt="Mitsuri Kanroji Banner"/>

<p><b>A high-performance, resilient Telegram music streaming bot infused with the passion of the Love Hashira! Powered by custom high-speed YouTube API proxy routing, seamless PyTgCalls streaming, and unshakeable stability.</b></p>

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-pink.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Pyrogram](https://img.shields.io/badge/Pyrogram-Async-brightgreen.svg?style=flat-square&logo=telegram&logoColor=white)](https://docs.pyrogram.org)
[![PyTgCalls](https://img.shields.io/badge/PyTgCalls-Stream-ff69b4.svg?style=flat-square&logo=soundcharts&logoColor=white)](https://py-tgcalls.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![Railway Deployment](https://img.shields.io/badge/Deploy-Railway-blueviolet.svg?style=flat-square&logo=railway&logoColor=white)](https://railway.com)

</div>

---

## 💖 Overview

**DevuxMitsu** is an advanced, production-grade Telegram music bot engineered to bypass modern YouTube rate limits and restrictions through a dedicated asynchronous custom API proxy engine. Designed with the grace and explosive power of Mitsuri Kanroji, it delivers crystal-clear audio streams directly into Telegram voice chats with zero lag, instant search resolution, and bulletproof fallback mechanisms.

---

## 🌟 Key Features

* **Custom YouTube API Proxy Integration:** Routes all music queries and high-speed audio streams through an optimized backend proxy, completely eliminating `Sign in to confirm you’re not a bot` errors and rate-limiting blocks.
* **Lightning-Fast Asynchronous Engine:** Built on top of Python's `asyncio` and `aiohttp` to ensure non-blocking event loops, capable of handling high-concurrency group requests effortlessly.
* **Robust Zero-Downtime Fallback:** Automatically switches between the primary custom API proxy and native search extractors (`py_yt` & `yt-dlp`) to guarantee uninterrupted music playback.
* **Advanced Voice Chat Streaming:** Powered by `py-tgcalls` for stable, high-fidelity Telegram voice chat and video streaming.
* **Multi-Platform & Playlist Support:** Full support for single tracks, direct links, search queries, and massive YouTube playlists.
* **One-Click Cloud Deployment:** Pre-configured with `Dockerfile`, `Procfile`, and `app.json` for instant deployment on **Railway**, Heroku, and VPS environments.

---

## 🛠️ Environment Variables

To run DevuxMitsu successfully, configure the following environment variables in your deployment dashboard (`.env` or Railway Variables):

| Variable | Description | Required |
| :--- | :--- | :--- |
| `API_ID` | Your Telegram API ID from [my.telegram.org](https://my.telegram.org) | **Yes** |
| `API_HASH` | Your Telegram API Hash from [my.telegram.org](https://my.telegram.org) | **Yes** |
| `BOT_TOKEN` | Your Telegram Bot Token from [@BotFather](https://t.me/BotFather) | **Yes** |
| `MONGO_URL` | MongoDB connection URI from [MongoDB Atlas](https://cloud.mongodb.com) | **Yes** |
| `OWNER_ID` | Telegram User ID of the bot owner | **Yes** |
| `LOGGER_ID` | Telegram Log Group / Channel ID for activity tracking | **Yes** |
| `SESSION` | Pyrogram PyTgCalls String Session for the assistant account | **Yes** |
| `YOUTUBE_API_URL` | Custom YouTube API proxy base URL | **Yes** |
| `YOUTUBE_API_KEY` | Authentication key for the custom YouTube API proxy | **Yes** |

---

## 🚀 Quick Setup & Deployment

### Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/devvus/DevuxMitsu.git
   cd DevuxMitsu
   ```

2. **Configure environment variables:**
   Copy `sample.env` to `.env` and fill in your credentials:
   ```bash
   cp sample.env .env
   nano .env
   ```

3. **Install dependencies and start the bot:**
   ```bash
   pip install -r requirements.txt
   python3 -m anony
   ```

### 🚄 Deploy on Railway (Recommended)

Click the button below or deploy manually via Railway CLI:
1. Create a new project on [Railway](https://railway.com).
2. Connect your `DevuxMitsu` GitHub repository.
3. Add all required environment variables listed in the table above.
4. Deploy! The bot will automatically build and start streaming.

---

## 🎵 Commands Reference

| Command | Arguments / Usage | Description |
| :--- | :--- | :--- |
| `/play` | `<song name / URL>` | Plays the requested song in the voice chat. |
| `/vplay` | `<video name / URL>` | Streams video in the voice chat. |
| `/pause` | None | Pauses the current playing stream (Admin/Auth). |
| `/resume` | None | Resumes the paused stream (Admin/Auth). |
| `/skip` | None | Skips to the next track in the queue (Admin/Auth). |
| `/end` | None | Stops streaming and clears the queue (Admin/Auth). |
| `/ping` | None | Checks bot latency and system status. |

---

## 🌸 Credits & Acknowledgements

* **Developer:** [Devvus](https://github.com/devvus)
* **Theme Inspiration:** Mitsuri Kanroji (Demon Slayer: Kimetsu no Yaiba)
* **Core Architecture:** Based on AnonXMusic & PyTgCalls

<div align="center">
<p><i>Made with 💖 and Passion by the Love Hashira.</i></p>
</div>
