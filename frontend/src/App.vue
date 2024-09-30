<template>
    <div class="min-h-full">
        <Disclosure as="nav" class="bg-gray-800">
            <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                <div class="flex h-16 items-center justify-between">
                    <div class="z-10 flex items-center">
                        <div class="flex-shrink-0">
                            <router-link :to="{ name: 'home' }"><img class="h-8 w-8" src="/favicon.png" alt="RTO Helper Logo" /></router-link>
                        </div>
                        <div class="hidden md:block">
                            <div class="ml-10 flex items-baseline space-x-4">
                                <router-link
                                v-for="item in navigation" :key="item.name" :to="{ name: item.rtrName }"
                                    :class="[item.current ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white', 'rounded-md px-3 py-2 text-sm font-medium']">
                                    {{ item.name }}
                                </router-link>
                            </div>
                        </div>
                    </div>
                    <div class="-mr-2 flex md:hidden">
                        <!-- Mobile menu button -->
                        <DisclosureButton
                            class="relative inline-flex items-center justify-center rounded-md bg-gray-800 p-2 text-gray-400 hover:bg-gray-700 hover:text-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-gray-800">
                            <span class="absolute -inset-0.5" />
                            <span class="sr-only">Open main menu</span>
                        </DisclosureButton>
                    </div>
                </div>
            </div>
        </Disclosure>

        <main>
            <RouterView />
        </main>
    </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { Disclosure, DisclosureButton } from '@headlessui/vue'

const navigation = [
    { name: 'Home', href: '/', rtrName: 'home', current: false },
    { name: 'About', href: '/about', rtrName: 'about', current: false }
]

// const router = useRouter();
// navigation.forEach(item => {
//     item.current = item.rtrName === router.currentRoute.value.name
// })
</script>
