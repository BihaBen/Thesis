<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { summaryStore } from '$lib/stores/summaryStore';

  let summary: string = "";


type Milestone = {
  id: number;
  title: string;
  completed: boolean;
};
let milestones: Milestone[] = [];

async function fetchMilestones() {
  try {
      const response = await fetch("http://localhost:8000/milestones");
      if (response.ok) {
          milestones = await response.json();
      } else {
          console.error("Hiba a mérföldkövek lekérdezésekor:", response.status);
      }
  } catch (error) {
      console.error("API hiba:", error);
  }
}


async function processFiles() {
  try {

    const response = await fetch("http://localhost:8000/api/createSummary", {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text: "Ez egy példa input szöveg" })
    });

    if (!response.ok) {
      console.error("Hiba a fájlok feldolgozása során:", response.status);
    } else {
      const data = await response.json();


      if (data && data.final_summary) {
        summaryStore.set(data.final_summary);
        goto('/chatbot');
      } else {
        console.error("Hiba: az összegzés nem érkezett meg a szervertől.");
      }
    }
  } catch (error) {
    console.error("API hiba:", error);
  }
}

onMount(() => {
    fetchMilestones();
    processFiles();
    const interval = setInterval(fetchMilestones, 3000);
    return () => clearInterval(interval);
});


</script>

<style>
:global(body, html) {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: Arial, sans-serif;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100vh;
  background-image: url('/background_upload.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.loading-box {
  background-color: rgba(255, 255, 255, 0.8);
  border: 3px solid #0367ba;
  padding: 30px;
  text-align: center;
  border-radius: 30px;
  width: 560px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  margin-top: 20px;
}

.milestone-list {
  list-style-type: none;
  padding: 0;
  width: 100%;
}

.milestone-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  border-bottom: 1px solid #ddd;
  font-size: 18px;
}

.milestone-item.completed {
  color: green;
  font-weight: bold;
}

.milestone-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.milestone-icon.completed {
  background-color: #4CAF50;
  color: white;
}

.milestone-icon.pending {
  background-color: #ddd;
  color: #555;
}
</style>

<div class="loading-container">
<div class="loading-box">
  <h2>A tartalom-összefoglalás megkezdődött...</h2>
  <ul class="milestone-list">
    {#each milestones as milestone}
      <li class="milestone-item {milestone.completed ? 'completed' : ''}">
        {milestone.title}
        <div class="milestone-icon {milestone.completed ? 'completed' : 'pending'}">
          {#if milestone.completed}
            ✓
          {:else}
            •
          {/if}
        </div>
      </li>
    {/each}
  </ul>
</div>
</div>
