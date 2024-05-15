# Use node 20.11.1 as the base image
FROM node:20.11.1

# Update package manager and install Git
RUN apt-get update -y && apt-get install -y git

# Clone the front-end code repository
RUN git clone https://github.com/opea-project/GenAIExamples.git /home/user/GenAIExamples

# Set the working directory
WORKDIR /home/user/GenAIExamples/ChatQnA/ui/svelte

# Install front-end dependencies
RUN npm install

# Expose the port of the front-end application
EXPOSE 5173

# Run the front-end application
CMD ["npm", "run", "dev"]
