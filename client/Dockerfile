FROM node:20.11.0

WORKDIR /app

COPY package.json pnpm-lock.yaml /app/

RUN npm install -g pnpm

RUN pnpm install

COPY . .

EXPOSE 5173

CMD ["pnpm", "dev", "--host"]