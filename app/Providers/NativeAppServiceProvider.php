<?php

namespace App\Providers;

use Native\Laravel\Facades\Window;
use Native\Laravel\Contracts\ProvidesPhpIni;

class NativeAppServiceProvider implements ProvidesPhpIni
{
    public function boot(): void
    {
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
