# 🎙️ Telegram Voice Message Summarizer

This project is a Telegram bot that converts voice and video messages into text and generates a short summary.

---

## ✨ Features

- Converts Telegram voice messages (.ogg → .wav) using FFmpeg.  
- Transcribes audio to text with Google Speech Recognition.  
- Summarizes long transcripts into concise text using a Hugging Face model (cointegrated/rut5-base-multitask).  
- Automatically deletes temporary audio files after processing.  
- **Saves user data (progress, preferences, ratings, etc.) in SQLite database — progress is not lost after bot restart.**  
- Built with Python and pyTelegramBotAPI.  

---

## 🛠️ Tech Stack

- Python 3  
- FFmpeg  
- SpeechRecognition  
- Hugging Face Transformers (for summarization)  
- PyTelegramBotAPI (Telegram bot framework)  
- **SQLite (for persistent user data storage)**  

---

## 🚀 How it works

- A user sends a voice or video message to the bot.  
- The bot saves and converts it into .wav.  
- The audio is transcribed into text.  
- The text is summarized by a local Hugging Face model.  
- **User progress (language, scores, opened cards, statistics) is saved in `users.db` via SQLite.**  
- The user receives either the full transcript or a short, meaningful summary.  
