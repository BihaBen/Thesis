
<script lang="ts">
  import { addUploadedFile, clearUploadedFiles, uploadedFilesStore } from '$lib/stores/uploadedFilesStore';

  let uploadedFiles: File[] = [];
  let isButtonDisabled = true; // Feltöltés gomb legyen kezdetben letiltva
  let isStoreInCloudEnabled = false; // Adatok fel
  let chatbotStyle = "clear"; // Alapértelmezett érték, ami kiválasztja az "Egyetemista" checkboxot

  // Fájl feltöltés kezelése
  function handleFileUpload(event: Event) {
    const target = event.target as HTMLInputElement;
    const files = target.files;

    // Ha van feltöltött fájl, akkor engedélyezzük a gombot
    if (files) {
      uploadedFiles = Array.from(files);
      isButtonDisabled = uploadedFiles.length === 0;
    }
      // Store ürítése, majd fájlok hozzáadása a store-hoz
      clearUploadedFiles();

      uploadedFiles.forEach(file => {
        const fileSize = file.size < 1024
          ? `${file.size} Bytes`
          : file.size < 1024 * 1024
          ? `${(file.size / 1024).toFixed(2)} KB`
          : file.size < 1024 * 1024 * 1024
          ? `${(file.size / (1024 * 1024)).toFixed(2)} MB`
          : `${(file.size / (1024 * 1024 * 1024)).toFixed(2)} GB`;

        const fileString = `${file.name}: (${fileSize})`;

        console.log("Hozzáadott fájl string:", fileString);
        addUploadedFile(fileString);
      });
      console.log("Store tartalma feltöltés után:", $uploadedFilesStore);
  }
  // Checkbox kiválasztásának kezelése
  function handleCheckboxChange(event: Event) {
    const input = event.target as HTMLInputElement;
    chatbotStyle = input.value;
    console.log("Selected option:", chatbotStyle);
  }

  //Backendre visszük a userSettingseket és fájlokat.
  async function SaveAllData() {
    const formData = new FormData();

    // Metaadatok hozzáadása
    formData.append("isStoreInCloudEnabled", String(isStoreInCloudEnabled));
    formData.append("chatbotStyle", chatbotStyle);

    // Fájlok hozzáadása
    uploadedFiles.forEach((file) => {
      formData.append("files", file);
    });

    try {
      // Metaadatok és fájlok elküldése a backendnek
      const response = await fetch('http://localhost:8000/api/saveAllData', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        console.error("Hiba a metaadatok elküldésekor:", response.status);
        return;
      }

      // Átnavigálás a loading oldalra
      window.location.href = "/loading";
    } catch (error) {
      console.error("Hálózati hiba történt:", error);
    }
}

</script>

