# build stage ------------------------------
FROM ghcr.io/astral-sh/uv:debian AS build
RUN mkdir -p /app/src

# copy project files
COPY src /app/src
COPY README.md /app/README.md
COPY LICENSE /app/LICENSE
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock

# setup dependencies
WORKDIR /app
RUN uv sync --all-groups
RUN uv build
# end build stage --------------------------

# runtime stage ----------------------------
FROM build AS runtime
VOLUME /aws
ENV AWS_CONFIG_FILE=/aws/config
EXPOSE 8000
ENTRYPOINT [".venv/bin/python", "-m", "chainlit", "run", "src/ui/app.py", "--host", "0.0.0.0", "--port", "8000"]
# end runtime stage ------------------------