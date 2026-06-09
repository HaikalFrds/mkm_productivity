<div class="w-full max-w-sm">

    {{-- Card --}}
    <div class="bg-white border border-gray-200 shadow-sm">

        {{-- Header merah --}}
        <div class="bg-red-600 px-8 py-6">
            <div class="text-white text-3xl font-bold tracking-tight leading-none">MKM</div>
            <div class="text-red-200 text-sm mt-1">Productivity System</div>
        </div>

        {{-- Form --}}
        <div class="px-8 py-7">
            <h2 class="text-gray-800 text-base font-semibold mb-6">Masuk ke Akun Anda</h2>

            {{-- Error --}}
            @if ($error)
                <div class="mb-4 px-4 py-3 bg-red-50 border border-red-200 text-red-700 text-sm">
                    {{ $error }}
                </div>
            @endif

            <form wire:submit="login" class="space-y-4">

                {{-- NIK --}}
                <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1.5 uppercase tracking-wide">
                        NIK / Username
                    </label>
                    <input
                        wire:model.live="nik"
                        type="text"
                        placeholder="Masukkan NIK"
                        autofocus
                        class="w-full px-3 py-2.5 border text-sm text-gray-800 bg-white
                               focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500
                               @error('nik') border-red-400 @else border-gray-300 @enderror"
                    />
                    @error('nik')
                        <p class="mt-1 text-xs text-red-600">{{ $message }}</p>
                    @enderror
                </div>

                {{-- Password --}}
                <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1.5 uppercase tracking-wide">
                        Password
                    </label>
                    <input
                        wire:model.live="password"
                        type="password"
                        placeholder="Masukkan password"
                        class="w-full px-3 py-2.5 border text-sm text-gray-800 bg-white
                               focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500
                               @error('password') border-red-400 @else border-gray-300 @enderror"
                    />
                    @error('password')
                        <p class="mt-1 text-xs text-red-600">{{ $message }}</p>
                    @enderror
                </div>

                {{-- Submit --}}
                <div class="pt-2">
                    <button
                        type="submit"
                        class="w-full bg-red-600 hover:bg-red-700 active:bg-red-800
                               text-white text-sm font-semibold py-2.5
                               transition-colors duration-150 flex items-center justify-center gap-2"
                    >
                        <span wire:loading.remove wire:target="login">Masuk</span>
                        <span wire:loading wire:target="login">Memproses...</span>
                    </button>
                </div>

            </form>
        </div>

        {{-- Footer --}}
        <div class="px-8 py-3 bg-gray-50 border-t border-gray-100 text-center text-xs text-gray-400">
            © {{ date('Y') }} MKM Productivity System
        </div>
    </div>

</div>
