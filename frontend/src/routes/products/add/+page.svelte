<!-- src/routes/products/add.svelte -->
<script>
    import Navbar from "../../../components/Navbar.svelte";
    import { onMount } from "svelte";

    let productName = "";
    let productCategory = "";
    let productLink = "";
    let errorMessage = "";
    let categories = [];
    let linkErrorMessage = "";

    // Функция для получения категорий
    const getCategories = async () => {
        try {
            const response = await fetch("http://127.0.0.1:8000/categories/");
            if (response.ok) {
                const data = await response.json();
                categories = data;
            } else {
                errorMessage = "Не удалось загрузить категории";
            }
        } catch (error) {
            errorMessage = "Ошибка соединения с сервером";
        }
    };

    // Валидация ссылки
    const validateLink = (link) => {
        const urlPattern = /^(https?|ftp):\/\/[^\s/$.?#].[^\s]*$/i;
        return urlPattern.test(link);
    };

    // Отправка формы на сервер
    const addProduct = async () => {
        // Сброс сообщений об ошибках
        errorMessage = "";
        linkErrorMessage = "";

        if (!validateLink(productLink)) {
            linkErrorMessage = "Введите правильный URL";
            return;
        }

        const productData = {
            ProductName: productName,
            CategoryID: parseInt(productCategory), // предполагаем, что CategoryID — это целое число
            ProductLink: productLink,
        };

        try {
            const response = await fetch("http://127.0.0.1:8000/products/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(productData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                // Изменение здесь: предполагаем, что detail — это строка
                errorMessage = errorData.detail
                    ? errorData.detail
                    : "Ошибка при добавлении товара";
            } else {
                alert("Товар добавлен!");
                // Сброс полей формы
                productName = "";
                productCategory = "";
                productLink = "";
                linkErrorMessage = "";
                errorMessage = "";
            }
        } catch (error) {
            errorMessage = "Ошибка соединения с сервером";
        }
    };

    // Загружаем категории при монтировании компонента
    onMount(() => {
        getCategories();
    });
</script>

<Navbar />

<main class="container mx-auto p-4">
    <h1 class="text-3xl font-bold mb-6">Добавить товар</h1>

    <form on:submit|preventDefault={addProduct} class="space-y-4">
        <div>
            <label for="name" class="block text-sm font-medium text-gray-700"
                >Название товара</label
            >
            <input
                id="name"
                type="text"
                bind:value={productName}
                class="input input-bordered w-full"
                required
            />
        </div>

        <div>
            <label
                for="category"
                class="block text-sm font-medium text-gray-700">Категория</label
            >
            <select
                id="category"
                bind:value={productCategory}
                class="select select-bordered w-full"
                required
            >
                <option value="" disabled selected>Выберите категорию</option>
                {#each categories as category}
                    <option value={category.CategoryID}
                        >{category.CategoryName}</option
                    >
                {/each}
            </select>
        </div>

        <div>
            <label for="link" class="block text-sm font-medium text-gray-700"
                >Ссылка на товар</label
            >
            <input
                id="link"
                type="text"
                bind:value={productLink}
                class="input input-bordered w-full"
                required
            />
            {#if linkErrorMessage}
                <p class="text-red-500 mt-2">{linkErrorMessage}</p>
            {/if}
        </div>

        <button type="submit" class="btn btn-primary w-full"
            >Добавить товар</button
        >

        {#if errorMessage}
            <p class="text-red-500 mt-2">{errorMessage}</p>
        {/if}
    </form>
</main>

<style>
    /* Ваши стили здесь */
</style>

