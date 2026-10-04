# vLLM-EVOx2

Imágenes y configuraciones de `docker compose` para disponibilizar modelos de lenguaje con **vLLM** sobre la arquitectura **ROCm** de la **GMKtec EVO-X2** (AMD Ryzen AI MAX+ 395 / iGPU Radeon 8060S = `gfx1151` / "Strix Halo", 128 GB de memoria unificada).

Cada modelo vive en su propia carpeta con un `docker-compose.yaml` independiente.

## Estructura

```
vLLM-EVOx2/
├── .env.example          # plantilla del token HF (cópiala a .env en la raíz)
├── .gitignore            # ignora .env
├── Qwen3.8-27B/            # denso 27B, BF16, abierto          → 8002
├── gemma-4-31B/            # multimodal 31B, BF16, gated       → 8003
├── Muse-Glimmer-30B/       # multimodal 30B, BF16, abierto     → 8004
├── gpt-oss-120b/           # MoE 117B, MXFP4 (experimental)    → 8005
├── Llama-3.3-70B-AWQ/      # denso 70B, INT4 (AWQ)             → 8006
└── Nemotron-3.5-Lightning/ # MoE 30B, BF16, híbrido Mamba      → 8007
```

## Requisitos del host (EVO-X2)

El host debe estar preparado **una sola vez** (BIOS + kernel + Docker). Ver el plan
de instalación: `plan-ubuntu-server-EVO-x2.md`. Resumen:

- **BIOS**: UMA Frame Buffer Size al mínimo (2 GB) → memoria dinámica (GTT).
- **Kernel (GRUB)**: `amdgpu.gttsize=131072 ttm.pages_limit=33554432 ttm.page_pool_size=33554432`
  → `mem_info_gtt_total` ≈ 128 GB.
- Usuario en los grupos `render` y `video`.
- Docker + plugin `docker compose` instalados.

Verificación rápida:
```bash
awk '{printf "%.1f GiB\n", $1/1024/1024/1024}' /sys/class/drm/card*/device/mem_info_gtt_total  # ~128
groups | tr ' ' '\n' | grep -E 'render|video'
ls /dev/kfd /dev/dri/renderD*
```

## Uso

```bash
# (solo si vas a usar modelos gated) token de HuggingFace:
cp .env.example .env && nano .env     # pega HUGGING_FACE_HUB_TOKEN

# levantar un modelo:
cd Qwen3.8-27B
docker compose up -d
docker compose logs -f                # espera "Application startup complete"
```

Probar la API (compatible con OpenAI):
```bash
curl http://localhost:8002/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen3-27b","messages":[{"role":"user","content":"Hola"}]}'
```

Detener:
```bash
docker compose down
```

> La caché de modelos es un volumen Docker compartido (`vllm-hf-cache`): cada modelo
> se descarga una sola vez aunque lo uses desde carpetas distintas.

## Notas de la plataforma (gfx1151)

- **Una sola iGPU** → `--tensor-parallel-size 1`.
- **Sin FP8**: RDNA 3.5 no tiene FP8 por hardware; se corre en BF16 (o AWQ/GPTQ).
- Imagen base: [`kyuz0/vllm-therock-gfx1151`](https://github.com/kyuz0/amd-strix-halo-vllm-toolboxes)
  (trae ROCm "TheRock" + vLLM compilados para gfx1151).
- `--gpu-memory-utilization` es el parámetro más delicado en memoria unificada; ajústalo según los logs.
- **Visión multimodal frágil en gfx1151**: las torres de visión de algunos modelos
  usan kernels que fallan en ROCm de consumo (`hipErrorInvalidValue` al perfilar el
  encoder). Si pasa, se desactiva esa modalidad con `--limit-mm-per-prompt` y el
  modelo queda de solo texto.

## Estado multimodal por modelo

| Modelo | Multimodal en la EVO |
|--------|----------------------|
| Qwen3.8-27B | ✅ Texto + **imagen** (su ViT sí corre) |
| **gemma-4-31B** | ⚠️ **Solo texto** — la torre de visión (imagen Y video) crashea en gfx1151; se desactiva con `--limit-mm-per-prompt '{"image":0,"video":0}'` |
| Muse-Glimmer-30B | ❓ Por confirmar |

## Tabla de puertos

| Modelo | Puerto host | `served-model-name` |
|--------|-------------|---------------------|
| Qwen3.8-27B | 8002 | `qwen3-27b` |
| gemma-4-31B | 8003 | `gemma-4-31b` |
| Muse-Glimmer-30B | 8004 | `muse-glimmer-30b` |
| gpt-oss-120b | 8005 | `gpt-oss-120b` |
| Llama-3.3-70B-AWQ | 8006 | `llama-3.3-70b` |
| Nemotron-3.5-Lightning | 8007 | `nemotron-3.5-lightning` |

> La iGPU sirve **un modelo grande a la vez** (comparten la misma memoria). Los puertos distintos permiten alternar sin chocar configuraciones.
