FROM python:2-slim

LABEL maintainer="oliverzscheyge@gmail.com"

# Prevent apt from querying for a keyboard configuration
ENV DEBIAN_FRONTEND noninteractive

# Dependencies to render PDFs
RUN apt-get update && apt-get install -y --no-install-recommends \
# Not using stock Ubuntu wkhtmltopdf, because it does not support --print-media-type
#		wkhtmltopdf \
    wget \
    xauth \
    xvfb \
# for extracting the wkhtmltox-0.12.3_linux-generic-amd64.tar.xz archive
    xz-utils \
# wkhtmltox-0.12.3_linux-generic-amd64.tar.xz archive dependencies
    libx11-dev libxext-dev libxrender-dev libfontconfig1 && \
    rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf with patched Qt supporting --print-media-type option
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.3/wkhtmltox-0.12.3_linux-generic-amd64.tar.xz && \
    tar vxf wkhtmltox-0.12.3_linux-generic-amd64.tar.xz && \
    cp wkhtmltox/bin/wk* /usr/bin/

# Using a "virtual" X server to run wkhtmltopdf:
# https://github.com/JazzCore/python-pdfkit/wiki/Using-wkhtmltopdf-without-X-server
RUN echo '#!/bin/bash\nxvfb-run -a --server-args="-screen 0, 1024x768x24" /usr/bin/wkhtmltopdf -q $*' > /usr/bin/wkhtmltopdf.sh
RUN chmod a+x /usr/bin/wkhtmltopdf.sh
RUN ln -s /usr/bin/wkhtmltopdf.sh /usr/local/bin/wkhtmltopdf

# Order app python dependencies
RUN pip install pdfkit==0.6.1 flask==0.12.2 epages-rest-python==0.9.0

# Copy order app files
COPY static /app/static
COPY templates /app/templates
COPY *.py /app/

# Expose app/HTTP port
EXPOSE 80

# Run app
CMD python /app/order_document_app.py $FLAGS
