<!-- src/routes/categories/add.svelte -->
<script>
    import Navbar from "../../../components/Navbar.svelte";

    import { onMount } from "svelte";
    let categoryName = "";
    let categoryDescription = "";
    let errorMessage = "";

    const addCategory = async () => {
        const categoryData = {
            CategoryName: categoryName,
            Description: categoryDescription,
        };

        try {
            const response = await fetch("http://127.0.0.1:8000/categories/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(categoryData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                errorMessage = errorData.detail
                    ? errorData.detail[0].msg
                    : "Ошибка при добавлении категории";
            } else {
                alert("Категория добавлена!");
                categoryName = "";
                categoryDescription = "";
                errorMessage = "";
            }
        } catch (error) {
            errorMessage = "Ошибка соединения с сервером";
        }
    };
</script>

<Navbar />

<main class="container mx-auto p-4">
    <h1 class="text-3xl font-bold mb-6">Добавить категорию</h1>

    <form on:submit|preventDefault={addCategory} class="space-y-4">
        <div>
            <label for="name" class="block text-sm font-medium text-gray-700"
                >Название категории</label
            >
            <input
                id="name"
                type="text"
                bind:value={categoryName}
                class="input input-bordered w-full"
                required
            />
        </div>

        <div>
            <label
                for="description"
                class="block text-sm font-medium text-gray-700">Описание</label
            >
            <textarea
                id="description"
                bind:value={categoryDescription}
                class="textarea textarea-bordered w-full"
                required
            ></textarea>
        </div>

        <button type="submit" class="btn btn-primary w-full"
            >Добавить категорию</button
        >

        {#if errorMessage}
            <p class="text-red-500 mt-2">{errorMessage}</p>
        {/if}
    </form>
</main>
