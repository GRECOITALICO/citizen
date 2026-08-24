# Public Citizen runtime image. Built from the frozen wheel.
# Runtime lives in the image. Citizen life lives on the volume.
#
# Do not pip-install Citizen onto the host.

FROM python:3.13-slim-bookworm

ENV CITIZEN_HOME=/citizen \
    CITIZEN_UI_HOST=0.0.0.0 \
    CITIZEN_UI_PORT=3434 \
    CITIZEN_OPEN_BROWSER=0

WORKDIR /opt/citizen-runtime

COPY release/0.4.2.1/conrrad_citizen-0.4.2.1-py3-none-any.whl /tmp/conrrad_citizen-0.4.2.1-py3-none-any.whl
COPY isolation/entrypoint.py /opt/citizen-runtime/entrypoint.py

RUN python -c "import hashlib, pathlib; \
p=pathlib.Path('/tmp/conrrad_citizen-0.4.2.1-py3-none-any.whl'); \
d=hashlib.sha256(p.read_bytes()).hexdigest(); \
assert d=='fe8f06d10219655bd0ebf84a1f8a08c955d65fa22a76316c3887d29fcede51e9', d" \
 && pip install --no-cache-dir /tmp/conrrad_citizen-0.4.2.1-py3-none-any.whl \
 && rm /tmp/conrrad_citizen-0.4.2.1-py3-none-any.whl

VOLUME ["/citizen"]
EXPOSE 3434
ENTRYPOINT ["python", "/opt/citizen-runtime/entrypoint.py"]
