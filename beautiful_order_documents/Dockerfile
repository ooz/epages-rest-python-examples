FROM python:2-slim

LABEL maintainer="oliverzscheyge@gmail.com"

# Prevent apt from querying for a keyboard configuration
ENV DEBIAN_FRONTEND noninteractive

# Dependencies to render PDFs
RUN apt-get update && apt-get install -y --no-install-recommends \
		wkhtmltopdf \
    xauth \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Using a "virtual" X server to run wkhtmltopdf:
# https://github.com/JazzCore/python-pdfkit/wiki/Using-wkhtmltopdf-without-X-server
RUN echo '#!/bin/bash\nxvfb-run -a --server-args="-screen 0, 1024x768x24" /usr/bin/wkhtmltopdf -q $*' > /usr/bin/wkhtmltopdf.sh
RUN chmod a+x /usr/bin/wkhtmltopdf.sh
RUN ln -s /usr/bin/wkhtmltopdf.sh /usr/local/bin/wkhtmltopdf

# Order app python dependencies
RUN pip install pdfkit==0.6.1 flask==0.12.2 epages-rest-python==0.7.0

# Copy order app files
COPY static /app/static
COPY templates /app/templates
COPY *.py /app/

# Expose app/HTTP port
EXPOSE 80

# Run app
CMD python /app/order_document_app.py $FLAGS
