# Use the Node.js base image
FROM node:18

# Set the working directory inside the container
WORKDIR /app

# Copy and install dependencies
COPY package*.json ./
RUN npm install

# Copy the application files
COPY . .

# Expose the default development server port
EXPOSE 5173

# Start the SvelteKit development server
CMD ["npm", "run", "dev", "--", "--host"]
