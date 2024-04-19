<script lang="ts">
    export let running = false
</script>

{#if running}
    <div class="img bg-cover -mb-20"></div>
{/if}

<style>
    .img {
        width: 600px;
        height: 300px;
        animation-name: flowingAnimation;
        animation-duration: 3s;
        animation-iteration-count: infinite;
        /* animation-timing-function: cubic-bezier(0.1, 0.7, 1, 0.1); */
        animation-timing-function: linear;
    }

    @keyframes flowingAnimation {
        0% {
            background-image: url(../../assets/icons/svg/1.svg)
        }

        20% {
            background-image: url(../../assets/icons/svg/2.svg)
        }

        40% {
            background-image: url(../../assets/icons/svg/3.svg)
        }

        60% {
            background-image: url(../../assets/icons/svg/4.svg)
        }

        80% {
            background-image: url(../../assets/icons/svg/5.svg)
        }

        100% {
            background-image: url(../../assets/icons/svg/1.svg)
        }
    }
</style>
