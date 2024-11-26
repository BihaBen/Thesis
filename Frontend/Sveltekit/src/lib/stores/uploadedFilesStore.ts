import { writable } from 'svelte/store';

// Ellenőrizzük, hogy a kód a böngészőben fut-e
const isBrowser = typeof window !== 'undefined';

// Olvassuk ki az adatokat a localStorage-ból, ha a böngészőben vagyunk, különben használjunk üres tömböt
const storedFiles = isBrowser ? JSON.parse(localStorage.getItem('uploadedFiles') || '[]') : [];

export const uploadedFilesStore = writable<string[]>(storedFiles);

// Új fájl hozzáadása a store-hoz és mentés a localStorage-ba
export function addUploadedFile(fileString: string) {
  uploadedFilesStore.update(files => {
    const updatedFiles = [...files, fileString];
    if (isBrowser) {
      localStorage.setItem('uploadedFiles', JSON.stringify(updatedFiles));
    }
    return updatedFiles;
  });
}

// A store ürítése és a localStorage törlése
export function clearUploadedFiles() {
  if (isBrowser) {
    localStorage.removeItem('uploadedFiles');
  }
  uploadedFilesStore.set([]);
}
