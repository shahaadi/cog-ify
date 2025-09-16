import os
import inspect
import fire
import glob
import numpy as np
import torch
from torch import autocast
from PIL import Image
import librosa
import ffmpeg
from librosa import onset
from librosa.feature import melspectrogram
import matplotlib.pyplot as plt
import pygame
import time
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeVideoClip


from diffusers import StableDiffusionPipeline
from diffusers.schedulers import LMSDiscreteScheduler

@torch.no_grad()
def diffuse(
        pipe,
        cond_embeddings, 
        cond_latents,  
        num_inference_steps,
        guidance_scale,
        eta,
    ):
    torch_device = torch.device("cpu")

    max_length = cond_embeddings.shape[1] 
    uncond_input = pipe.tokenizer([""], padding="max_length", max_length=max_length, return_tensors="pt")
    uncond_embeddings = pipe.text_encoder(uncond_input.input_ids.to(torch_device))[0]
    text_embeddings = torch.cat([uncond_embeddings, cond_embeddings])

    if isinstance(pipe.scheduler, LMSDiscreteScheduler):
        cond_latents = cond_latents * pipe.scheduler.sigmas[0]

    accepts_offset = "offset" in set(inspect.signature(pipe.scheduler.set_timesteps).parameters.keys())
    extra_set_kwargs = {}
    if accepts_offset:
        extra_set_kwargs["offset"] = 1
    pipe.scheduler.set_timesteps(num_inference_steps, **extra_set_kwargs)

    accepts_eta = "eta" in set(inspect.signature(pipe.scheduler.step).parameters.keys())
    extra_step_kwargs = {}
    if accepts_eta:
        extra_step_kwargs["eta"] = eta

    for i, t in enumerate(pipe.scheduler.timesteps):
        latent_model_input = torch.cat([cond_latents] * 2)
        if isinstance(pipe.scheduler, LMSDiscreteScheduler):
            sigma = pipe.scheduler.sigmas[i]
            latent_model_input = latent_model_input / ((sigma**2 + 1) ** 0.5)

        noise_pred = pipe.unet(latent_model_input, t, encoder_hidden_states=text_embeddings)["sample"]

        noise_pred_uncond, noise_pred_text = noise_pred.chunk(2)
        noise_pred = noise_pred_uncond + guidance_scale * (noise_pred_text - noise_pred_uncond)

        if isinstance(pipe.scheduler, LMSDiscreteScheduler):
            cond_latents = pipe.scheduler.step(noise_pred, i, cond_latents, **extra_step_kwargs)["prev_sample"]
        else:
            cond_latents = pipe.scheduler.step(noise_pred, t, cond_latents, **extra_step_kwargs)["prev_sample"]

    cond_latents = 1 / 0.18215 * cond_latents
    image = pipe.vae.decode(cond_latents)
    image = image.sample
    image = (image / 2 + 0.5).clamp(0, 1)
    image = image.cpu().permute(0, 2, 3, 1).numpy()
    image = (image[0] * 255).astype(np.uint8)

   

    return image

def interpolate(image_a, image_b, steps):
    ratio = torch.linspace(0, 1, steps)
    result = []
    for r in ratio:
        img = r * image_a + (1 - r) * image_b
        result.append(img)
    return result

def get_audio_features(audio_input):
    # Load the audio file and its sample rate
    audio_data, sample_rate = librosa.load(audio_input)
    print("Audio file path:", audio_input)


    # Compute the mel spectrogram
    n_mels = 80
    n_fft = 2048
    hop_length = 512
    mel_spectrogram = librosa.feature.melspectrogram(
        audio_data, sr=sample_rate, n_fft=n_fft, hop_length=hop_length, n_mels=n_mels
    )

    # Convert to log-mel spectrogram
    log_mel_spectrogram = librosa.power_to_db(mel_spectrogram, ref=np.max)

    # Compute the beat track
    onset_envelope = onset.onset_strength(y=audio_data, sr=sample_rate)
    bpm, _ = librosa.beat.beat_track(onset_envelope=onset_envelope, sr=sample_rate)

    return log_mel_spectrogram, sample_rate, bpm







