FROM python:2-slim

LABEL maintainer="oliverzscheyge@gmail.com"

# Dependencies to render PDFs
RUN apt-get update && apt-get install -y --no-install-recommends \
		wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Order app python dependencies
RUN pip install pdfkit==0.6.1 flask==0.12.2 epages-rest-python==0.3.0

# Copy order app files
COPY static /orders/static
COPY templates /orders/templates
COPY order_document_app.py /orders/

# Expose app/HTTP port
EXPOSE 80

# Run app
CMD ["python", "/orders/order_document_app.py"]
