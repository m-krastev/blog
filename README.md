# krastev.dev/blog

Проповеди и бележки – Hugo сайт, публикуван чрез GitHub Pages при всяко качване в `main`.

## Нова публикация

1. Създай папка `content/posts/<slug>/` с `index.md` (front matter: виж съществуващите публикации).
2. Текстът от ръкопис: `python3 scripts/import_manuscript.py РЪКОПИС.md > тяло.md` (работи и с `.docx`).
3. Аудио (по желание): сложи файла в същата папка и посочи го в `audio:`; `duration:` е дължината.
   Компресиране за говор: `ffmpeg -i запис.m4a -af loudnorm=I=-16:TP=-1.5:LRA=11 -ac 1 -c:a aac_at -b:a 48k -movflags +faststart <slug>.m4a`
4. Преглед: `hugo server`; публикуване: `git push`.
