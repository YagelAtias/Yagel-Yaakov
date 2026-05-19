# We use a Node.js image to build the React application.
FROM node:20-alpine AS build

# Set the working directory to /app.
WORKDIR /app

# Copy package.json and package-lock.json to install dependencies.
COPY package*.json ./

# Install the project dependencies.
RUN npm install

# Copy the remaining frontend source code.
COPY . .

# Build the Vite React app for production. The output will be in the 'dist' folder.
RUN npm run build

# We use a lightweight Nginx image to serve the compiled static files.
FROM nginx:alpine

# Copy our custom Nginx configuration to handle client-side routing.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built application files from the previous build stage.
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 8080 to match Google Cloud Run default expectations.
EXPOSE 8080

# Start the Nginx server in the foreground.
CMD ["nginx", "-g", "daemon off;"]
