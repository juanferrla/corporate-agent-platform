# Plataforma local de agentes

Esqueleto para probar el recorrido **cliente → LangGraph → LiteLLM → modelo**, con trazas en Langfuse. LangChain y LangGraph se instalan en el contenedor `agent-api`; no son servicios independientes.

## Requisitos

- Docker Engine o Docker Desktop con Docker Compose.
- Una clave de proveedor de modelo compatible con el modelo de ejemplo (OpenAI), o adaptar `litellm/config.yaml` a vuestro proveedor.
- Git, para incorporar la composición oficial de Langfuse.

## 1. Configurar secretos

```bash
cp .env.example .env
```

Edita `.env`: sustituye los valores de ejemplo por secretos aleatorios y añade `OPENAI_API_KEY`. Para este entorno local, deja `LITELLM_API_KEY` igual a `LITELLM_MASTER_KEY`. **No reutilices esa clave maestra en producción**: crea una clave virtual restringida para el agente desde LiteLLM.

## 2. Añadir el Compose oficial de Langfuse

```bash
git clone --depth 1 https://github.com/langfuse/langfuse.git infra/langfuse
```

La composición de Langfuse tiene sus propias dependencias de almacenamiento. La combinamos con `compose.yaml` en un mismo proyecto Docker para que `agent-api` pueda resolver `langfuse-web` por nombre de servicio:

```bash
docker compose -f compose.yaml -f infra/langfuse/docker-compose.yml up --build
```

La primera descarga puede tardar unos minutos. Comprueba los nombres de servicios y las variables de la composición oficial si actualizas Langfuse a una versión posterior.

## 3. Crear las claves de Langfuse

Abre `http://localhost:3000`, crea el usuario inicial, una organización y un proyecto. Copia las claves públicas y secretas del proyecto en `.env` como `LANGFUSE_PUBLIC_KEY` y `LANGFUSE_SECRET_KEY`. Reinicia el agente:

```bash
docker compose -f compose.yaml -f infra/langfuse/docker-compose.yml up -d --force-recreate agent-api
```

## 4. Probar

- LangGraph API: `http://localhost:2024/docs`
- LiteLLM: `http://localhost:4000`
- Langfuse: `http://localhost:3000`

LangGraph sirve el grafo con el identificador `data_platform_agent`. El endpoint `POST /threads` crea un hilo; `POST /threads/{thread_id}/runs/wait` ejecuta el grafo y espera la respuesta. Ejemplo con `curl`:

```bash
THREAD_ID=$(curl -s http://localhost:2024/threads \
  -H 'Content-Type: application/json' \
  -d '{}' | python -c 'import json,sys; print(json.load(sys.stdin)["thread_id"])')

curl -s "http://localhost:2024/threads/${THREAD_ID}/runs/wait" \
  -H 'Content-Type: application/json' \
  -d '{"assistant_id":"data_platform_agent","input":{"messages":[{"role":"user","content":"Resume qué hace un agente de datos."}]}}'
```

## Detener

```bash
docker compose -f compose.yaml -f infra/langfuse/docker-compose.yml down
```

No añadas `-v` salvo que quieras borrar también los volúmenes con los datos.

## Límites de este starter

- `langgraph dev` es para desarrollo y validación; el estado no está configurado como almacenamiento productivo persistente.
- Los puertos están enlazados a `127.0.0.1`, para no exponerlos en la red.
- Compose en una máquina no proporciona alta disponibilidad, SSO, copias de seguridad ni gestión corporativa de secretos.
- El ejemplo envía mensajes al proveedor configurado en LiteLLM. Revisa las políticas de retención y privacidad antes de enviar datos reales; Langfuse puede registrar entradas y salidas.
- Para vuestro ClickHouse 25.8, revisad la compatibilidad con la versión de Langfuse que elijáis. Langfuse v4 requiere ClickHouse 25.12 o posterior; esta composición utiliza la infraestructura incluida en el Compose oficial.

Para producción, trasladaría los contenedores a Kubernetes y configuraría persistencia, autenticación corporativa, límites de acceso, retención y observabilidad antes de abrir el servicio a negocio.
