<?php

namespace App\Livewire;

use Livewire\Component;

class InputLaporan extends Component
{
    public function render()
    {
        return view('livewire.input-laporan')
            ->layout('components.layouts.app', ['title' => 'Input Laporan Harian']);
    }
}
