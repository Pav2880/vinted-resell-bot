# Vinted AI Resell Bot 24/7

Discord bot til resell-vurdering.

## Kommandoer

```text
/ping
/check vare: Converse CDG 243 kr god stand med boks
```

eller:

```text
!check Converse CDG 243 kr god stand med boks
```

## Railway 24/7 setup

1. Upload alle filer til GitHub.
2. Gå til Railway.
3. New Project.
4. Deploy from GitHub repo.
5. Vælg dette repo.
6. Gå til Variables.
7. Tilføj:

```text
DISCORD_TOKEN=dit_bot_token
```

8. Railway bruger `Procfile`:

```text
worker: python bot.py
```

Botten kører nu 24/7.
