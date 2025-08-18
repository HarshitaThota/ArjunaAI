# frontend/Dockerfile
FROM node:18-alpine
WORKDIR /app

COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --prefer-offline --no-audit; else npm install --no-audit; fi

COPY . .
RUN npm run build

EXPOSE 3000
ENV PORT=3000
CMD ["npm","run","start"]  
