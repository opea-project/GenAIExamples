<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script>
	import { createEventDispatcher } from "svelte";
  import extreme_ironing from '$lib/assets/imageData/extreme_ironing.jpg';
  import waterview from '$lib/assets/imageData/waterview.jpg';
	import { base64ImageStore } from "$lib/shared/stores/common/Store";

  let dispatch = createEventDispatcher();

  let images = [
    {
      id: 1,
      alt: 'Waterview',
      imgurl: waterview,
      prompt: 'What are the things I should be cautious about when I visit here?'
    },
    {
      id: 0,
      alt: 'Extreme Ironing',
      imgurl: extreme_ironing,
      prompt: 'What is unusual about this image?'
    }
  ];

  let currentIndex = 0;

  function nextImage() {
    currentIndex = (currentIndex + 1) % images.length;
  }

  function prevImage() {
    currentIndex = (currentIndex - 1 + images.length) % images.length;
  }


  async function handleImageClick() {
    const imgUrl = images[currentIndex].imgurl;
    const base64Data = await convertImageToBase64(imgUrl);
    const currentPrompt = images[currentIndex].prompt;
    dispatch("imagePrompt", { content: currentPrompt });
    base64ImageStore.set(base64Data);
  }

  async function convertImageToBase64(url) {
    const response = await fetch(url);
    const blob = await response.blob();
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }
</script>

<div class="flex w-full flex-col gap-3 rounded-xl bg-white p-5 my-2">
  <p>Example</p>
  <div class="relative w-full max-w-4xl mx-auto">
    <button
      class="absolute left-0 top-1/2 transform -translate-y-1/2 z-10  w-8 h-8 rounded-full sm:w-10 sm:h-10 bg-white/30 dark:bg-gray-800/30 group-hover:bg-white/50 dark:group-hover:bg-gray-800/60 group-focus:ring-4 group-focus:ring-white dark:group-focus:ring-gray-800/70 group-focus:outline-none"
      on:click={prevImage}
      aria-label="Previous image"
    >
      &#10094;
    </button>

    <div class="relative">
      <img
        src={images[currentIndex].imgurl}
        alt={images[currentIndex].alt}
        class="carousel-image w-full h-auto cursor-pointer"
        on:click={handleImageClick}
      />
      <div class="absolute bottom-0 left-0 bg-opacity-55 bg-black text-white p-3 w-full">
        <p>{images[currentIndex].prompt}</p>
      </div>
    </div>

    <button
      class="absolute right-0 top-1/2 transform -translate-y-1/2 z-10  w-8 h-8 rounded-full sm:w-10 sm:h-10 bg-white/30 dark:bg-gray-800/30 group-hover:bg-white/50 dark:group-hover:bg-gray-800/60 group-focus:ring-4 group-focus:ring-white dark:group-focus:ring-gray-800/70 group-focus:outline-none"
      on:click={nextImage}
      aria-label="Next image"
    >
      &#10095;
    </button>
  </div>
</div>

<style>
  .relative img {
    object-fit: cover;
  }
</style>
