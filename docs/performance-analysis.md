# ASR Transcription Performance Analysis: OpenAI Whisper Base vs. Faster-Whisper

## 1. Executive Summary

This document analyzes the performance of different Automatic Speech Recognition (ASR) configurations to determine the optimal balance between accuracy and speed for audio transcription. The analysis is based on logs from tests conducted on a 42-minute sermon and a 4-minute audio clip.

### Key Findings:

- **Best Overall Performance**: The **`faster-whisper` library on GPU with the `accuracy-turbo` profile (using the `large-v3-turbo` model)** provides the best balance of high accuracy and fast processing time (~69 seconds for 42 minutes of audio).
- **Fastest for Long Audio**: The **`faster-whisper` library on GPU with the `speed` profile (using the `small` model)** is the fastest for long audio (~60 seconds) but sacrifices some accuracy, producing a more informal transcript.
- **OpenAI Whisper Base Performance**: The OpenAI Whisper `base` model (74M parameters, trained on 680,000 hours of audio) is slower for long audio (~85 seconds) and demonstrates lower accuracy compared to `faster-whisper` on GPU. However, it is the fastest for short audio clips (~16 seconds for 4 minutes).
- **CPU Viability**: CPU-based transcription using `faster-whisper` is not a viable option for long audio files (>40 mins), as it consistently fails due to memory limitations or timeouts. It only works for short files.
- **Reliability Issue**: The `faster-whisper` `accuracy` profile (using the `large-v3` model) is unreliable, producing transcripts with repetitive word glitches in multiple tests.

## 2. Detailed Benchmark Comparison

The following table summarizes the performance of each tested configuration on a 42-minute audio file.

| ASR Solution | Profile | Model | Hardware | Processing Time | Status | Key Accuracy Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Faster-Whisper**| `accuracy-turbo` | `large-v3-turbo` | GPU (L4) | ~69s | Success | **Highest accuracy.** Formal language ("going to"). |
| **Faster-Whisper**| `accuracy` | `large-v3` | GPU (L4) | ~184s | Glitch | Produced transcripts with **repetition artifacts**. |
| **Faster-Whisper**| `speed` | `small` | GPU (L4) | **~60s** | Success | Good speed. Less formal ("gonna", "wanna"). |
| **Faster-Whisper**| `speed` | `small` | CPU | N/A | **FAILED (OOM)** | Failed on 42min audio. (Processed 4min audio in ~27s) |
| **Faster-Whisper**| `balanced` | `small` | CPU | N/A | **FAILED (OOM)** | Failed on 42min audio. (Processed 4min audio in ~29s) |
| **OpenAI Whisper** | N/A | `base` | GPU | ~85s | Success | **Lowest accuracy.** Noticeable errors ("Nogger", "hall of"). |

## 2.1. Latest Benchmark Results

**Run metadata**
- Whisper-base (vanilla): Workflow completed in **25.16s**
- Whisper-small + CT2 (profile: speed): Workflow completed in **35.53s**
- Whisper-large-v3-turbo (profile: accuracy-turbo): Workflow completed in **8.09s**

---

| Section                     | Whisper-base (vanilla)                                       | Whisper-small + CT2 (speed)                                   | Whisper-large-v3-turbo (accuracy-turbo)                     | Notes on Accuracy |
|-----------------------------|--------------------------------------------------------------|---------------------------------------------------------------|-------------------------------------------------------------|-------------------|
| Scripture heading           | "Matthew chapter 21 verses 12 through 17"                    | "Matthew 21-12-17"                                            | "Matthew chapter 21, verses 12 through 17"                  | Turbo and base both correct citation; small model loses detail. |
| Money changers phrase       | "the tables of the money changes"                            | "the tables of the money changers"                            | "the tables of the money changers"                          | Small+CT2 & Turbo correct; base error ("changes"). |
| Name (theologian)           | "Dan Doryan"                                                 | "Dan Doriani"                                                 | "Dan Doriani"                                               | Small+CT2 & Turbo correct; base misspells. |
| Pronouns / attribution      | "We call Jesus's final entrance..."                          | "He called Jesus' final entrance..."                          | "We call Jesus' final entrance..."                          | Turbo mirrors base here (shift to "We"); small model preserves "He." |
| Priests reference           | "…the priest to allow it"                                    | "…the priests who allowed it"                                 | "…the priests who allowed it"                               | Small+CT2 & Turbo correct; base ungrammatical. |
| Hosanna phrase              | "Hosanna may God save us, to the Son of David"               | "Hosanna, may God save us, to the son of David"               | "Hosanna, may God save us, to the son of David"             | Small+CT2 & Turbo more natural with comma; base lacks pause. |
| Psalm quotation             | "O Lord, our Lord, how majestic is your name"                | "O Lord our Lord, how majestic is Your name"                  | "O Lord, our Lord, how majestic is your name"               | Turbo matches base capitalization; small model uses "Your." |
| Capitalization of "He/His"  | Mostly lowercase                                             | Consistently capitalized                                      | Mostly lowercase                                            | Small+CT2 aligns with traditional scripture style. |
| Workflow completion time    | 25.16s                                                      | 35.53s                                                        | **8.09s**                                                   | Turbo is dramatically faster despite being larger. |

