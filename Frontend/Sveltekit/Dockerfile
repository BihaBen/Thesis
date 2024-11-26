# 1. lépés: Alap képként használj egy Node.js képet
FROM node:18 AS builder

# 2. lépés: Állítsd be a munkakönyvtárat
WORKDIR /app

# 3. lépés: Másold a package.json és package-lock.json fájlokat
COPY package*.json ./

# 4. lépés: Telepítsd a függőségeket
RUN npm install

# 5. lépés: Másold a teljes alkalmazást
COPY . .

# 6. lépés: Készítsd el az alkalmazást
RUN npm run build

# 7. lépés: A végső képhez használd a második lépést
FROM node:18

# 8. lépés: Állítsd be a munkakönyvtárat
WORKDIR /app

# 9. lépés: Másold a buildelt alkalmazást
COPY --from=builder /app/build ./build

# 10. lépés: Telepítsd a szükséges csomagokat a futtatáshoz
RUN npm install --only=production

# 11. lépés: Állítsd be a környezeti változót
ENV PORT=3000

# 12. lépés: Tedd elérhetővé a portot
EXPOSE 3000

# 13. lépés: Indítsd el az alkalmazást
CMD ["npm", "start"]
