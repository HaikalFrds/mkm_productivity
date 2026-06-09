<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MKM Productivity System</title>
    @vite(['resources/css/app.css', 'resources/js/app.js'])
    @livewireStyles
</head>
<body class="bg-gray-100 flex h-screen overflow-hidden">

    {{-- Sidebar --}}
    <aside class="w-56 bg-white border-r border-gray-200 flex flex-col flex-shrink-0">

        {{-- Logo --}}
        <div class="px-5 py-5 border-b border-gray-200">
            <div class="text-2xl font-bold text-red-600 leading-none">MKM</div>
            <div class="text-xs text-gray-400 mt-0.5">Productivity System</div>
        </div>

        {{-- Nav --}}
        <nav class="flex-1 py-2">
            @php
                $nav = [
                    ['route' => 'dashboard',     'label' => 'Dashboard'],
                    ['route' => 'input-laporan', 'label' => 'Input Laporan'],
                    ['route' => 'riwayat',       'label' => 'Riwayat Laporan'],
                    ['route' => 'master-data',   'label' => 'Master Data'],
                ];
                $current = request()->routeIs(Route::currentRouteName());
            @endphp

            @foreach ($nav as $item)
                @php $active = request()->routeIs($item['route']); @endphp
                <a href="{{ route($item['route']) }}"
                   class="flex items-center px-5 py-2.5 text-sm font-medium transition-colors
                          {{ $active
                              ? 'text-gray-900 bg-gray-50 border-l-4 border-red-600 pl-[17px]'
                              : 'text-gray-400 hover:text-gray-700 hover:bg-gray-50 border-l-4 border-transparent' }}">
                    {{ $item['label'] }}
                </a>
            @endforeach
        </nav>

        {{-- User + Logout --}}
        <div class="px-5 py-4 border-t border-gray-200">
            <div class="text-xs text-gray-500 font-medium truncate mb-2">
                {{ auth()->user()->name ?? '' }}
            </div>
            <form method="POST" action="{{ route('logout') }}">
                @csrf
                <button type="submit"
                    class="text-xs text-gray-400 hover:text-red-600 transition-colors">
                    Keluar
                </button>
            </form>
        </div>
    </aside>

    {{-- Main content --}}
    <div class="flex-1 flex flex-col overflow-hidden">

        {{-- Topbar --}}
        <header class="h-12 bg-white border-b border-gray-200 flex items-center px-6">
            <h1 class="text-sm font-semibold text-gray-800">{{ $title ?? 'Dashboard' }}</h1>
        </header>

        {{-- Page --}}
        <main class="flex-1 overflow-y-auto p-6">
            {{ $slot }}
        </main>
    </div>

    @livewireScripts
</body>
</html>
