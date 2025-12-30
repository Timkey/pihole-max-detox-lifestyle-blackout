FROM python:3.11-slim

# Install required Python packages
RUN pip install --no-cache-dir \
    requests \
    beautifulsoup4 \
    lxml

# Set working directory
WORKDIR /workspace

# Configure DNS to use external resolvers (not Pi-hole)
# This is set at runtime via docker-compose

# Default command
CMD ["/bin/bash"]