def main(
        audio_input,
        prompts=["abstract geometry", "cosmic landscape"],
        seeds=[243, 523],
        name='ekarma_video_output',
        rootdir='.',
        num_steps=72,
        num_inference_steps=50,
        guidance_scale=7.5,
        eta=0.0,
        width=512,
        height=512,
        fps=24
):
    print("Number of prompts:", len(prompts))
    print("Number of seeds:", len(seeds))
    print("Prompts:")
    for prompt in prompts:
        print(prompt)
    print("Seeds:")
    for seed in seeds:
        print(seed)
    assert len(prompts) == len(seeds)
    assert height % 8 == 0 and width % 8 == 0

    outdir = os.path.join(rootdir, name)
    os.makedirs(outdir, exist_ok=True)
    print(f"Output directory created at {outdir}")

    pipe = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-3", use_auth_token=True)
    torch_device = torch.device("cpu")
    pipe.unet.to(torch_device)
    pipe.vae.to(torch_device)
    pipe.text_encoder.to(torch_device)

    prompt_embeddings = []
    for prompt in prompts:
        text_input = pipe.tokenizer(
            prompt,
            padding="max_length",
            max_length=pipe.tokenizer.model_max_length,
            truncation=True,
            return_tensors="pt"
        )
        with torch.no_grad():
            embed = pipe.text_encoder(text_input.input_ids.to(torch_device))[0]

        prompt_embeddings.append(embed)

    prompt_embedding_a, *prompt_embeddings = prompt_embeddings
    init_seed, *seeds = seeds
    init_a = torch.randn(
        (1, pipe.unet.in_channels, height // 8, width // 8),
        device=torch_device,
        generator=torch.Generator().manual_seed(init_seed)
    )

    log_mel_spectrogram, sample_rate, bpm = get_audio_features(audio_input)
    frame_duration = 60.0 / bpm
    frame_hop_duration = frame_duration / num_steps

    image_a = diffuse(
        pipe,
        prompt_embedding_a,
        init_a,
        num_inference_steps,
        guidance_scale,
        eta,
    )
    images = [image_a]

    for prompt_embedding, seed in zip(prompt_embeddings, seeds):
        init_b = torch.randn(
            (1, pipe.unet.in_channels, height // 8, width // 8),
            device=torch_device,
            generator=torch.Generator().manual_seed(seed)
        )
        image_b = diffuse(
            pipe,
            prompt_embedding,
            init_b,
            num_inference_steps,
            guidance_scale,
            eta,
        )

        images.extend(interpolate(image_a, image_b, num_steps))
        images.append(image_b)
        image_a = image_b

    output_video_path = os.path.join(outdir, "output_video.mp4")
    save_and_play_audio_with_images(audio_input, images, frame_duration, output_video_path)
    print(f"Video saved at {output_video_path}")


def save_and_play_audio_with_images(audio_path, images, frame_duration, output_video_path):
    pygame.init()
    screen = pygame.display.set_mode((512, 512))
    pygame.mixer.init()
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()

    frames = []

    for image in images:
        print("Shape:", image.shape)
        print("Data type:", image.dtype)
        image = image.cpu().numpy() if isinstance(image, torch.Tensor) else image
        # If the shape is (channels, height, width), then permute it
        if image.shape[0] == 3 or image.shape[0] == 4:
            image = image.transpose(1, 2, 0)

        # Normalize the image to [0, 1] if it's not already
        if image.max() > 1:
            image = image / 255.0

        # Convert to uint8
        image = (image * 255).astype(np.uint8)
        image_pil = Image.fromarray(image)
        pygame_image = pygame.image.fromstring(image_pil.tobytes(), image_pil.size, image_pil.mode)
        screen.blit(pygame_image, (0, 0))
        pygame.display.flip()   
        time.sleep(frame_duration)
        frames.append(image_pil)  # Appending the PIL image
    
    

    audio = AudioFileClip(audio_path)
    frames = [np.array(image) for image in frames]

    clip = ImageSequenceClip(frames, fps=1.0 / frame_duration)
    final_clip = CompositeVideoClip([clip.set_audio(audio)])
    final_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac")

    pygame.quit()



if __name__ == '__main__':
    audio_input = input("Please enter the audio file path: ")
    fire.Fire(main, audio_input)
