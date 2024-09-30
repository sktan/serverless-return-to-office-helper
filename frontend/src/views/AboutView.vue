<template>
    <div class="relative bg-cover isolate overflow-hidden bg-gray-900 py-24 sm:py-32">
        <img
src="https://images.unsplash.com/photo-1556761175-b413da4baf72?auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&w=2830&h=1500&q=80&blend=111827&sat=-100&exp=15&blend-mode=multiply"
            alt="" class="absolute bg-cover inset-0 -z-10 h-full w-full object-cover object-right md:object-center" />
        <div
class="hidden sm:absolute sm:-top-10 sm:right-1/2 sm:-z-10 sm:mr-10 sm:block sm:transform-gpu sm:blur-3xl"
            aria-hidden="true">
            <div
class="aspect-[1097/845] w-[68.5625rem] bg-gradient-to-tr from-[#ff4694] to-[#776fff] opacity-20"
                style="clip-path: polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)" />
        </div>
        <div
class="absolute -top-52 left-1/2 -z-10 -translate-x-1/2 transform-gpu blur-3xl sm:top-[-28rem] sm:ml-16 sm:translate-x-0 sm:transform-gpu"
            aria-hidden="true">
            <div
class="aspect-[1097/845] w-[68.5625rem] bg-gradient-to-tr from-[#ff4694] to-[#776fff] opacity-20"
                style="clip-path: polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)" />
        </div>
        <div class="mx-auto max-w-7xl px-6 lg:px-8">
            <div class="mx-auto max-w-2xl lg:mx-0">
                <h2 class="text-4xl font-bold tracking-tight text-white sm:text-6xl">About this Project</h2>
                <p class="mt-6 text-lg leading-8 text-gray-300">The Return to Office Helper project came about when trying to coordinate office
                    trips with fellow coworkers but also figuring out whether I was meeting my office attendance obligations or not.
                    <br /><br />
                    The project is a simple website that allows you to create your own dashboard and keep track of your office attendance through a simple
                    "does this IP belong to the office?" check.
                </p>
                <p class="mt-6 text-lg leading-8 text-gray-300">
                    Key Project Contributors and Dependencies:
                </p>
            </div>
            <div class="mx-auto mt-10 max-w-2xl lg:mx-0 lg:max-w-none">
                <div
                    class="grid grid-cols-1 gap-x-8 gap-y-6 text-base font-semibold leading-7 text-white sm:grid-cols-2 md:flex lg:gap-x-10">
                    <a v-for="credit in credits" :key="credit.name" :href="credit.href">
                        <span  aria-hidden="true">
                            <img alt="Github Logo" class="logo inline-flex h-4 w-4" src="@/assets/github.svg"/>
                        </span> {{ credit.name }}
                    </a>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
const credits = [
    { name: 'Sktan', href: 'https://github.com/sktan/' },
    { name: 'Nager.Date', href: 'https://github.com/nager/Nager.Date' },
]
</script>
