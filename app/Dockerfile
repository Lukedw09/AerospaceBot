FROM public.ecr.aws/docker/library/python:3.12-slim-bookworm

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter

WORKDIR /var/task
ENV PORT=8080
ENV AWS_LWA_PORT=8080
ENV PYTHONPATH=/var/task
ENV MPLCONFIGDIR=/tmp/mpl
ENV MPLBACKEND=Agg
ENV AEROSPACE_HTTP=1

COPY app/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY app /var/task/app
COPY skills /var/task/skills

CMD ["python", "-m", "app.server"]
