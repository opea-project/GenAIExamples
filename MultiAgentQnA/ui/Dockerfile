FROM node:18

# Set the working directory
WORKDIR /app

# Copy package.json
COPY package.json ./

# Install dependencies (this will create package-lock.json if missing)
RUN npm install

# Copy the rest of the application files
COPY . .

# Expose the port the app runs on
EXPOSE 3000

# Command to run the application
CMD ["npm", "run", "dev"]

