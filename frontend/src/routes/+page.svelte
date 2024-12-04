<script>
    import Card from "../components/Card.svelte";
    import CategoryCard from "../components/CategoryCard.svelte";
    import Navbar from "../components/Navbar.svelte";
</script>

<Navbar/>
<main class="container mx-auto p-4">
    <h1 class="text-3xl font-bold mb-6">
        Посчитай свою инфляцию
    </h1>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 gap-6">
        <Card
            title="Твоя корзина"
            content="Составь свою продуктовую корзину и отслеживай изменение цен на нее"
        />
        <Card
            title="Актуальные цены и категории товаров"
            content="Составь свой список категорий и отслеживай изменение цен в категории"
        />
    </div>
</main>
