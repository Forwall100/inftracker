<script>
  import { createEventDispatcher } from 'svelte';
  export let categoryName;
  export let description;
  export let categoryID; // Добавляем ID категории

  const dispatch = createEventDispatcher();

  function handleDelete() {
      dispatch('delete', { categoryID });
  }
</script>

<div class="card shadow-lg p-4 rounded">
  <h2 class="text-xl font-semibold">{categoryName}</h2>
  <p class="text-gray-600">{description}</p>
  <button on:click={handleDelete} class="btn btn-outline btn-error mt-4">Удалить</button>
</div>

<style>
  /* Ваши стили здесь */
</style>
