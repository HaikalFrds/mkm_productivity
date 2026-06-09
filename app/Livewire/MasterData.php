<?php

namespace App\Livewire;

use Livewire\Component;

class MasterData extends Component
{
    public function render()
    {
        return view('livewire.master-data')
            ->layout('components.layouts.app', ['title' => 'Master Data']);
    }
}
