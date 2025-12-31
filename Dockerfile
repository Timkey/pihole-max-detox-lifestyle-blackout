FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Install required Python packages
RUN pip install --no-cache-dir \
    requests \
    beautifulsoup4 \
    lxml \
    playwright

# Install Playwright browsers (chromium only for speed/size)
RUN playwright install chromium --with-deps

# Set working directory
WORKDIR /workspace

# Configure DNS to use external resolvers (not Pi-hole)
# This is set at runtime via docker-compose

# Default command
CMD ["/bin/bash"]
