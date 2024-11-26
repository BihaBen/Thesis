# Base image
FROM node:18-slim

# Set the working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application files
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 5173

# Start the application
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
