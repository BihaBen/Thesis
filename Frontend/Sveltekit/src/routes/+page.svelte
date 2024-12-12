<script>
  import { onMount } from 'svelte';

  let message = "Sikeres";

  // Fetch API from FastAPI backend
  onMount(async () => {
      try {
          const res = await fetch("http://localhost:8000/status");
          if (!res.ok) {
              throw new Error(`Hiba: ${res.status} - ${res.statusText}`);
          }
          window.location.href = "/upload";
          const data = await res.json();
          message = data.message;
      } catch (err) {
          console.error(err);
          message = "Hiba történt az API hívás során.";
      }
  });
</script>

<style>
  main {
    background-color: rgb(6, 202, 237);
    color: white;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
  }
</style>

<main>
  <h1>{message}</h1>
</main>