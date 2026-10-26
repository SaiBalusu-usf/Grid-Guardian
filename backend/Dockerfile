FROM python:3.13-slim
WORKDIR /app
# Copy backend as a package so "from backend.x import y" works
COPY . ./backend/
RUN python backend/build_adk_compat.py \
    && pip install --no-cache-dir --require-hashes -r backend/requirements.lock \
    && pip check
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
