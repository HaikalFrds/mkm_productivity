<?php

namespace App\Livewire;

use Illuminate\Support\Facades\Auth;
use Livewire\Attributes\Rule;
use Livewire\Component;

class Login extends Component
{
    #[Rule('required')]
    public string $nik = '';

    #[Rule('required')]
    public string $password = '';

    public string $error = '';

    public function login(): void
    {
        $this->validate();

        $credentials = [
            'nik'      => trim($this->nik),
            'password' => $this->password,
        ];

        if (Auth::attempt($credentials, remember: true)) {
            session()->regenerate();
            $this->redirect(route('dashboard'), navigate: false);
            return;
        }

        $this->error = 'NIK atau password salah.';
        $this->password = '';
    }

    public function render()
    {
        return view('livewire.login')
            ->layout('components.layouts.guest');
    }
}
