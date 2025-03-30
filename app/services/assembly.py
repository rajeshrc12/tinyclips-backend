
import assemblyai as aai
from app.config.settings import ASSEMBLYAI_API_KEY


aai.settings.api_key = ASSEMBLYAI_API_KEY


def transcribe_audio(audio):
    print("transcribing audio...")
    transcriber = aai.Transcriber()

    config = aai.TranscriptionConfig(
        speaker_labels=True, punctuate=True, format_text=True)

    transcript = transcriber.transcribe(audio, config)
    if transcript.status == aai.TranscriptStatus.error:
        print(f"Transcription failed: {transcript.error}")
        exit(1)

    subtitles_sentence = []
    for sentence in transcript.get_sentences():
        sentence_data = {
            "start": round(sentence.start / 1000, 2),  # Convert ms to sec
            "end": round(sentence.end / 1000, 2),
            "word": sentence.text
        }
        subtitles_sentence.append(sentence_data)

    output = []
    word = ""
    start = 0.0

    for i in range(len(subtitles_sentence)):
        if i + 1 == len(subtitles_sentence):
            output.append(
                {"start": start, "end": subtitles_sentence[i]["end"], "word": word + subtitles_sentence[i]["word"]})
            break

        if subtitles_sentence[i]["end"] == subtitles_sentence[i + 1]["start"]:
            word += subtitles_sentence[i]["word"] + " "
        else:
            output.append(
                {"start": start, "end": subtitles_sentence[i + 1]["start"], "word": word + subtitles_sentence[i]["word"]})
            word = ""
            start = subtitles_sentence[i + 1]["start"]

    subtitles_word = []
    for word in transcript.words:
        word_data = {
            "start": round(word.start / 1000, 2),
            "end": round(word.end / 1000, 2),
            "word": word.text
        }
        subtitles_word.append(word_data)

    print("transcription completed")
    return subtitles_word, output
