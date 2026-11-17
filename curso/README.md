# Curso Renda com IA

Seis aulas em vídeo (estilo da VSL: fundo escuro, verde-limão e as estátuas) e um PDF de apoio por aula,
para colocar no comentário fixado da área de membros.

| Aula | Título | Duração |
|---|---|---|
| 1 | O Novo Jogo da Renda com IA | 5:32 |
| 2 | As Ferramentas Essenciais | 6:13 |
| 3 | Do Zero ao Primeiro Projeto | 5:26 |
| 4 | Como Vender Serviços de IA | 5:34 |
| 5 | Automação e Escala de Receita | 4:56 |
| 6 | Seu Negócio com IA na Prática | 5:09 |

Total: cerca de 33 minutos de vídeo.

## Pastas

- `conteudo/aula-0N.json`: roteiro (narração e slides) e conteúdo do PDF de cada aula.
- `pdf/`: os 6 PDFs prontos.
- `video/`: os 6 vídeos (MP4 720p, ~4 MB cada). Não vão para o git.
- `voz/`: narração do ElevenLabs (voz Pedro Ernesto). Não vai para o git.
- `build/`: scripts que geram tudo.

## Como refazer

```bash
cd curso/build
node render_slides.js N          # slides da aula N em PNG
python3 make_video.py N 8,16     # junta slides + voz (8,16 = onde cada arquivo de voz termina)
node make_pdf.js N               # PDF da aula N
./rebuild.sh                     # refaz os 6 vídeos
```

Para mudar o texto de uma aula: edite o `aula-0N.json`, gere a narração de novo no ElevenLabs
(salve em `voz/aula-0N_a.mp3`, `_b.mp3`) e rode os comandos acima. Os slides acompanham o tempo da voz
automaticamente. Escreva "IA" como "i-á" no campo `say` para a pronúncia sair certa.
