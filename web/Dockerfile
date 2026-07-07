FROM node:20-slim

WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .

EXPOSE 3000
# Dev server for the hackathon scaffold (hot reload). Swap to build+start for prod.
CMD ["npm", "run", "dev"]
