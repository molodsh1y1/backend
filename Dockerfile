FROM python:3.12

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY ./app /app
RUN mkdir -p /static

RUN addgroup --gid 1000 unprivileged && \
    adduser --uid 1000 --gid 1000 unprivileged && \
    chown -R unprivileged:unprivileged /app /static

USER unprivileged:unprivileged

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["sleep", "infinity"]

EXPOSE 8000