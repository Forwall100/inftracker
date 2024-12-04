<script>
  import { createEventDispatcher } from "svelte";

  // Свойства, получаемые из родительского компонента
  export let productName;
  export let productPrice; // LatestPriceWithDiscount
  export let productPriceWithoutDiscount; // LatestPriceWithoutDiscount
  export let priceDate; // LatestPriceDate
  export let productLink;
  export let categoryName;
  export let productID;

  const dispatch = createEventDispatcher();

  // Функция для обработки удаления продукта
  function handleDelete() {
    dispatch("delete", { productID });
  }
</script>

<div class="card shadow-lg p-4 rounded">
  <!-- Название продукта -->
  <h2 class="text-xl font-semibold">{productName}</h2>

  <!-- Отображение цены со скидкой, если доступна -->
  {#if productPrice !== null && productPrice !== undefined}
    <p class="text-green-600 text-lg font-semibold">
      Цена со скидкой: {productPrice} ₽
    </p>
  {/if}

  <!-- Отображение цены без скидки, если доступна -->
  {#if productPriceWithoutDiscount !== null && productPriceWithoutDiscount !== undefined}
    <p class="text-gray-600 text-lg">
      Цена без скидки: {productPriceWithoutDiscount} ₽
    </p>
  {/if}

  <!-- Название категории -->
  <p class="text-gray-600">Категория: {categoryName}</p>

  <!-- Дата последнего обновления цены, если доступна -->
  {#if priceDate}
    <p class="text-sm text-gray-500 mt-1">
      Последнее обновление цены: {priceDate}
    </p>
  {/if}

  <div class="flex mt-4">
    <!-- Ссылка на продукт -->
    <a
      href={productLink}
      target="_blank"
      rel="noopener noreferrer"
      class="btn btn-circle btn-primary mr-4"
    >
      <!-- Иконка ссылки -->
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
        class="size-5"
      >
        <path
          d="M12.232 4.232a2.5 2.5 0 0 1 3.536 3.536l-1.225 1.224a.75.75 0 0 0 1.061 1.06l1.224-1.224a4 4 0 0 0-5.656-5.656l-3 3a4 4 0 0 0 .225 5.865.75.75 0 0 0 .977-1.138 2.5 2.5 0 0 1-.142-3.667l3-3Z"
        />
        <path
          d="M11.603 7.963a.75.75 0 0 0-.977 1.138 2.5 2.5 0 0 1 .142 3.667l-3 3a2.5 2.5 0 0 1-3.536-3.536l1.225-1.224a.75.75 0 0 0-1.061-1.06l-1.224 1.224a4 4 0 1 0 5.656 5.656l3-3a4 4 0 0 0-.225-5.865Z"
        />
      </svg>
    </a>

    <!-- Кнопка удаления продукта -->
    <button on:click={handleDelete} class="btn btn-circle btn-error">
      <!-- Иконка удаления -->
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 20 20"
        fill="currentColor"
        class="size-5"
      >
        <path
          fill-rule="evenodd"
          d="M8.75 1A2.75 2.75 0 0 0 6 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 1 0 .23 1.482l.149-.022.841 10.518A2.75 2.75 0 0 0 7.596 19h4.807a2.75 2.75 0 0 0 2.742-2.53l.841-10.52.149.023a.75.75 0 0 0 .23-1.482A41.03 41.03 0 0 0 14 4.193V3.75A2.75 2.75 0 0 0 11.25 1h-2.5ZM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4ZM8.58 7.72a.75.75 0 0 0-1.5.06l.3 7.5a.75.75 0 1 0 1.5-.06l-.3-7.5Zm4.34.06a.75.75 0 1 0-1.5-.06l-.3 7.5a.75.75 0 1 0 1.5.06l.3-7.5Z"
          clip-rule="evenodd"
        />
      </svg>
    </button>
  </div>
</div>

<style>
  
</style>
