<?php

use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Route;
use App\Livewire\Login;
use App\Livewire\Dashboard;
use App\Livewire\InputLaporan;
use App\Livewire\RiwayatLaporan;
use App\Livewire\MasterData;

// Guest routes
Route::get('/', fn() => redirect()->route('login'));
Route::get('/login', Login::class)->name('login')->middleware('guest');

// Logout
Route::post('/logout', function () {
    Auth::logout();
    session()->invalidate();
    session()->regenerateToken();
    return redirect()->route('login');
})->name('logout');

// Authenticated routes
Route::middleware('auth')->group(function () {
    Route::get('/dashboard',    Dashboard::class)->name('dashboard');
    Route::get('/input-laporan', InputLaporan::class)->name('input-laporan');
    Route::get('/riwayat',       RiwayatLaporan::class)->name('riwayat');
    Route::get('/master-data',   MasterData::class)->name('master-data');
});
