<script setup lang="ts">
import axios from 'axios';
import { onMounted, onUnmounted, ref, computed } from "vue";
import notfoundview from './NotFoundView.vue';

const props = defineProps({
    id: {
        type: String,
        required: true
    }
});

const apiEndpoint = import.meta.env.VITE_WEBAPI_ENDPOINT.replace(/\/$/, "");
const dashboardId = props?.id!;
const dashboardUrl = `${apiEndpoint}/dashboard/${  dashboardId}`;
const statsUrl = `${apiEndpoint}/stats/${  dashboardId}`;
const currentDate = new Date();

interface DashboardData {
    id: string;
    month: string;
    office_ips: Array<string>;
    rounding: string;
    timezone: string;
    percentage: number;
    holidays: Map<string, string>;
    created_at: string
    county: string
    country: string
}

interface MonthData {
    id: string;
    month: string;
    days: Map<string, string>;
    business_days: number;
    holidays: Map<string, string>;
}

interface StatsData {
    attendance: string;
}

const apiEndpoint = import.meta.env.VITE_WEBAPI_ENDPOINT.replace(/\/$/, "")
const loaded = ref<boolean>(false);
const dashboardData = ref<DashboardData | null>(null);
const monthData = ref<MonthData>();
const statsData = ref<StatsData>();
const zeroPad = (num: number, places: number) => String(num).padStart(places, '0')

const poller = ref<number>();
const dashboardPoller = () => {
    axios.post(`${apiEndpoint}/checkin/${props.id}`);
}

onMounted(async () => {
    await axios.get(dashboardUrl).then((dashboardResponse) => {
        loaded.value = true;
        if (dashboardResponse.status === 200) {
            poller.value = window.setTimeout(dashboardPoller, 15 * 60 * 1000);

            dashboardData.value = dashboardResponse.data;
            axios.get(`${dashboardUrl  }/${  currentDate.getFullYear()  }/${  currentDate.getMonth() + 1}`).then((response) => {
                monthData.value = response.data;
            });
            axios.get(`${statsUrl  }/${  currentDate.getFullYear()  }/${  currentDate.getMonth() + 1}`).then((response) => {
                statsData.value = response.data;
            });
        }
    });
})

onUnmounted(async() => {
    clearInterval(poller.value);
})

const attendendedDays = computed(() => {
    if (monthData?.value?.days === undefined) {
        return 0;
    }

    const count = Object.values(monthData?.value?.days).filter((value) => value != null).length;

    return count;
});

const totalDays = computed(() => {
    if (monthData?.value?.holidays === undefined || monthData?.value?.business_days === undefined) {
        return 0;
    }

    let count = monthData?.value?.business_days;
    count -= Object.keys(monthData.value.holidays).length;

    return count;
});
</script>

<template>
    <div v-if="!loaded" class="text-center">
        <div role="status">
            <svg aria-hidden="true" class="inline w-12 h-12 text-gray-200 animate-spin dark:text-gray-600 fill-yellow-400" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor"/>
                <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="currentFill"/>
            </svg>
            <span class="sr-only">Loading...</span>
        </div>
    </div>
    <notfoundview v-else-if="!dashboardData" />
    <main v-else>
        <div class="mx-auto max-w-7xl py-6 sm:px-6 lg:px-8">
            <div class="mb-1 text-lg font-medium dark:text-gray-900">Your Attendance ({{ attendendedDays }}/{{ totalDays
                }}):</div>
            <div class="w-full h-6 bg-gray-200 rounded-full dark:bg-gray-700">
                <div
class="bg-blue-600 text-xl font-medium text-blue-100 text-center p-0.5 leading-none rounded-full"
                    :style="{ 'width': `${parseInt(statsData?.attendance!)  }%` }">
                    {{ parseInt(statsData?.attendance!) }}%
                </div>
            </div>
        </div>
        <div class="mx-auto max-w-7xl py-2 sm:px-6 lg:px-8">
            Your Dashboard Id is: {{ dashboardData?.id }} <br />
            Keep this saved somewhere as you'll need this to access your dashboard and configure your local helper.
        </div>
        <div class="mx-auto max-w-7xl py-6 sm:px-6 lg:px-8">
            <div class="mb-1 text-lg font-medium dark:text-gray-900">Calendar:</div>
            <div class="relative overflow-x-auto">
                <table class="w-full text-sm text-left rtl:text-right text-gray-500 dark:text-gray-400">
                    <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
                        <tr>
                            <th scope="col" class="px-6 py-3">
                                Date
                            </th>
                            <th scope="col" class="px-6 py-3">
                                Attended
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr
class="bg-white border-b dark:bg-gray-800 dark:border-gray-700"
                            v-for="(value, key) in monthData?.days" v-bind:key="key">
                            <th
v-if="value != null" scope="row"
                                class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                                {{ monthData?.month }}-{{ zeroPad(key, 2) }}
                            </th>
                            <td v-if="value != null" class="px-6 py-4">
                                {{ value != null ? "Attended" : '-' }}
                            </td>
                        </tr>
                        <tr
class="bg-white border-b dark:bg-gray-800 dark:border-gray-700"
                            v-for="(value, key) in monthData?.holidays" v-bind:key="key">
                            <th
v-if="value != null" scope="row"
                                class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                                {{ key }}
                            </th>
                            <td v-if="value != null" class="px-6 py-4">
                                {{ value }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </main>
</template>
