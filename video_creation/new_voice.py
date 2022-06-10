from pathlib import Path
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
from mutagen.mp3 import MP3
from tempfile import gettempdir
from rich.progress import track
import emoji
from pydub import AudioSegment

# from utils.console import print_step

# Create a client using the credentials and region defined in the [adminuser]
# section of the AWS credentials file (~/.aws/credentials).
session = Session(profile_name="default")
polly = session.client("polly")

def generate_text_mp3(reddit_obj):
    # print_step("Saving Text to MP3 files...")
    length = 0

    # Create a folder for the mp3 files.
    Path("assets/mp3").mkdir(parents=True, exist_ok=True)

    __download_mp3(reddit_obj["thread_title"], "title")
    length += __get_clip_length("title")
    
    if reddit_obj["thread_post"] != "":
        __download_mp3(reddit_obj["thread_post"], "post")
        length += __get_clip_length("post")

    for idx, comment in track(enumerate(reddit_obj["comments"]), "Saving..."):
         # ! Stop creating mp3 files if the length is greater than 50 seconds.
        if length > 50:
            break

        __download_mp3(comment["comment_body"], f"{idx}")
        length += __get_clip_length(f"{idx}")

    # ! Return the index so we know how many screenshots of comments we need to make.
    return length, idx

def __download_mp3(text, filename):
    text=__remove_emoji(text);
    try:
        # Request speech synthesis
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat="mp3", 
            VoiceId="Matthew", 
            Engine="neural")

    except (BotoCoreError, ClientError) as error:
        # The service returned an error, exit gracefully
        print(error)
        sys.exit(-1)

    # Access the audio stream from the response
    if "AudioStream" in response:
        # Note: Closing the stream is important because the service throttles on the
        # number of parallel connections. Here we are using contextlib.closing to
        # ensure the close method of the stream object will be called automatically
        # at the end of the with statement's scope.
        with closing(response["AudioStream"]) as stream:
            output = os.path.join("assets/mp3", f"{filename}.mp3")
            
            try:
                # Open a file for writing the output as a binary stream
                with open(output, "wb") as file:
                    file.write(stream.read())
            except IOError as error:
                # Could not write to file, exit gracefully
                print(error)
                sys.exit(-1)

    else:
        # The response didn't contain audio data, exit gracefully
        print("Could not stream audio")
        sys.exit(-1)

def __get_clip_length(clip_name):
    return MP3(f"assets/mp3/{clip_name}.mp3").info.length

def __remove_emoji(string):
    return emoji.get_emoji_regexp().sub(u'', string)

def __change_audio_speed(sound, speed=1.0):
    # shift the pitch up by half an octave (speed will increase proportionally)
    octaves = 0.5

    new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))

    # keep the same samples but tell the computer they ought to be played at the 
    # new, higher sample rate. This file sounds like a chipmunk but has a weird sample rate.
    chipmunk_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})

    # now we just convert it to a common sample rate (44.1k - standard audio CD) to 
    # make sure it works in regular audio players. Other than potentially losing audio quality (if
    # you set it too low - 44.1k is plenty) this should now noticeable change how the audio sounds.
    return chipmunk_sound.set_frame_rate(44100)