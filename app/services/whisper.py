import torchaudio
import whisper

def transcribe_audio(audio):
    """
    Generate word-level and segment-level subtitles from an audio file using Whisper.
    :param audio: Audio file or BytesIO object.
    :return: Word-level and segment-level subtitles.
    """
    print("Transcribing audio...")
    # Load the Whisper model
    model = whisper.load_model("base")
        # Convert BytesIO to tensor
    audio.seek(0)  # Ensure file pointer is at the start
    waveform, sample_rate = torchaudio.load(audio)
    
    # Whisper expects 16kHz sample rate
    if sample_rate != 16000:
        waveform = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)(waveform)

    # Convert waveform to numpy array for Whisper compatibility
    audio_array = waveform.squeeze().numpy()

    # Transcribe the audio file with word-level timestamps
    result_word = model.transcribe(audio_array, word_timestamps=True, fp16=False)
    result_segment = model.transcribe(audio_array, word_timestamps=False, fp16=False)
    # Extract words and their timestamps
    subtitles = []
    subtitles_segment = []
    for segment in result_word['segments']:
        for word_data in segment['words']:
            word = word_data['word']
            start = word_data['start']
            end = word_data['end']
            subtitles.append({"word": word, "start": start, "end": end})

    for segment in result_segment['segments']:
        word = segment['text']
        start = segment['start']
        end = segment['end']
        subtitles_segment.append({"word": word, "start": start, "end": end})

    print("Transcribing audio completed!!!")
    return subtitles, subtitles_segment
