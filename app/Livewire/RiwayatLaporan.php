<?php

namespace App\Livewire;

use Livewire\Component;

class RiwayatLaporan extends Component
{
    public function render()
    {
        return view('livewire.riwayat-laporan')
            ->layout('components.layouts.app', ['title' => 'Riwayat Laporan']);
    }
}
