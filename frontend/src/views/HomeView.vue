<template>
    <div class="isolate mx-auto bg-white px-6 py-24 sm:py-32 lg:px-8">
        <div
        class="absolute inset-x-0 top-[-10rem] -z-10 transform-gpu overflow-hidden blur-3xl sm:top-[-20rem]"
            aria-hidden="true">
            <div
            class="relative left-1/2 -z-10 aspect-[1155/678] w-[36.125rem] max-w-none -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-30 sm:left-[calc(50%-40rem)] sm:w-[72.1875rem]"
                style="clip-path: polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)" />
        </div>
        <div class="mx-auto max-w-2xl text-center">
            <h2 class="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">Get Started!</h2>
            <p class="mt-2 text-lg leading-8 text-gray-600">Get started by creating a new dashboard or by pasting in
                your Dashboard Id.</p>
        </div>
        <div class="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">
            <form class="space-y-3" action="#" method="POST">
                <div>
                    <label for="dashboardId" class="block text-sm font-medium leading-6 text-gray-900">Your
                        Dashboard Id</label>
                    <div class="mt-2">
                        <input
                        id="dashboardId" name="dashboardId" type="text" v-model="dashboardId"
                            class="block w-full rounded-md border-0 p-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6" />
                    </div>
                </div>

                <div>
                    <button
                    @click="viewDashboard" type="button"
                        class="flex w-full justify-center rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-semibold leading-6 text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">
                        View Dashboard
                    </button>
                </div>
            </form>

            <p class="mt-10 text-center text-sm text-gray-500">
                Don't have a dashboard?
                {{ ' ' }}
                <button
                type="button" @click="registerUser" class="text-sm font-semibold leading-6 text-indigo-600 hover:text-indigo-500">Create one
                    now!</button>
            </p>
        </div>
    </div>
</template>

<script setup lang="ts">
import axios from 'axios';
import { useRouter } from 'vue-router';
import { ref } from 'vue';

const apiEndpoint = import.meta.env.VITE_WEBAPI_ENDPOINT.replace(/\/$/, "")
const url = `${apiEndpoint}/dashboard`;
const router = useRouter()
const dashboardId = ref<string>();

const viewDashboard = () => {
    router.push({ name: 'dashboard', params: { id: dashboardId.value } });
}

const registerUser = () => {
    axios.put(url).then((response) => {
        const { data } = response;
        if (response.status === 200) {
            router.push({ name: 'dashboard', params: { id: data.id } });
        }
    });
}
</script>
