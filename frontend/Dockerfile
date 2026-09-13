FROM node:20-alpine

WORKDIR /app

# Copy package management files first to leverage Docker layer caching
COPY package*.json ./

RUN npm install

# Copy the rest of the Next.js application files
COPY . .

# Build the Next.js production build
# RUN npm run build

EXPOSE 3000

# Start the Next.js production server (or "npm", "run", "dev" for dynamic local development)
CMD ["npm", "run", "dev"]