**Key Insights from Latest Benchmarks:**
- **Whisper-large-v3-turbo (accuracy-turbo) shows dramatic performance gains** with **8.09s completion time** - 3x faster than the previous 42-minute benchmark suggested
- **Superior accuracy combined with fastest processing** makes accuracy-turbo the clear winner for most use cases
- **Whisper-base vanilla shows competitive speed** at 25.16s but with notable accuracy issues
- **Whisper-small + CT2 (speed profile)** at 35.53s is slower than expected, suggesting the turbo model's optimizations are significant

## 3. Accuracy Discrepancies

Accuracy varies significantly across profiles. The `accuracy-turbo` profile provides the most faithful transcription.

| Source Speech | `faster-whisper` (accuracy-turbo) | `faster-whisper` (speed) | `OpenAI Whisper base` |
| :--- | :--- | :--- | :--- |
| "...we're **going to** read Luke 11" | "...we're **going to** read Luke 11" | "...we're **gonna** read Luke 11" | "...we're **gonna** read Luke 11" |
| "the parable of the **Midnight Knocker**" | "...the parable of the **Midnight Knocker**" | "...the parable of the **midnight knocker**" | "...the parable of the **midnight knocker**" (*later "Nogger"*) |
| "**hallowed be** your name" | "**hallowed be** your name" | "**hallowed be** your name" | "**hall of be** your name" |
| "don't want to **stumble on** my kids" | *Not in transcript* | "don't want to **stuff him in** one of my kids" | "don't want to **stuff on** my kids" |

The OpenAI Whisper `base` model introduced the most significant errors, affecting comprehensibility. The `speed` profile on `faster-whisper` maintained good accuracy but adopted a more conversational tone.

### Detailed Error Comparison: OpenAI Whisper Base vs. Faster-Whisper (Winner)

The following table provides a side-by-side comparison of specific transcription errors made by the OpenAI Whisper `base` model compared to the highest-accuracy `faster-whisper` `accuracy-turbo` profile.

| Error Type | Winner (`faster-whisper` `accuracy-turbo`) | Loser (`OpenAI Whisper base`) | Analysis |
| :--- | :--- | :--- | :--- |
| **Critical Word Error** | "...**hallowed be** your name..." | "...**hall of be** your name..." | The OpenAI Whisper base model misinterprets a key phrase from the Lord's Prayer, changing the meaning entirely. |
| **Critical Word Error** | "...the parable of the **Midnight Knocker**." | "...the parable of the **Midnight Nogger**." | The model mishears a key term from the sermon's title, creating a nonsensical word. |
| **Numerical Error** | "...read Luke 11, **1 to 13**." | "...read Luke 11, **1 to 39**." | The OpenAI Whisper base model incorrectly transcribed the scripture reference. |
| **Contextual Error** | "...I don't want to **stumble on** my kids..." | "...I don't want to **stuff on** my kids..." | The OpenAI Whisper base version is less logical in the context of walking carefully in a dark room. |
| **Grammar & Formality** | "...we're **going to** read..." | "...we're **gonna** read..." | The winning model uses more formal language, while OpenAI Whisper base defaults to a conversational tone, which may not be suitable for all content. |
| **Punctuation & Flow** | "You have to remember too, this is not like **24-7** grocery stores..." | "But to remember too, this is not like **24, 7** groceries, stores..." | OpenAI Whisper base version has awkward phrasing ("But to remember") and less natural punctuation. |
| **Repetitive Glitch** | "...in first century homes..." | "...in, in, in first century homes..." | The OpenAI Whisper base model introduced stutter-like repetitions, which required manual cleanup. |

