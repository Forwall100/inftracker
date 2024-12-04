<script>
    import { onMount } from "svelte";
    import ProductCard from "../../components/ProductCard.svelte";
    import Navbar from "../../components/Navbar.svelte";

    // Переменные состояния
    let categories = [];
    let products = [];
    let filteredProducts = [];
    let selectedCategory = "";
    let errorMessage = "";
    let isLoading = true;

    // Функция для получения данных с API
    async function fetchData() {
        try {
            // Параллельный запрос категорий и продуктов
            const [categoriesRes, productsRes] = await Promise.all([
                fetch("http://localhost:8000/categories/"),
                fetch("http://localhost:8000/products/"),
            ]);

            // Проверка успешности запросов
            if (!categoriesRes.ok) {
                throw new Error("Не удалось загрузить категории");
            }

            if (!productsRes.ok) {
                throw new Error("Не удалось загрузить продукты");
            }

            // Парсинг данных
            const categoriesData = await categoriesRes.json();
            const productsData = await productsRes.json();

            categories = categoriesData;
            // Добавляем название категории к каждому продукту
            products = productsData.map((product) => ({
                ...product,
                CategoryName:
                    categories.find(
                        (cat) => cat.CategoryID === product.CategoryID,
                    )?.CategoryName || "Неизвестно",
            }));

            // Инициализация отображаемых продуктов
            filteredProducts = products;
        } catch (error) {
            errorMessage = error.message;
        } finally {
            isLoading = false;
        }
    }

    // Функция для удаления продукта
    async function deleteProduct(productID) {
        // Подтверждение удаления
        const confirmed = confirm(
            "Вы уверены, что хотите удалить этот продукт?",
        );
        if (!confirmed) return;

        try {
            const response = await fetch(
                `http://localhost:8000/products/${productID}`,
                {
                    method: "DELETE",
                },
            );

            if (response.ok) {
                // Удаляем продукт из списка
                products = products.filter(
                    (product) => product.ProductID !== productID,
                );
                // Обновляем отфильтрованные продукты
                filteredProducts = selectedCategory
                    ? products.filter(
                          (product) =>
                              product.CategoryID === parseInt(selectedCategory),
                      )
                    : products;
            } else {
                const errorData = await response.json();
                alert(`Ошибка при удалении продукта: ${errorData.detail}`);
            }
        } catch (error) {
            alert("Ошибка соединения с сервером при удалении продукта");
        }
    }

    // Загрузка данных при монтировании компонента
    onMount(() => {
        fetchData();
    });

    // Реактивное обновление фильтрованных продуктов при изменении selectedCategory или products
    $: filteredProducts = selectedCategory
        ? products.filter(
              (product) => product.CategoryID === parseInt(selectedCategory),
          )
        : products;
</script>

<Navbar />

<main class="container mx-auto p-4">
    <div class="flex items-baseline mb-6">
        <h1 class="text-3xl font-bold mr-4">Товары</h1>
        <a href="/products/add" class="btn">+ Добавить</a>
    </div>

    {#if errorMessage}
        <div class="alert alert-error mb-4">
            <span>{errorMessage}</span>
        </div>
    {/if}

    {#if isLoading}
        <div class="flex justify-center items-center">
            <span class="loading loading-spinner text-primary"></span>
            <span class="ml-2">Загрузка...</span>
        </div>
    {:else}
        <div class="mb-4">
            <label for="categoryFilter" class="block text-lg mb-2"
                >Выберите категорию</label
            >
            <select
                id="categoryFilter"
                bind:value={selectedCategory}
                class="select select-bordered w-full max-w-xs"
            >
                <option value="">Все</option>
                <!-- Используем пустую строку вместо null -->
                {#each categories as category}
                    <option value={category.CategoryID}
                        >{category.CategoryName}</option
                    >
                {/each}
            </select>
        </div>

        {#if filteredProducts.length > 0}
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {#each filteredProducts as product}
                    <ProductCard
                        productName={product.ProductName}
                        productPrice={product.LatestPriceWithDiscount}
                        productPriceWithoutDiscount={product.LatestPriceWithoutDiscount}
                        priceDate={product.LatestPriceDate}
                        productLink={product.ProductLink}
                        categoryName={product.CategoryName}
                        productID={product.ProductID}
                        on:delete={(event) =>
                            deleteProduct(event.detail.productID)}
                    />
                {/each}
            </div>
        {:else}
            <div class="text-center text-gray-500">
                Нет продуктов для отображения.
            </div>
        {/if}
    {/if}
</main>

<style>
    /* Добавьте здесь ваши стили, если необходимо */
</style>
