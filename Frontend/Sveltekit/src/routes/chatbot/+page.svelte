<script lang="ts">
  import { onMount } from 'svelte';
  import { uploadedFilesStore } from '$lib/stores/uploadedFilesStore';
  import { summaryStore } from '$lib/stores/summaryStore';
  import { marked } from 'marked';
  
  let isSidebarOpen = false;
  let isRecording = false;
  let isVoice = false;
  let inputText = "";
  let isTyping = false;
  let currentBotMessage = "";
  let thinkingMessage = "Hagy gondolkozzak egy kicsit...";
  let recognition: any;
  let uploadedFiles: string[] = [];
  let isAdditionalProcessingEnabled = false;
  let summaryResult=""

  let chatbotStyle: string;
  let isStoreInLocal: boolean;

  uploadedFilesStore.subscribe(value => {
    uploadedFiles = value;
    console.log("A store tartalma a chatbot oldalon:", uploadedFiles);
  });
    
  summaryStore.subscribe((value) => {
    summaryResult = value;
  });

  let messages = [
    { sender: "bot", text: marked.parse(summaryResult)}
  ];

  onMount(async () => {
    const switchValue = localStorage.getItem('additionalProcessingEnabled');
    const switchValue_style = localStorage.getItem('additionalProcessingEnabled');

    if (switchValue) {
      isAdditionalProcessingEnabled = JSON.parse(switchValue);
    }

    if ('speechSynthesis' in window) {
      console.log('A SpeechSynthesis API támogatott!');
    } else {
      console.error('A SpeechSynthesis API nem támogatott ezen a platformon.');
    }

    if ('webkitSpeechRecognition' in window) {
      recognition = new (window as any).webkitSpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'hu-HU';

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        inputText += transcript;
      };

      recognition.onerror = (event: any) => {
        console.error("Beszédfelismerési hiba:", event.error);
      };
    } else {
      console.error("A Web Speech API nem támogatott.");
    }
  });

  function toggleSidebar() {
    isSidebarOpen = !isSidebarOpen;
  }

  function toggleMicrophone() {
    if (isRecording) {
      recognition.stop();
    } else {
      recognition.start();
    }
    isRecording = !isRecording;
  }

  function toggleVoice() {
    if (isVoice) {
      
    } else {
      
    }
    isVoice = !isVoice;
  }

  async function displayTypingEffect(text: string) {
    currentBotMessage = "";
    thinkingMessage = "";

    for (let i = 0; i < text.length; i++) {
      currentBotMessage += text[i];
      await new Promise(resolve => setTimeout(resolve, 50));
    }


    speakText(currentBotMessage);
  }


  function speakText(text: string) {
    if (isVoice) { 
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "hu-HU";
      speechSynthesis.speak(utterance);
    }
  }

  async function sendMessage() {
    if (inputText.trim() === "") return;

    messages = [...messages, { sender: "user", text: inputText }];
    const userMessage = inputText;
    inputText = "";

    isTyping = true;
    thinkingMessage = "Hagy gondolkozzak egy kicsit...";

    try {
        const response = await fetch('http://localhost:8000/askmodel', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: userMessage })
        });

        if (!response.ok) {
            console.error(`Hiba a kérés során: ${response.status}`);
            const errorData = await response.json();
            console.error("Hiba részletei:", errorData);
            messages = [...messages, { sender: "bot", text: "Hiba történt a válasz lekérésekor." }];
            return;
        }

        const data = await response.json();
        const botMessage = data.response;

        await displayTypingEffect(botMessage);

        messages = [...messages, { sender: "bot", text: currentBotMessage }];
    } catch (error) {
        console.error("Hiba történt a válasz lekérésekor:", error);
        messages = [...messages, { sender: "bot", text: "Hiba történt a válasz lekérésekor." }];
    } finally {
        isTyping = false;
        currentBotMessage = "";
    }
  }

  function handleKeyPress(event: KeyboardEvent) {
    if (event.key === "Enter") {
      sendMessage();
    }
  }

  function saveConversation() {
  const conversationData = messages.map((message) => ({
    sender: message.sender,
    text: message.text,
  }));

  const jsonContent = JSON.stringify(conversationData, null, 2);

  const blob = new Blob([jsonContent], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'conversation.json';
  a.click();
  URL.revokeObjectURL(url);
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

  .chatbot-container {
    width: 100%;
    height: 100%;
    display: flex;
    background-color: #f5f5f5;
    transition: all 0.3s ease;
    overflow-x: hidden;
  }

  .sidebar {
    background-color: #0078d7;
    color: white;
    width: 250px;
    height: 100vh;
    border-right: 2px solid white;
    display: flex;
    flex-direction: column;
    padding: 20px;
    position: fixed;
    top: 0;
    left: 0;
    overflow: hidden;
    transition: transform 0.3s ease;
    transform: translateX(-100%);
  }

  .sidebar.open {
    transform: translateX(0);
  }

  .file-list {
  padding: 0;
  margin: 0;
  list-style-type: none;
}

.file-item {
  word-wrap: break-word;
  overflow-wrap: anywhere;
  max-width: 100%;
  margin-bottom: 0px;
  padding: 0px 50px 0px 0px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

  .toggle-sidebar-button {
    position: absolute;
    top: 20px;
    left: 20px;
    background-color: #0078d7;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    z-index: 2;
  }

  .main-content {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    margin-left: 0;
    transition: margin-left 0.3s ease;
    z-index: 1;
    background-color: #f5f5f5;
    overflow-x: hidden;
  }

  .main-content.shifted {
    margin-left: 250px;
  }

  .chatbot-header {
    width: 100%;
    background-color: #0078d7;
    color: white;
    padding: 20px;
    text-align: center;
    font-size: 24px;
  }

  .chatbot-messages {
    flex-grow: 1;
    width: 100%;
    padding: 20px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    box-sizing: border-box;
  }

  .message {
    max-width: 70%;
    margin-bottom: 10px;
    padding: 15px;
    border-radius: 15px;
    word-wrap: break-word;
    box-sizing: border-box;
  }

  .message.bot {
    background-color: #e0e0e0;
    align-self: flex-start;
    font-size: 14px;
    
  }

  .message.user {
    background-color: #0078d7;
    color: white;
    align-self: flex-end;
  }

  .input-wrapper {
    display: flex;
    align-items: center;
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    box-sizing: border-box;
  }

  .chatbot-input-area {
    width: 100%;
    padding: 20px;
    border-top: 1px solid #ddd;
    background-color: #fff;
  }

  .input-field {
    flex-grow: 1;
    padding: 15px;
    border-radius: 20px;
    border: 1px solid #ddd;
    outline: none;
    box-sizing: border-box;
  }

  .send-button {
    background-color: transparent;
    border: none;
    width: 40px;
    height: 40px;
    background-image: url('/send.png');
    background-size: cover;
    background-position: center;
    cursor: pointer;
    margin-left: 10px;
  }

  .microphone-button {
    background-color: transparent;
    border: none;
    width: 40px;
    height: 40px;
    background-image: url('/mic.png');
    background-size: cover;
    background-position: center;
    cursor: pointer;
    margin-left: 10px;
  }

  .voice-button {
    background-color: transparent;
    border: none;
    width: 40px;
    height: 40px;
    background-image: url('/voice_NO.png');
    background-size: cover;
    background-position: center;
    cursor: pointer;
    margin-left: 10px;
  }

  .voice-button.voiceON {
    background-image: url('/voice.png');
  }

  .microphone-button.recording {
    background-image: url('/mic_rec.png');
  }

  .save-button {
  position: absolute;
  top: 20px;
  right: 20px;
  background-color: transparent;
  border: none;
  width: 40px;
  height: 40px;
  background-image: url('/saveConversation.png');
  background-size: cover;
  background-position: center;
  cursor: pointer;
  }
</style>

<div class="chatbot-container">
  <div class="sidebar {isSidebarOpen ? 'open' : ''}">
    <br><br>
    <h3>Feltöltött állományok:</h3>
    
    <ul class="file-list">
      {#each uploadedFiles as fileString}
        <li class="file-item">{fileString}</li>
        <br>
      {/each}
    </ul>
  </div>

  <div class="main-content {isSidebarOpen ? 'shifted' : ''}">
    <div class="chatbot-header">
      Tartalom-összefoglaló MI
      <button class="toggle-sidebar-button" on:click={toggleSidebar}>
        {isSidebarOpen ? 'Menü bezárása' : 'Menü megnyitása'}
      </button>
      <button class="save-button" on:click={saveConversation}></button>
    </div>

    <div class="chatbot-messages">
      {#each messages as message (message.text)}
        <div class="message {message.sender}">{@html message.text}</div>
      {/each}
      {#if isTyping && thinkingMessage}
        <div class="message bot">{thinkingMessage}</div>
      {/if}
      {#if isTyping && !thinkingMessage}
        <div class="message bot">{currentBotMessage}</div>
      {/if}
    </div>

    <div class="chatbot-input-area">
      <div class="input-wrapper">
        <input class="input-field" type="text" placeholder="Írd le, miben tudok segíteni..." bind:value={inputText} on:keypress={handleKeyPress} />
        <button class="send-button" on:click={sendMessage}></button>
        <button class="microphone-button {isRecording ? 'recording' : ''}" on:click={toggleMicrophone}></button>
        <button class="voice-button {isVoice ? 'voiceON' : ''}" on:click={toggleVoice}></button>
      </div>
    </div>
  </div>
</div>