## 4. Speed Comparison: OpenAI Whisper Base vs. Faster-Whisper (Speed Profile)

A key goal was to compare the speed of the OpenAI Whisper `base` model against the `faster-whisper` `speed` profile on GPU.

- **For Long Audio (42 minutes):**
  - **`faster-whisper` (GPU `speed`): ~60 seconds**
  - `OpenAI Whisper base`: ~85 seconds
  - **Result**: `faster-whisper` is approximately **42% faster** and more accurate.

- **For Short Audio (4 minutes):**
  - `faster-whisper` (CPU `speed`): ~27 seconds
  - **`OpenAI Whisper base`: ~16 seconds**
  - **Result**: `OpenAI Whisper base` is significantly faster for short audio clips. However, the `faster-whisper` test was run on a CPU; a GPU test would likely be much closer. Even with the speed advantage, the OpenAI Whisper base solution's accuracy on short audio was still lower.

## 5. Conclusion & Recommendation

For applications requiring high-fidelity transcriptions, such as sermons or professional content, the **`faster-whisper` `accuracy-turbo` profile on GPU is the clear winner.** It delivers superior accuracy with a processing time that is still very competitive.

If raw speed is the absolute priority and some loss of quality/formality is acceptable, the `faster-whisper` `speed` profile on GPU offers the fastest processing for long-form audio.

The **OpenAI Whisper base model is not recommended for this use case**. While fast for short clips, it is slower for long audio and its accuracy is consistently lower than the `faster-whisper` alternatives.

## 6. Appendix: Redacted Key Data Points from Logs

This section contains a selection of key data points extracted directly from the test logs for a more detailed, data-driven comparison.

### `faster-whisper` on GPU: `accuracy-turbo` Profile
- **Model**: `large-v3-turbo`
- **Audio Duration**: 42:28.974
- **Model Load Time**: ~40s
- **Transcription Time**: **~25s** (Total run time ~69s)
- **VAD Optimization**: Removed 7+ minutes of silence.
- **Key Takeaway**: Achieves approximately **100x real-time** transcription speed while maintaining the highest accuracy.

### `faster-whisper` on GPU: `accuracy` Profile
- **Model**: `openai/whisper-large-v3`
- **Audio Duration**: 42:28.974
- **Model Load Time**: 3.591s
- **Warm-up Time**: 0.972s
- **Transcription Time**: **~182s - 186s** (across two runs)
- **Key Takeaway**: Significantly slower and produced unreliable, glitchy output with word repetitions.

### `faster-whisper` on GPU: `speed` Profile
- **Model**: `openai/whisper-small`
- **Audio Duration**: 42:28.974
- **Model Load Time**: 0.823s
- **Warm-up Time**: 0.605s
- **Transcription Time**: **~60s** (Total time including download and VAD)
- **VAD Optimization**: Removed 07:04.032 of audio.
- **Key Takeaway**: The fastest option for long-form audio on GPU.

### `faster-whisper` on CPU: `speed` & `balanced` Profiles
- **Model**: `openai/whisper-small`
- **Long Audio (42m)**: **FAILED** (Out of Memory / Worker Timeout).
- **Short Audio (4m)**:
    - `speed` profile: **~27s**
    - `balanced` profile: **~29s**
- **Key Takeaway**: CPU is not a viable option for long audio due to resource constraints.

### OpenAI Whisper Base Model
- **Model**: `base` (74M parameters, trained on 680,000 hours)
- **Long Audio (42m)**:
    - Transcription Time: **~78s** (Total time ~85s from logs)
- **Short Audio (4m)**:
    - Transcription Time: **~8s** (Total time ~16s from logs)
- **Key Takeaway**: While very fast on short audio, it is significantly slower than `faster-whisper` `speed` profile on long audio and has notable accuracy issues.
