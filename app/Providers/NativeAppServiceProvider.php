<?php

namespace App\Providers;

use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\DB;
use Native\Laravel\Facades\Window;
use Native\Laravel\Contracts\ProvidesPhpIni;

class NativeAppServiceProvider implements ProvidesPhpIni
{
    public function boot(): void
    {
        // Seed default admin user on first boot (jika users table kosong)
        try {
            $count = DB::connection('nativephp')->table('users')->count();
            if ($count === 0) {
                Artisan::call('db:seed', ['--force' => true]);
            }
        } catch (\Throwable) {
            // Tabel belum ada saat pertama boot — biarkan migrasi jalan dulu
        }

        Window::open()
            ->title('MKM Productivity System')
            ->width(1280)
            ->height(800)
            ->minWidth(960)
            ->minHeight(640)
            ->showDevTools(false)
            ->url(url('/'));
    }

    public function phpIni(): array
    {
        return [
            'memory_limit' => '256M',
        ];
    }
}
