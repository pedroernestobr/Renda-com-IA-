"""Monta o vídeo de uma aula: slides (PNG) + narração (mp3) -> mp4 leve.

Uso: python3 make_video.py N ENDS
  N    número da aula (1..6)
  ENDS índices (exclusivos) onde cada arquivo de voz termina, ex.: 8,16
       Os áudios ficam em curso/voz/aula-0N_a.mp3, _b.mp3, ...
Tempo dos slides: proporcional ao texto e ajustado ao silêncio mais forte
perto de cada fronteira (as pausas da narração).
"""
import json, os, re, subprocess, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FPS = 15
FADE = 0.35
LEAD = 0.5      # silêncio antes da voz
GAP = 0.6       # silêncio entre blocos de voz
TAIL = 1.0


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        print(r.stderr[-1500:]); raise SystemExit(1)
    return r


def dur(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).stdout)


def silences(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "silencedetect=noise=-38dB:d=0.22", "-f", "null", "-"],
                       capture_output=True, text=True)
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    return [((a + b) / 2, b - a) for a, b in zip(st, en)]


def main():
    n = int(sys.argv[1]); ends = [int(x) for x in sys.argv[2].split(",")]
    L = json.load(open(os.path.join(ROOT, "conteudo", f"aula-0{n}.json"), encoding="utf-8"))
    sl = L["slides"]; man = json.load(open(os.path.join(ROOT, "out", f"aula-0{n}", "manifest.json")))
    tmp = os.path.join(ROOT, "out", f"aula-0{n}", "tmp"); os.makedirs(tmp, exist_ok=True)
    voz = sorted(glob.glob(os.path.join(ROOT, "voz", f"aula-0{n}_*.mp3")))
    assert len(voz) == len(ends), (voz, ends)

    # 1) áudio: wav mono 44.1k, silêncios entre blocos, e tempo das fronteiras
    parts, bounds, t0, start = [], [0.0], LEAD, 0
    def sil(sec, name):
        p = os.path.join(tmp, name); run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", str(sec), p]); return p
    parts.append(sil(LEAD, "sil0.wav"))
    for ci, (mp3, end) in enumerate(zip(voz, ends)):
        w = os.path.join(tmp, f"v{ci}.wav"); run(["ffmpeg", "-y", "-i", mp3, "-ar", "44100", "-ac", "1", w])
        D = dur(w); sis = silences(w)
        idx = list(range(start, end)); chars = [len(sl[i]["say"]) for i in idx]; tot = sum(chars)
        cum = 0
        for j, i in enumerate(idx):
            cum += chars[j]
            if j == len(idx) - 1: break
            est = cum / tot * D
            cand = [(d, m) for m, d in sis if abs(m - est) <= 2.5]
            m = max(cand)[1] if cand else est
            bounds.append(t0 + m)
        bounds.append(t0 + D)  # fim do bloco = começo do próximo
        parts.append(w); t0 += D
        if ci < len(voz) - 1:
            parts.append(sil(GAP, f"gap{ci}.wav")); t0 += GAP
            bounds[-1] = t0  # o próximo slide começa depois da pausa
        start = end
    parts.append(sil(TAIL, "tail.wav")); total = t0 + TAIL
    lst = os.path.join(tmp, "a.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    audio = os.path.join(tmp, "narr.wav"); run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", audio])

    # fronteiras: bounds[i] = início do slide i ; ajusta para a lista de slides
    B = [0.0] + [b for b in bounds[1:len(sl)]]
    B = sorted(set(round(x, 3) for x in B))
    while len(B) < len(sl): B.append(B[-1] + 1)
    B = B[:len(sl)]
    d = [(B[i + 1] if i + 1 < len(sl) else total) - B[i] for i in range(len(sl))]
    print("duração total %.1fs | slides %d | min %.1fs max %.1fs" % (total, len(sl), min(d), max(d)))

    # 2) um clipe por slide (estados de revelação) e xfade entre eles
    offs = [B[i] - 0.18 if i else 0.0 for i in range(len(sl))]
    clips = []
    for i, s in enumerate(sl):
        k = man[i]; L_i = (offs[i + 1] + FADE - offs[i]) if i + 1 < len(sl) else (total - offs[i])
        if k == 1: starts = [0.0]
        elif s["t"] == "compare": starts = [0.0, 0.18, 0.55]
        elif s["t"] == "prompt": starts = [0.0, 0.25]
        else: starts = [0.0] + [0.14 + 0.80 * j / (k - 1) for j in range(k - 1)]
        times = [x * L_i for x in starts] + [L_i]
        lines = []
        for j in range(k):
            img = os.path.join(ROOT, "out", f"aula-0{n}", f"s{i:02d}_{j}.png")
            lines.append(f"file '{img}'\nduration {max(times[j + 1] - times[j], 0.05):.3f}\n")
        lines.append(f"file '{img}'\n")
        cl = os.path.join(tmp, f"c{i:02d}.txt"); open(cl, "w").write("".join(lines))
        mp = os.path.join(tmp, f"c{i:02d}.mp4")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", cl, "-r", str(FPS), "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", mp])
        clips.append(mp)

    inp = []; [inp.extend(["-i", c]) for c in clips]
    fc = []; prev = "[0:v]"
    for i in range(1, len(clips)):
        fc.append(f"{prev}[{i}:v]xfade=transition=fade:duration={FADE}:offset={offs[i]:.3f}[x{i}]"); prev = f"[x{i}]"
    fc.append(f"{prev}[{len(clips)}:v]overlay=x='-w+w*t/{total:.2f}':y=H-h:shortest=0[v]")
    out = os.path.join(ROOT, "video"); os.makedirs(out, exist_ok=True)
    dst = os.path.join(out, f"aula-0{n}.mp4")
    bar = ["-f", "lavfi", "-i", f"color=c=0xb6f23e:s=1280x6:r={FPS}"]
    run(["ffmpeg", "-y", *inp, *bar, "-i", audio, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", f"{len(clips) + 1}:a",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "64k", "-ac", "1", "-t", f"{total:.2f}", "-movflags", "+faststart", dst])
    print("ok", dst, "%.1f MB" % (os.path.getsize(dst) / 1e6), "%.1f min" % (total / 60))
    json.dump({"B": B, "total": total}, open(os.path.join(out, f"aula-0{n}.tempos.json"), "w"))


if __name__ == "__main__":
    main()
