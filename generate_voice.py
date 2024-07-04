import asyncio, pathlib
from pydantic import SecretStr

from novelai_python import VoiceGenerate, VoiceResponse, JwtCredential, APIError
from novelai_python.sdk.ai.generate_voice import VoiceSpeakerV2, VoiceSpeakerV1
from novelai_python.utils.useful import enum_to_list

jwt = "pst-"

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def generate_voice(text: str):
    credential = JwtCredential(jwt_token=SecretStr(jwt))
    print(f"VoiceSpeakerV2 List:{enum_to_list(VoiceSpeakerV2)}")
    try:
        voice_gen = VoiceGenerate.build(
            text=text,
            voice_engine=VoiceSpeakerV1.Crina,  # VoiceSpeakerV2.Ligeia,
        )
        result = await voice_gen.request(
            session=credential
        )
    except APIError as e:
        print(f"Error: {e.message}")
        return None
    else:
        print(f"Meta: {result.meta}")
    file = result.audio
    with open("generate_voice.mp3", "wb") as f:
        f.write(file)
    print("Voice generated successfully")

# This part is only executed when the script is run directly
if __name__ == "__main__":
    asyncio.run(generate_voice("Hello, I am a test voice, limit 1000 characters"))