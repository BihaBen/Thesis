
<script lang="ts">
  import { addUploadedFile, clearUploadedFiles, uploadedFilesStore } from '$lib/stores/uploadedFilesStore';

  let uploadedFiles: File[] = [];
  let isButtonDisabled = true;
  let isStoreInLocal = false;
  let chatbotStyle = "clear";

 
  function handleFileUpload(event: Event) {
    const target = event.target as HTMLInputElement;
    const files = target.files;
    if (files) {
      uploadedFiles = Array.from(files);
      isButtonDisabled = uploadedFiles.length === 0;
    }
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

  function handleCheckboxChange(event: Event) {
    const input = event.target as HTMLInputElement;
    chatbotStyle = input.value;
    console.log("Selected option:", chatbotStyle);
  }


  async function SaveAllData() {
    const formData = new FormData();
    formData.append("isStoreInLocal", String(isStoreInLocal));
    formData.append("chatbotStyle", chatbotStyle);
    uploadedFiles.forEach((file) => {formData.append("files", file);});
    try {
        const response = await fetch('http://localhost:8000/api/saveAllData', {
          method: 'POST',
          body: formData,
        });
        if (!response.ok) {
          console.error("Hiba a metaadatok elküldésekor:", response.status);
          return;
        }
        window.location.href = "/loading";
      } catch (error) {
      console.error("Hálózati hiba történt:", error);
    }
 }

</script>

<style>

    :global(body, html) {
    margin: 0;
    padding: 0;
    height: 100%;
    font-family: Arial, sans-serif;
  }

  
  :global(#svelte) {
    height: 100%;
  }

  
  .upload-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 100vh;
    background-image: url('/background_upload.jpg');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
  }


  .upload-box {
    background-color: rgba(255, 255, 255, 0.8);
    border: 3px solid #0367ba;
    padding: 30px; 
    text-align: center;
    border-radius: 30px;
    width: 560px;
    display: flex;/* Belső tér */
    flex-direction: column;
    justify-content: center;
    align-items: center;
    margin-top: 40px;
  }

  
  .upload-text {
    font-size: 24px;
    color: #0078d7;
    margin-bottom: 20px;
  }

  
  .upload-subtext {
    font-size: 15px;
    color: #0078d7;
    margin-bottom: 20px;
  }

 
  .file-input {
    margin-bottom: 40px;
  }


  .next-button {
    background-color: #0078d7;
    color: white;
    border: none;
    padding: 15px 30px;
    border-radius: 20px;
    cursor: pointer;
    text-decoration: none;
    font-size: 16px;
  }

  .next-button.disabled {
    background-color: #cccccc;
    cursor: not-allowed;
    pointer-events: none;
  }


  .next-button:hover:not(.disabled) {
    background-color: #005bb5; 
  }


  .switch-container {
    margin-bottom: 20px;
    display: flex;
    align-items: center;
  }


  .switch-label {
    margin-left: 10px;
    font-size: 16px;
    color: #0078d7;
  }


  .switch-input {
    width: 40px;
    height: 20px;
    appearance: none;
    background-color: #ccc;
    position: relative;
    outline: none;
    border-radius: 20px;
    cursor: pointer;
  }


  .switch-input:checked {
    background-color: #0078d7;
  }


  .switch-input:before {
    content: '';
    position: absolute;
    width: 18px;
    height: 18px;
    background-color: white;
    border-radius: 50%;
    transition: 0.3s;
    left: 1px;
    top: 1px;
  }

  .switch-input:checked:before {
    transform: translateX(20px);
  }


  .checkbox-container {
    display: flex;
    flex-direction: column;
  }


  .checkbox-square {
    width: 300px;
    height: 30px;
    border: 2px solid #0078d7;
    border-radius: 10px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20px;
    margin-bottom: 20px;
    background-color: #f9f9f98c;
  }

  .checkbox-title {
    font-size: 20px;
    font-weight: bold;
    color: #0078d7;
    text-align: center;
    margin-bottom: 20px;
  }


  .checkbox-container {
    display: flex;
    flex-direction: row;
    gap: 20px;
  }


  .checkbox-container label {
    font-size: 12px;
    color: #0078d7;
    display: flex;
    align-items: center;
  }


  .checkbox-container input[type="checkbox"] {
    margin-right: 10px;
  }
</style>

<div class="upload-container">
  <div class="upload-box">

    <div class="upload-text">Kérlek tölts fel fájlokat a további kommunikációhoz:</div>
     
    <div class="upload-subtext">Elfogadott formátumok: (.txt, .docx, .pdf, .json, .epub, .png, .jpg, .mp3, .mp4, .zip)</div>

    <input type="file" accept=".txt, .docx, .pdf, .json, .epub, .png, .jpg, .mp3, .mp4, .zip" class="file-input" on:change="{handleFileUpload}" multiple />
    

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

    <div class="switch-container">
      <input type="checkbox" class="switch-input" bind:checked={isStoreInLocal} />
      <div class="switch-label">Adatok lokális gépen tartása</div>
    </div>

    <button class="next-button {isButtonDisabled ? 'disabled' : ''}" on:click="{SaveAllData}" disabled={isButtonDisabled}>Feltöltés</button>
  </div>
</div>
