# spatial-crop-modeler skill

AI-assisted spatial crop yield simulation using DSSAT + CHIRPS + SoilGrids.
Built by Climate Data Hub — CGIAR.

Works on Claude Code, OpenAI Codex, Google Antigravity, and Gemini CLI.
All heavy computation (data download, DSSAT) runs on your machine — free.

---

## Install (pick your platform)

**Claude Code**
```bash
claude skills install github:anaguilarar/spatial-crop-modeler-skill
```

**OpenAI Codex CLI** (ChatGPT Plus / pay-as-you-go)
```bash
codex skills install github:anaguilarar/spatial-crop-modeler-skill
```

**Google Antigravity** (free with AI Studio)
```bash
agy skills install github:anaguilarar/spatial-crop-modeler-skill
```

**Gemini CLI** (free tier)
```bash
gemini skills install github:anaguilarar/spatial-crop-modeler-skill
```

---

## Prerequisites (one-time, on your machine)

Both packages are installed directly from GitHub:

```bash
pip install "ag-cube-cm[models] @ git+https://github.com/anaguilarar/ag-cube-cm.git"
pip install "aggeodata[download,mcp] @ git+https://github.com/anaguilarar/aggeodata.git"
```

For solar radiation via AgERA5, create `~/.cdsapirc`:
```
url: https://cds.climate.copernicus.eu/api/v2
key: <your-uid>:<your-api-key>
```
Register free at https://cds.climate.copernicus.eu — or use NASA POWER instead (no key needed).

---

## Usage

Just talk to your agent:

> "Simulate maize yield in Honduras, bbox [-87.5, 14.2, -87.2, 14.5], 2000 to 2020"

> "I already have the weather and soil cubes at D:/cubes/ — run DSSAT for wheat"

> "My simulation shows pixels_skipped=45, is that normal?"

The agent will ask one clarifying question if needed, show you a plan, and generate
the YAML config. You run two commands on your machine:

```bash
ag-cube-cm validate config.yaml
ag-cube-cm run config.yaml
```

Paste the results back and the agent interprets them and offers a yield map.

---

## What the AI does vs your machine

| Step | Where it runs | Cost |
|------|--------------|------|
| Generate YAML config | AI (~10K tokens) | Free (Flash) or ~$0.05 |
| Download CHIRPS/CHIRTS/SoilGrids | Your machine | Free |
| Build weather + soil datacubes | Your machine | Free |
| Run DSSAT (all pixels, all years) | Your machine | Free |
| Interpret results + yield map | AI (~5K tokens) | Free (Flash) or ~$0.02 |

A 20-year simulation costs the same AI tokens as a 1-year simulation.

---

## Supported crops and cultivars

| Cultivar | Crop | Region |
|----------|------|--------|
| IB1072 | Maize | Tropical / Central America |
| PC0002 | Maize | Temperate |
| IB1015 | Spring Wheat | Ethiopia, South Asia |
| IB1487 | Winter Wheat | Europe, North Africa |
| IB0001 | Bean / Soybean | General |

---

## Climate sources

| Variable | Source | Notes |
|----------|--------|-------|
| Precipitation | CHIRPS | 0.05 deg, 1981-present, free |
| Max/Min temperature | CHIRTS | 0.05 deg, free |
| Solar radiation | AgERA5 | 0.1 deg, free CDS account required |
| Solar radiation | NASA POWER | 0.5 deg, no account needed |

---

## License

MIT — Climate Data Hub, CGIAR
