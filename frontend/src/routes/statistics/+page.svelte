<script>
    import { onMount } from "svelte";
    import Navbar from "../../components/Navbar.svelte";

    let inflationAllTime = null;
    let inflationPeriod = null;
    let inflationCategory = null;
    let startDate = "";
    let endDate = "";
    let selectedCategory = "";
    let categories = [];
    let periodInflationError = "";
    let categoryInflationError = "";
    let allTimeInflationError = "";

    // Функция для получения инфляции за все время
    async function getInflationAllTime() {
        try {
            const response = await fetch(
                "http://localhost:8000/inflation/overall/all_time",
            );
            if (!response.ok) {
                throw new Error(
                    "Ошибка при получении инфляции за все время наблюдений",
                );
            }
            const data = await response.json();
            inflationAllTime = data.inflation_percentage;
        } catch (error) {
            allTimeInflationError = error.message;
        }
    }

    // Функция для получения инфляции за заданный период
    async function getInflationForPeriod() {
        if (!startDate || !endDate) {
            periodInflationError = "Пожалуйста, укажите оба периода";
            inflationPeriod = null;
            return;
        }

        try {
            const response = await fetch(
                `http://localhost:8000/inflation/overall?start_date=${startDate}&end_date=${endDate}`,
            );
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(
                    errorData.detail ||
                        "Ошибка при получении инфляции за период",
                );
            }
            const data = await response.json();
            inflationPeriod = data.inflation_percentage;
            periodInflationError = ""; // Сброс ошибки
        } catch (error) {
            periodInflationError = error.message;
            inflationPeriod = null; // Сброс результата
        }
    }

    // Функция для получения инфляции по категории
    async function getInflationForCategory() {
        if (!selectedCategory || !startDate || !endDate) {
            categoryInflationError =
                "Пожалуйста, выберите категорию и укажите оба периода";
            inflationCategory = null;
            return;
        }

        try {
            const response = await fetch(
                `http://localhost:8000/inflation/category/${selectedCategory}?start_date=${startDate}&end_date=${endDate}`,
            );
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(
                    errorData.detail ||
                        "Ошибка при получении инфляции по категории",
                );
            }
            const data = await response.json();
            inflationCategory = data.inflation_percentage;
            categoryInflationError = ""; // Сброс ошибки
        } catch (error) {
            categoryInflationError = error.message;
            inflationCategory = null; // Сброс результата
        }
    }

    // Функция для получения категорий
    async function getCategories() {
        try {
            const response = await fetch("http://localhost:8000/categories/");
            if (!response.ok) {
                throw new Error("Не удалось загрузить категории");
            }
            const data = await response.json();
            categories = data;
        } catch (error) {
            categoryInflationError = error.message;
        }
    }

    // Загружаем инфляцию за все время и категории при монтировании компонента
    onMount(() => {
        getInflationAllTime();
        getCategories();
    });
</script>

<Navbar />

<main class="container mx-auto p-4">
    <h1 class="text-3xl font-bold mb-6">Статистика изменения цен</h1>

    <!-- Инфляция за все время -->
    <div class="mb-6">
        <h2 class="text-xl font-semibold mb-2">
            Инфляция за все время наблюдений
        </h2>
        {#if allTimeInflationError}
            <p class="text-red-500">{allTimeInflationError}</p>
        {:else if inflationAllTime !== null}
            <table class="table table-zebra table-sm w-full">
                <thead>
                    <tr>
                        <th class="p-2">Период</th>
                        <th class="p-2">Инфляция (%)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="p-2">Все время</td>
                        <td class="p-2">{inflationAllTime.toFixed(2)}</td>
                    </tr>
                </tbody>
            </table>
        {/if}
    </div>

    <div class="flex justify-start gap-10">
        <!-- Инфляция за период -->
        <div class="mb-6">
            <h2 class="text-xl font-semibold mb-2">Инфляция за период</h2>
            <div class="flex">
                <div class="flex flex-col mb-4 mr-4">
                    <label for="startDate" class="text-lg">Дата начала:</label>
                    <input
                        type="date"
                        id="startDate"
                        bind:value={startDate}
                        class="bg-base-100 border p-2 rounded-md"
                    />
                </div>
                <div class="flex flex-col mb-4">
                    <label for="endDate" class="text-lg">Дата окончания:</label>
                    <input
                        type="date"
                        id="endDate"
                        bind:value={endDate}
                        class="bg-base-100 border p-2 rounded-md"
                    />
                </div>
            </div>
            <button
                on:click={getInflationForPeriod}
                class="btn btn-primary p-2 rounded-md"
            >
                Рассчитать инфляцию за период
            </button>

            {#if periodInflationError}
                <p class="text-red-500 mt-4">{periodInflationError}</p>
            {:else if inflationPeriod !== null}
                <table class="table table-zebra table-sm w-full mt-4">
                    <thead>
                        <tr>
                            <th class="p-2">Период</th>
                            <th class="p-2">Инфляция (%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="p-2">
                                {startDate} - {endDate}
                            </td>
                            <td class="p-2">{inflationPeriod.toFixed(2)}</td>
                        </tr>
                    </tbody>
                </table>
            {/if}
        </div>

        <!-- Инфляция по категории -->
        <div class="mb-6">
            <h2 class="text-xl font-semibold mb-2">Инфляция по категории</h2>
            <div class="flex flex-col mb-4">
                <label for="category" class="text-lg">Выберите категорию:</label
                >
                <select
                    id="category"
                    bind:value={selectedCategory}
                    class="select select-bordered w-full"
                >
                    <option value="" disabled selected
                        >Выберите категорию</option
                    >
                    {#each categories as category}
                        <option value={category.CategoryID}
                            >{category.CategoryName}</option
                        >
                    {/each}
                </select>
            </div>
            <div class="flex">
                <div class="flex flex-col mb-4 mr-4">
                    <label for="startDateCategory" class="text-lg"
                        >Дата начала:</label
                    >
                    <input
                        type="date"
                        id="startDateCategory"
                        bind:value={startDate}
                        class="bg-base-100 border p-2 rounded-md"
                    />
                </div>
                <div class="flex flex-col mb-4">
                    <label for="endDateCategory" class="text-lg"
                        >Дата окончания:</label
                    >
                    <input
                        type="date"
                        id="endDateCategory"
                        bind:value={endDate}
                        class="bg-base-100 border p-2 rounded-md"
                    />
                </div>
            </div>

            <button
                on:click={getInflationForCategory}
                class="btn btn-primary p-2 rounded-md"
            >
                Рассчитать инфляцию по категории
            </button>

            {#if categoryInflationError}
                <p class="text-red-500 mt-4">{categoryInflationError}</p>
            {:else if inflationCategory !== null}
                <table class="table table-zebra table-sm w-full mt-4">
                    <thead>
                        <tr>
                            <th class="p-2">Категория</th>
                            <th class="p-2">Период</th>
                            <th class="p-2">Инфляция (%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="p-2"
                                >{categories.find(
                                    (cat) => cat.CategoryID == selectedCategory,
                                )?.CategoryName}</td
                            >
                            <td class="p-2">{startDate} - {endDate}</td>
                            <td class="p-2">{inflationCategory.toFixed(2)}</td>
                        </tr>
                    </tbody>
                </table>
            {/if}
        </div>
    </div>
</main>

<style>
    table th,
    table td {
        text-align: left;
    }
</style>
