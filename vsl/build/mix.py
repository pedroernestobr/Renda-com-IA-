"""Mixa narração + trilha (com ducking) + efeitos e junta com os frames.

Uso: python3 mix.py            -> gera ../renda-com-ia-vsl.mp4
Se voz/take1.mp3 não existir, gera uma prévia só com trilha e efeitos.
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DUR = 103.5
MUSIC = False  # trilha desligada a pedido; True para voltar
VOICE = os.path.join(HERE, "voz", "take1_fix.wav")
SFX = os.path.join(HERE, "sfx")
OUT = os.path.join(HERE, "..", "renda-com-ia-vsl.mp4" if os.path.exists(VOICE) else "renda-com-ia-vsl-sem-voz.mp4")

# (tempo em s, efeito, volume)
CUES = [
    (0.0, "hit", 1.0), (0.0, "glitch", .5), (0.96, "glitch", .55), (2.08, "whoosh", .5), (3.0, "glitch", .55),
    (4.0, "whoosh", .55), (5.6, "hit", .9), (7.2, "whoosh", .5), (7.6, "hit", .8), (8.08, "click", .5),
    (10.5, "pop", .5), (12.35, "whoosh", .6), (12.45, "hit", .85),
    (13.4, "whoosh", .35), (14.8, "click", .7), (15.8, "whoosh", .35), (17.7, "click", .7), (18.6, "whoosh", .35), (20.4, "click", .7),
    (21.7, "riser", .45), (23.5, "hit", .9), (25.4, "pop", .4), (26.45, "pop", .4),
    (27.85, "whoosh", .5), (29.84, "hit", .7), (31.44, "whoosh", .45), (32.76, "hit", .7),
    (33.84, "hit", .8), (34.8, "whoosh", .45), (36.88, "typing", .55), (39.4, "click", .6), (39.5, "click", .4), (40.3, "pop", .45),
    (41.5, "pop", .45), (42.6, "pop", .45), (43.7, "whoosh", .55), (43.76, "pop", .6), (44.8, "pop", .6), (45.44, "pop", .6),
    (46.24, "hit", .85), (47.5, "riser", .45), (49.3, "hit", 1.0), (49.3, "ding", .35),
    (50.88, "pop", .55), (52.2, "pop", .55), (53.8, "pop", .6), (55.68, "whoosh", .45), (56.0, "whoosh", .35),
    (56.53, "pop", .5), (57.72, "pop", .5), (59.89, "pop", .5), (61.2, "pop", .5), (62.92, "pop", .5), (64.16, "pop", .5),
    (66.3, "whoosh", .5), (66.4, "hit", .6), (67.44, "hit", 1.0), (67.44, "ding", .55), (68.96, "pop", .5),
    (70.16, "click", .6), (70.6, "hit", .6), (72.8, "whoosh", .5), (74.4, "pop", .5), (76.0, "whoosh", .35),
    (76.1, "riser", .5), (77.44, "hit", .9), (79.4, "hit", .7), (81.15, "whoosh", .5), (83.95, "whoosh", .45),
    (87.28, "pop", .5), (87.8, "click", .4), (88.2, "click", .4), (88.6, "click", .4), (89.0, "click", .4), (89.4, "click", .4), (89.8, "click", .4), (90.2, "click", .4),
    (90.68, "hit", .8), (91.04, "pop", .6), (93.5, "ding", .3), (97.65, "hit", .8), (99.5, "whoosh", .45), (99.6, "ding", .35),
]


def run(cmd):
    print(" ".join(cmd[:6]), "...")
    subprocess.run(cmd, check=True)


def main():
    inputs, filters, labels = [], [], []
    # trilha em loop (ou silêncio, quando MUSIC = False)
    if MUSIC:
        inputs += ["-stream_loop", "-1", "-i", os.path.join(SFX, "music.wav")]
    else:
        inputs += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    have_voice = os.path.exists(VOICE)
    idx = 1
    if have_voice:
        inputs += ["-i", VOICE]; vidx = idx; idx += 1
    for i, (t, name, vol) in enumerate(CUES):
        inputs += ["-i", os.path.join(SFX, name + ".wav")]
        ms = int(t * 1000)
        filters.append(f"[{idx}:a]volume={vol*0.30:.3f},adelay={ms}|{ms}[s{i}]")
        labels.append(f"[s{i}]"); idx += 1
    filters.append(f"[0:a]atrim=0:{DUR},volume=0.30,afade=t=in:d=0.6,afade=t=out:st={DUR-2.5}:d=2.5[mus]")
    if have_voice:
        filters.append(f"[{vidx}:a]aresample=48000,pan=stereo|c0=c0|c1=c0,highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=120,volume=1.35,asplit=2[vo][vosc]")
        filters.append("[mus][vosc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[musd]")
        filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0[fx]")
        filters.append("[vo][musd][fx]amix=inputs=3:normalize=0,alimiter=limit=0.89,apad[aout]")
    else:
        filters.append(f"[mus]{''.join(labels)}amix=inputs={len(labels)+1}:normalize=0,alimiter=limit=0.89,apad[aout]")
    wav = os.path.join(HERE, "mix.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters), "-map", "[aout]", "-t", str(DUR), "-ar", "48000", wav])
    run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", os.path.join(HERE, "frames", "%05d.jpg"), "-i", wav,
         "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", "-t", str(DUR), OUT])
    print("ok:", os.path.abspath(OUT), "voz:", have_voice)


if __name__ == "__main__":
    main()
