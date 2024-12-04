<script>
    import { onMount } from "svelte";
    import CategoryCard from "../../components/CategoryCard.svelte";
    import Navbar from "../../components/Navbar.svelte";

    let categories = [];
    let errorMessage = "";
    let isLoading = true;

    // Функция для получения категорий с API
    const getCategories = async () => {
        try {
            const response = await fetch("http://localhost:8000/categories/");
            if (response.ok) {
                const data = await response.json();
                categories = data;
            } else {
                errorMessage = "Не удалось загрузить категории";
            }
        } catch (error) {
            errorMessage = "Ошибка соединения с сервером";
        } finally {
            isLoading = false;
        }
    };

    // Функция для удаления категории
    const deleteCategory = async (categoryID) => {
        // Подтверждение удаления
        const confirmed = confirm('Вы уверены, что хотите удалить эту категорию?');
        if (!confirmed) return;

        try {
            const response = await fetch(`http://localhost:8000/categories/${categoryID}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                // Удаляем категорию из списка
                categories = categories.filter(category => category.CategoryID !== categoryID);
            } else {
                const errorData = await response.json();
                alert(`Ошибка при удалении категории: ${errorData.detail}`);
            }
        } catch (error) {
            alert('Ошибка соединения с сервером при удалении категории');
        }
    };

    // Загружаем данные при монтировании компонента
    onMount(() => {
        getCategories();
    });
</script>

<Navbar />
<main class="container mx-auto p-4">
    <div class="flex items-baseline">
        <h1 class="text-3xl font-bold mb-6">Категории товаров</h1>
        <a href="/categories/add" class="btn ml-10">+ Добавить</a>
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
        {#if categories.length > 0}
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {#each categories as category}
                    <CategoryCard
                        categoryName={category.CategoryName}
                        description={category.Description}
                        categoryID={category.CategoryID} 
                        on:delete={event => deleteCategory(event.detail.categoryID)} 
                    />
                {/each}
            </div>
        {:else}
            <div class="text-center text-gray-500">
                Нет категорий для отображения.
            </div>
        {/if}
    {/if}
</main>

<style>
    /* Добавьте здесь ваши стили, если необходимо */
</style>
