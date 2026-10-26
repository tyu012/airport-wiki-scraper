# Based on https://docs.astral.sh/uv/guides/integration/docker/

FROM python:3.14-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /uvx /bin/

# Copy the project into the image
COPY . /app

# Disable development dependencies
ENV UV_NO_DEV=1

# Disable buffering
ENV PYTHONUNBUFFERED=1

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked

EXPOSE 5432

CMD [ "uv", "run", "airport-wiki-scraper", "-frl" ]
