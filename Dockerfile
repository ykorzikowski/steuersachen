FROM harbor.swokiz.dev/hub-proxy/library/python:3.12-slim

COPY --chown=1000:1000 requirements.txt /app/requirements.txt
COPY --chown=1000:1000 run.py /app/run.py
COPY --chown=1000:1000 .streamlit /app/.streamlit
COPY --chown=1000:1000 modules /app/modules
COPY --chown=1000:1000 config /app/config

WORKDIR /app
ENV PYTHONPATH=/app
ENV STREAMLIT_CONFIG_DIR=/app/.streamlit

RUN useradd -m -u 1000 app \
 && chown -R 1000:1000 /app \
 && python3 -m pip install -r /app/requirements.txt

USER 1000:1000

ENTRYPOINT ["python3", "-m", "streamlit", "run", "--server.address", "0.0.0.0", "run.py"]

EXPOSE 8501/tcp