<style>
    /* A body és html elemek alapvető stílusai */
    :global(body, html) {
    margin: 0; /* Nincs külső margó */
    padding: 0; /* Nincs belső margó */
    height: 100%; /* A teljes ablak magassága */
    font-family: Arial, sans-serif; /* Alapértelmezett betűtípus */
  }

  /* A Svelte gyökérelem magasságának beállítása */
  :global(#svelte) {
    height: 100%; /* A teljes ablak magasságának kitöltése */
  }

  /* Az egész feltöltési konténer középre igazítva, teljes képernyőn */
  .upload-container {
    display: flex;
    flex-direction: column; /* Elemei oszlopirányban rendeződnek */
    align-items: center; /* Vízszintesen középre igazítás */
    height: 100vh; /* A teljes képernyőmagasságot lefedi */
    background-image: url('/background_upload.jpg'); /* Háttérkép */
    background-size: cover; /* A kép a teljes hátteret kitölti */
    background-position: center; /* Kép középre igazítása */
    background-repeat: no-repeat; /* Nem ismétlődik a háttérkép */
  }

  /* A feltöltődoboz stílusai */
  .upload-box {
    background-color: rgba(255, 255, 255, 0.8); /* Átlátszó fehér háttér */
    border: 3px solid #0367ba; /* Kék szegély */
    padding: 30px; /* Belső tér */
    text-align: center; /* Szöveg középre igazítás */
    border-radius: 30px; /* Lekerekített sarkok */
    width: 560px; /* Fix szélesség */
    display: flex;
    flex-direction: column; /* Elemei oszlopirányban rendeződnek */
    justify-content: center; /* Függőleges középre igazítás */
    align-items: center; /* Vízszintes középre igazítás */
    margin-top: 40px; /* Felső margó */
  }

  /* Nagy betűméret és kék szín a fő szöveges címnek */
  .upload-text {
    font-size: 24px; /* Betűméret */
    color: #0078d7; /* Szöveg színe */
    margin-bottom: 20px; /* Alsó margó */
  }

  /* Kisebb betűméret és kék szín a kiegészítő szöveghez */
  .upload-subtext {
    font-size: 15px; /* Betűméret */
    color: #0078d7; /* Szöveg színe */
    margin-bottom: 20px; /* Alsó margó */
  }

  /* Alsó margó a fájlfeltöltési mezőhöz */
  .file-input {
    margin-bottom: 40px; /* Alsó margó */
  }

  /* Feltöltés gomb alapstílusa */
  .next-button {
    background-color: #0078d7; /* Kék háttér */
    color: white; /* Fehér szöveg */
    border: none; /* Nincs szegély */
    padding: 15px 30px; /* Belső tér */
    border-radius: 20px; /* Lekerekített sarkok */
    cursor: pointer; /* Kéz kurzor */
    text-decoration: none; /* Nincs aláhúzás */
    font-size: 16px; /* Betűméret */
  }

  /* Letiltott gomb stílusa */
  .next-button.disabled {
    background-color: #cccccc; /* Szürke háttér */
    cursor: not-allowed; /* Tilos jelzés */
    pointer-events: none; /* Nem lehet kattintani */
  }

  /* Gomb hover effektus, ha nem letiltott */
  .next-button:hover:not(.disabled) {
    background-color: #005bb5; /* Sötétebb kék háttér hover állapotban */
  }

  /* Switch konténer stílusa */
  .switch-container {
    margin-bottom: 20px; /* Alsó margó */
    display: flex;
    align-items: center; /* Vízszintes középre igazítás */
  }

  /* Switch címke stílusa */
  .switch-label {
    margin-left: 10px; /* Bal margó */
    font-size: 16px; /* Betűméret */
    color: #0078d7; /* Szöveg színe */
  }

  /* Switch stílusa */
  .switch-input {
    width: 40px; /* Szélesség */
    height: 20px; /* Magasság */
    appearance: none; /* Alapértelmezett stílus kikapcsolása */
    background-color: #ccc; /* Alap szürke háttér */
    position: relative;
    outline: none; /* Nincs keret */
    border-radius: 20px; /* Lekerekített sarkok */
    cursor: pointer; /* Kéz kurzor */
  }

  /* Bekapcsolt állapotban lévő switch színe */
  .switch-input:checked {
    background-color: #0078d7; /* Kék háttér bekapcsolt állapotban */
  }

  /* Switch kapcsoló gomb stílusa */
  .switch-input:before {
    content: '';
    position: absolute;
    width: 18px; /* Szélesség */
    height: 18px; /* Magasság */
    background-color: white; /* Fehér háttér */
    border-radius: 50%; /* Kör alak */
    transition: 0.3s; /* Sima átmenet */
    left: 1px;
    top: 1px;
  }

  /* Switch kapcsoló gomb pozíciója bekapcsolt állapotban */
  .switch-input:checked:before {
    transform: translateX(20px); /* Elmozdul jobbra */
  }

  /* Checkbox konténer oszlopirányú elrendezéshez */
  .checkbox-container {
    display: flex;
    flex-direction: column; /* Függőleges elrendezés */
  }

  /* Checkbox mező stílusa */
  .checkbox-square {
    width: 300px; /* Szélesség */
    height: 30px; /* Magasság */
    border: 2px solid #0078d7; /* Kék szegély */
    border-radius: 10px; /* Lekerekített sarkok */
    display: flex;
    flex-direction: column; /* Oszlopirányú elrendezés */
    align-items: center; /* Vízszintes középre igazítás */
    justify-content: center; /* Függőleges középre igazítás */
    padding: 20px; /* Belső margó */
    margin-bottom: 20px; /* Alsó margó */
    background-color: #f9f9f98c; /* Áttetsző fehér háttér */
  }

  /* Checkbox cím stílusa */
  .checkbox-title {
    font-size: 20px; /* Betűméret */
    font-weight: bold; /* Félkövér betű */
    color: #0078d7; /* Szöveg színe */
    text-align: center; /* Szöveg középre igazítás */
    margin-bottom: 20px; /* Alsó margó */
  }

  /* Checkboxok elrendezése sorban */
  .checkbox-container {
    display: flex;
    flex-direction: row; /* Sorirányú elrendezés */
    gap: 20px; /* Checkboxok közötti távolság */
  }

  /* Checkbox címkék stílusa */
  .checkbox-container label {
    font-size: 12px; /* Betűméret */
    color: #0078d7; /* Szöveg színe */
    display: flex;
    align-items: center; /* Középre igazítás függőlegesen */
  }

  /* Checkbox input mező margóval */
  .checkbox-container input[type="checkbox"] {
    margin-right: 10px; /* Jobb margó a szöveg előtt */
  }
</style>

<div class="upload-container">
  <div class="upload-box">

    <div class="upload-text">Kérlek tölts fel fájlokat a további kommunikációhoz:</div>
     
    <div class="upload-subtext">Elfogadott formátumok: (.txt, .docx, .pdf, .json, .epub, .png, .jpg, .mp3, .mp4, .zip)</div>
    <!-- Fájl feltöltése -->
    <input type="file" accept=".txt, .docx, .pdf, .json, .epub, .png, .jpg, .mp3, .mp4, .zip" class="file-input" on:change="{handleFileUpload}" multiple />
    
    <!-- Fogalmazási mód -->
    <div class="checkbox-square">
      <div class="checkbox-title">Fogalmazási mód:</div>
      <div class="checkbox-container">
        <label>
          <input type="checkbox" value="exprt" bind:group={chatbotStyle} on:change="{handleCheckboxChange}" />
          Szakértő
        </label>
        <label>
          <input type="checkbox" value="student" bind:group={chatbotStyle} on:change="{handleCheckboxChange}" />
          Egyetemista
        </label>
        <label>
          <input type="checkbox" value="clear" bind:group={chatbotStyle} on:change="{handleCheckboxChange}" />
          Közérthető
        </label>
      </div>
    </div>
   
    <!-- Adatok lokális gépen tartása -->
    <div class="switch-container">
      <input type="checkbox" class="switch-input" bind:checked={isStoreInCloudEnabled} />
      <div class="switch-label">Adatok lokális gépen tartása</div>
    </div>

    <!-- Feltöltés -->
    <button class="next-button {isButtonDisabled ? 'disabled' : ''}" on:click="{SaveAllData}" disabled={isButtonDisabled}>Feltöltés</button>
  </div>
</div>
